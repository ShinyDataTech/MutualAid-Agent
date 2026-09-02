"""
Dispatch Planner for MutualAid-Agent.
Creates human-in-the-loop proposals with single-decision SMS formats and handles approvals/rejections.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from mutualaid_agent.db.models import (
    IncidentAlert,
    CommunityResource,
    DispatchProposal,
    ProposalStatus,
    ResourceStatus
)
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.engine.matcher import MatchResult, find_matching_resources


def format_single_decision_sms(
    incident_type_name: str,
    target_address: str,
    owner_name: str,
    resource_title: str,
    distance_miles: float
) -> str:
    """
    Formats an ultra-concise, single-decision SMS for the neighborhood coordinator.
    Designed for instant cognitive processing and binary response (Reply YES / NO).
    """
    clean_type = incident_type_name.replace("_", " ").title()
    return (
        f"[MutualAid Alert] {clean_type} at {target_address}. "
        f"Dispatch {owner_name}'s {resource_title} ({distance_miles} mi away)? "
        f"Reply YES to approve, NO for alternative."
    )


def build_dispatch_proposal(
    incident: IncidentAlert,
    match: MatchResult,
    client=None
) -> DispatchProposal:
    """
    Constructs and persists a new DispatchProposal in DynamoDB with a single-decision SMS prompt.
    """
    target_client = client or db_client
    proposal_id = f"prop-{uuid.uuid4().hex[:8]}"
    
    sms_text = format_single_decision_sms(
        incident_type_name=incident.incident_type.value,
        target_address=incident.address,
        owner_name=match.resource.owner_name,
        resource_title=match.resource.title,
        distance_miles=match.distance_miles
    )
    
    rationale = (
        f"Matched {match.resource.title} ({match.resource.capacity_specs}) owned by {match.resource.owner_name} "
        f"located {match.distance_miles} miles from incident ({incident.address}). "
        f"Match score: {match.match_score}/100."
    )

    proposal = DispatchProposal(
        proposal_id=proposal_id,
        incident_id=incident.incident_id,
        resource_id=match.resource.resource_id,
        resource_title=match.resource.title,
        owner_name=match.resource.owner_name,
        owner_phone=match.resource.owner_phone,
        target_address=incident.address,
        distance_miles=match.distance_miles,
        rationale=rationale,
        single_decision_sms=sms_text,
        status=ProposalStatus.PENDING_APPROVAL,
        created_at=datetime.utcnow().isoformat()
    )

    target_client.put_proposal(proposal)
    return proposal


def process_coordinator_decision(
    decision_text: str,
    proposal_id: Optional[str] = None,
    client=None
) -> Dict[str, Any]:
    """
    Processes the coordinator's inbound SMS reply (e.g. YES, NO, STATUS).
    Executes equipment state transition in DynamoDB and returns operational confirmation.
    """
    target_client = client or db_client
    normalized = decision_text.strip().upper()

    # Find the target proposal
    if proposal_id:
        proposal = target_client.get_proposal(proposal_id)
    else:
        proposal = target_client.get_latest_pending_proposal()

    if not proposal:
        return {
            "status": "NO_PENDING_PROPOSAL",
            "reply_sms": "[MutualAid] No pending emergency dispatch proposals at this time."
        }

    now_iso = datetime.utcnow().isoformat()

    if "YES" in normalized or normalized == "Y":
        # Approve proposal
        target_client.update_proposal_status(
            proposal_id=proposal.proposal_id,
            status=ProposalStatus.APPROVED,
            approved_at=now_iso
        )
        # Mark resource as dispatched in DynamoDB
        target_client.update_resource_status(
            resource_id=proposal.resource_id,
            new_status=ResourceStatus.DISPATCHED
        )
        
        reply_sms = (
            f"[MutualAid Confirmed] Dispatch APPROVED for {proposal.resource_title}. "
            f"Notifying {proposal.owner_name} ({proposal.owner_phone}) to stage equipment for {proposal.target_address}."
        )
        owner_notification = (
            f"[MutualAid Emergency Request] Hello {proposal.owner_name}, coordinator approved dispatch of your "
            f"{proposal.resource_title} to {proposal.target_address}. Please verify readiness."
        )

        return {
            "status": "APPROVED",
            "proposal_id": proposal.proposal_id,
            "resource_id": proposal.resource_id,
            "reply_sms": reply_sms,
            "owner_notification": owner_notification
        }

    elif "NO" in normalized or normalized == "N":
        # Reject proposal and seek alternative
        target_client.update_proposal_status(
            proposal_id=proposal.proposal_id,
            status=ProposalStatus.REJECTED
        )
        incident = target_client.get_incident(proposal.incident_id)
        
        alternative_proposal = None
        if incident:
            matches = find_matching_resources(incident, client=target_client)
            # Filter out rejected resource
            candidates = [m for m in matches if m.resource.resource_id != proposal.resource_id]
            if candidates:
                alt_match = candidates[0]
                alternative_proposal = build_dispatch_proposal(incident, alt_match, client=target_client)

        if alternative_proposal:
            reply_sms = (
                f"[MutualAid] Dispatch rejected. Found alternative:\n"
                f"{alternative_proposal.single_decision_sms}"
            )
        else:
            reply_sms = (
                f"[MutualAid] Dispatch rejected. No alternative {proposal.resource_title} available nearby. "
                f"Escalating to municipal services."
            )

        return {
            "status": "REJECTED",
            "proposal_id": proposal.proposal_id,
            "reply_sms": reply_sms,
            "alternative_proposal": alternative_proposal.model_dump() if alternative_proposal else None
        }

    elif "STATUS" in normalized:
        return {
            "status": "STATUS_CHECK",
            "reply_sms": (
                f"[MutualAid Status] Pending Proposal: {proposal.proposal_id} | "
                f"Target: {proposal.target_address} | Item: {proposal.resource_title} | "
                f"Dist: {proposal.distance_miles}mi. Reply YES to dispatch or NO to reject."
            )
        }
    else:
        return {
            "status": "UNRECOGNIZED_COMMAND",
            "reply_sms": "[MutualAid] Unrecognized command. Please reply YES to approve dispatch, NO to reject, or STATUS."
        }
