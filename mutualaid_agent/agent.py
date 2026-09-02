"""
MutualAid-Agent: Autonomous Background Emergency Coordinator using Strands Agents SDK.
"""

import json
import logging
from typing import Dict, Any, Optional
from strands import Agent
from strands.models.bedrock import BedrockModel

from mutualaid_agent.config import settings
from mutualaid_agent.tools import (
    ALL_AGENT_TOOLS,
    parse_and_register_weather_alert,
    query_community_resources_by_proximity,
    draft_and_send_coordinator_approval_sms
)
from mutualaid_agent.engine.dispatch_planner import (
    process_coordinator_decision,
    format_single_decision_sms
)
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import IncidentAlert, DispatchProposal

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are MutualAid-Agent, an autonomous background emergency logistics AI agent built for community mutual aid.
Your role:
1. Autonomously monitor incoming emergency feeds (weather alerts, disaster webhooks, community pings).
2. Parse alert payloads to determine incident type, severity, and required community equipment (e.g. submersible pumps, generators, chainsaws).
3. Query the community inventory in Amazon DynamoDB and rank equipment by proximity.
4. Prepare a single-decision SMS proposal for the human neighborhood coordinator.
5. Never execute physical resource dispatch without explicit human-in-the-loop approval.
6. When the coordinator replies YES, confirm the dispatch and notify the equipment owner.

Always follow strict safety protocols and prioritize proximity and equipment capacity.
"""


def create_mutualaid_agent(model_id: Optional[str] = None) -> Agent:
    """
    Initializes and returns a Strands Agent configured with Amazon Bedrock and MutualAid tools.
    """
    model_name = model_id or settings.bedrock_model_id
    try:
        bedrock_model = BedrockModel(
            model_id=model_name,
            region_name=settings.aws_region
        )
    except Exception as e:
        logger.warning(f"Bedrock model init deferred or using default: {e}")
        bedrock_model = None

    agent = Agent(
        name="MutualAid-Agent",
        description="Autonomous background emergency logistics and community resource coordinator.",
        system_prompt=SYSTEM_PROMPT,
        tools=ALL_AGENT_TOOLS,
        model=bedrock_model
    )
    return agent


class MutualAidCoordinator:
    """
    Orchestration wrapper for the autonomous background loop.
    Enables direct execution for serverless Lambda webhooks and interactive CLI.
    """
    def __init__(self):
        self.db = db_client
        self._agent = None

    @property
    def agent(self) -> Agent:
        if self._agent is None:
            self._agent = create_mutualaid_agent()
        return self._agent

    def process_incoming_alert(self, alert_payload: str) -> Dict[str, Any]:
        """
        Main autonomous pipeline for processing a weather alert:
        1. Parse and register the alert in DynamoDB.
        2. Query and rank nearest matching equipment.
        3. Formulate single-decision SMS proposal for the coordinator.
        """
        # Step 1: Parse alert
        reg_result_str = parse_and_register_weather_alert(alert_payload)
        reg_data = json.loads(reg_result_str)
        incident_id = reg_data["incident_id"]

        # Step 2: Query nearby equipment
        query_result_str = query_community_resources_by_proximity(
            incident_id=incident_id,
            max_radius_miles=settings.default_search_radius_miles
        )
        query_data = json.loads(query_result_str)

        if query_data.get("matches_found", 0) == 0:
            return {
                "status": "NO_MATCH_FOUND",
                "incident": reg_data,
                "message": query_data.get("message")
            }

        best_match = query_data["best_match"]
        resource_id = best_match["resource_id"]

        # Step 3: Draft single-decision SMS proposal
        sms_result_str = draft_and_send_coordinator_approval_sms(
            incident_id=incident_id,
            resource_id=resource_id
        )
        sms_data = json.loads(sms_result_str)

        return {
            "status": "PROPOSAL_PENDING_APPROVAL",
            "incident": reg_data,
            "best_match": best_match,
            "proposal": sms_data
        }

    def handle_inbound_sms(self, from_number: str, body: str) -> Dict[str, Any]:
        """
        Handles incoming coordinator SMS replies (e.g. YES, NO, STATUS).
        """
        return process_coordinator_decision(
            decision_text=body,
            client=self.db
        )


coordinator = MutualAidCoordinator()
