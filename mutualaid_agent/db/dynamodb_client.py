"""
DynamoDB Client & Data Access Layer for MutualAid-Agent.
Supports both AWS DynamoDB (via boto3) and a high-fidelity local in-memory mock
for offline development, tests, and local demo execution.
"""

import logging
from typing import List, Optional, Dict, Any
from mutualaid_agent.config import settings
from mutualaid_agent.db.models import (
    CommunityResource,
    IncidentAlert,
    DispatchProposal,
    ResourceStatus,
    ProposalStatus,
    ResourceType
)

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Local thread-safe in-memory database simulating DynamoDB."""
    def __init__(self):
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self.propatches: Dict[str, Dict[str, Any]] = {}

    def clear(self):
        self.resources.clear()
        self.incidents.clear()
        self.propatches.clear()


_local_store = InMemoryStore()


class DynamoDBClient:
    """
    Unified DynamoDB Client for MutualAid-Agent.
    Handles CRUD operations for community resources, emergency incidents, and dispatch proposals.
    """
    def __init__(self, use_mock: Optional[bool] = None):
        self.use_mock = use_mock if use_mock is not None else settings.use_mock_db
        self.boto_client = None
        self.resources_table = None
        self.incidents_table = None
        self.dispatches_table = None

        if not self.use_mock:
            try:
                import boto3
                dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
                self.resources_table = dynamodb.Table(settings.resources_table_name)
                self.incidents_table = dynamodb.Table(settings.incidents_table_name)
                self.dispatches_table = dynamodb.Table(settings.dispatches_table_name)
                # Quick health check to test connection
                self.resources_table.table_status
            except Exception as e:
                logger.info(f"AWS DynamoDB connection unavailable ({e}). Falling back to local in-memory storage.")
                self.use_mock = True

    # ================= Community Resources =================

    def put_resource(self, resource: CommunityResource) -> bool:
        if self.use_mock:
            _local_store.resources[resource.resource_id] = resource.model_dump()
            return True
        try:
            self.resources_table.put_item(Item=resource.model_dump())
            return True
        except Exception as e:
            logger.error(f"Error putting resource {resource.resource_id}: {e}")
            return False

    def get_resource(self, resource_id: str) -> Optional[CommunityResource]:
        if self.use_mock:
            data = _local_store.resources.get(resource_id)
            return CommunityResource(**data) if data else None
        try:
            resp = self.resources_table.get_item(Key={"resource_id": resource_id})
            item = resp.get("Item")
            return CommunityResource(**item) if item else None
        except Exception as e:
            logger.error(f"Error fetching resource {resource_id}: {e}")
            return None

    def list_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        status: Optional[ResourceStatus] = None
    ) -> List[CommunityResource]:
        if self.use_mock:
            results = []
            for item in _local_store.resources.values():
                if resource_type and item.get("resource_type") != resource_type.value:
                    continue
                if status and item.get("status") != status.value:
                    continue
                results.append(CommunityResource(**item))
            return results
        try:
            # DynamoDB scan with filters
            scan_kwargs = {}
            filter_expressions = []
            expr_names = {}
            expr_values = {}

            if resource_type:
                filter_expressions.append("#rt = :rt")
                expr_names["#rt"] = "resource_type"
                expr_values[":rt"] = resource_type.value
            if status:
                filter_expressions.append("#st = :st")
                expr_names["#st"] = "status"
                expr_values[":st"] = status.value

            if filter_expressions:
                scan_kwargs["FilterExpression"] = " AND ".join(filter_expressions)
                scan_kwargs["ExpressionAttributeNames"] = expr_names
                scan_kwargs["ExpressionAttributeValues"] = expr_values

            resp = self.resources_table.scan(**scan_kwargs)
            items = resp.get("Items", [])
            return [CommunityResource(**item) for item in items]
        except Exception as e:
            logger.error(f"Error scanning resources: {e}")
            return []

    def update_resource_status(self, resource_id: str, new_status: ResourceStatus) -> bool:
        if self.use_mock:
            if resource_id in _local_store.resources:
                _local_store.resources[resource_id]["status"] = new_status.value
                return True
            return False
        try:
            self.resources_table.update_item(
                Key={"resource_id": resource_id},
                UpdateExpression="SET #st = :val",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":val": new_status.value}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating resource status for {resource_id}: {e}")
            return False

    # ================= Emergency Incidents =================

    def put_incident(self, incident: IncidentAlert) -> bool:
        if self.use_mock:
            _local_store.incidents[incident.incident_id] = incident.model_dump()
            return True
        try:
            self.incidents_table.put_item(Item=incident.model_dump())
            return True
        except Exception as e:
            logger.error(f"Error saving incident {incident.incident_id}: {e}")
            return False

    def get_incident(self, incident_id: str) -> Optional[IncidentAlert]:
        if self.use_mock:
            data = _local_store.incidents.get(incident_id)
            return IncidentAlert(**data) if data else None
        try:
            resp = self.incidents_table.get_item(Key={"incident_id": incident_id})
            item = resp.get("Item")
            return IncidentAlert(**item) if item else None
        except Exception as e:
            logger.error(f"Error getting incident {incident_id}: {e}")
            return None

    # ================= Dispatch Proposals =================

    def put_proposal(self, proposal: DispatchProposal) -> bool:
        if self.use_mock:
            _local_store.propatches[proposal.proposal_id] = proposal.model_dump()
            return True
        try:
            self.dispatches_table.put_item(Item=proposal.model_dump())
            return True
        except Exception as e:
            logger.error(f"Error storing proposal {proposal.proposal_id}: {e}")
            return False

    def get_proposal(self, proposal_id: str) -> Optional[DispatchProposal]:
        if self.use_mock:
            data = _local_store.propatches.get(proposal_id)
            return DispatchProposal(**data) if data else None
        try:
            resp = self.dispatches_table.get_item(Key={"proposal_id": proposal_id})
            item = resp.get("Item")
            return DispatchProposal(**item) if item else None
        except Exception as e:
            logger.error(f"Error getting proposal {proposal_id}: {e}")
            return None

    def get_latest_pending_proposal(self) -> Optional[DispatchProposal]:
        """Finds the most recent proposal pending coordinator approval."""
        if self.use_mock:
            pending = [
                DispatchProposal(**p)
                for p in _local_store.propatches.values()
                if p.get("status") == ProposalStatus.PENDING_APPROVAL.value
            ]
            if not pending:
                return None
            pending.sort(key=lambda x: x.created_at, reverse=True)
            return pending[0]
        try:
            resp = self.dispatches_table.scan(
                FilterExpression="#st = :pending",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":pending": ProposalStatus.PENDING_APPROVAL.value}
            )
            items = resp.get("Items", [])
            if not items:
                return None
            proposals = [DispatchProposal(**it) for it in items]
            proposals.sort(key=lambda x: x.created_at, reverse=True)
            return proposals[0]
        except Exception as e:
            logger.error(f"Error scanning pending proposals: {e}")
            return None

    def update_proposal_status(
        self,
        proposal_id: str,
        status: ProposalStatus,
        approved_at: Optional[str] = None
    ) -> bool:
        if self.use_mock:
            if proposal_id in _local_store.propatches:
                _local_store.propatches[proposal_id]["status"] = status.value
                if approved_at:
                    _local_store.propatches[proposal_id]["approved_at"] = approved_at
                return True
            return False
        try:
            expr = "SET #st = :status"
            names = {"#st": "status"}
            vals = {":status": status.value}
            if approved_at:
                expr += ", approved_at = :app"
                vals[":app"] = approved_at

            self.dispatches_table.update_item(
                Key={"proposal_id": proposal_id},
                UpdateExpression=expr,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=vals
            )
            return True
        except Exception as e:
            logger.error(f"Error updating proposal {proposal_id}: {e}")
            return False


# Global singleton instance
db_client = DynamoDBClient()
