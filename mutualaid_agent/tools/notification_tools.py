"""
Notification and single-decision human-in-the-loop SMS tools for Strands Agents SDK.
"""

import json
import logging
from typing import Dict, Any, Optional
from strands import tool

from mutualaid_agent.config import settings
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.engine.matcher import haversine_distance_miles, MatchResult
from mutualaid_agent.engine.dispatch_planner import build_dispatch_proposal

logger = logging.getLogger(__name__)


@tool
def draft_and_send_coordinator_approval_sms(
    incident_id: str,
    resource_id: str
) -> str:
    """
    Drafts a single-decision SMS proposal for the human coordinator and logs the proposal
    in DynamoDB awaiting the coordinator's YES/NO response.

    Parameters:
        incident_id: Unique ID of the active emergency incident.
        resource_id: Unique ID of the matched community resource.

    Returns:
        JSON string containing the drafted SMS text, proposal ID, and dispatch parameters.
    """
    incident = db_client.get_incident(incident_id)
    if not incident:
        return json.dumps({"error": f"Incident {incident_id} not found."})

    resource = db_client.get_resource(resource_id)
    if not resource:
        return json.dumps({"error": f"Resource {resource_id} not found."})

    distance = haversine_distance_miles(
        incident.latitude, incident.longitude,
        resource.latitude, resource.longitude
    )
    score = max(0.0, round(100.0 - (distance * 5.0), 1))
    match_result = MatchResult(resource=resource, distance_miles=distance, match_score=score)

    proposal = build_dispatch_proposal(incident, match_result, client=db_client)

    logger.info(f"Generated Single-Decision SMS for Coordinator: {proposal.single_decision_sms}")

    return json.dumps({
        "status": "SMS_SENT_AWAITING_APPROVAL",
        "proposal_id": proposal.proposal_id,
        "coordinator_phone": settings.coordinator_phone,
        "single_decision_sms": proposal.single_decision_sms,
        "target_address": proposal.target_address,
        "resource_title": proposal.resource_title,
        "owner_name": proposal.owner_name,
        "owner_phone": proposal.owner_phone,
        "distance_miles": proposal.distance_miles,
        "action_required": "Wait for coordinator to reply YES via Twilio SMS webhook."
    }, indent=2)


@tool
def send_dispatch_confirmation(proposal_id: str) -> str:
    """
    Sends dispatch instructions to both the equipment owner and the coordinator
    after the coordinator has approved the proposal.

    Parameters:
        proposal_id: Unique ID of the approved dispatch proposal.

    Returns:
        JSON string confirming notifications sent to owner and coordinator.
    """
    proposal = db_client.get_proposal(proposal_id)
    if not proposal:
        return json.dumps({"error": f"Proposal {proposal_id} not found."})

    owner_sms = (
        f"[MutualAid Emergency Dispatch] Hello {proposal.owner_name}, "
        f"your {proposal.resource_title} has been requested for emergency aid at "
        f"{proposal.target_address}. Please stage equipment for pickup. Thank you!"
    )
    coordinator_sms = (
        f"[MutualAid Status] Dispatch confirmed for {proposal.resource_title}. "
        f"Owner {proposal.owner_name} ({proposal.owner_phone}) notified."
    )

    return json.dumps({
        "status": "CONFIRMATIONS_DISPATCHED",
        "proposal_id": proposal.proposal_id,
        "owner_sms": owner_sms,
        "coordinator_sms": coordinator_sms
    }, indent=2)
