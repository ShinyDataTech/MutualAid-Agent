"""
Database and inventory query tools for Strands Agents SDK.
"""

import json
from typing import Optional
from strands import tool

from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import ResourceStatus, ResourceType
from mutualaid_agent.engine.matcher import find_matching_resources


@tool
def query_community_resources_by_proximity(
    incident_id: str,
    max_radius_miles: float = 5.0
) -> str:
    """
    Queries DynamoDB for community resources matching the required equipment type
    for an active incident, and ranks them by geographic proximity.

    Parameters:
        incident_id: Unique ID of the registered incident.
        max_radius_miles: Maximum distance in miles to search around the incident (default 5.0).

    Returns:
        JSON string containing ranked matching resources with distance and owner contact info.
    """
    incident = db_client.get_incident(incident_id)
    if not incident:
        return json.dumps({
            "error": f"Incident with ID {incident_id} not found in DynamoDB."
        })

    matches = find_matching_resources(
        incident=incident,
        max_radius_miles=max_radius_miles,
        client=db_client
    )

    if not matches:
        return json.dumps({
            "incident_id": incident_id,
            "required_resource": incident.required_resource_type.value,
            "matches_found": 0,
            "message": f"No available {incident.required_resource_type.value} found within {max_radius_miles} miles."
        })

    results = [m.to_dict() for m in matches]
    return json.dumps({
        "incident_id": incident_id,
        "target_address": incident.address,
        "required_resource": incident.required_resource_type.value,
        "matches_found": len(results),
        "best_match": results[0],
        "all_matches": results
    }, indent=2)


@tool
def get_community_inventory() -> str:
    """
    Returns a summary of all registered community emergency resources and their current availability statuses.

    Returns:
        JSON string containing all resources grouped by availability status.
    """
    resources = db_client.list_resources()
    summary = {
        "total_resources": len(resources),
        "available": [r.model_dump() for r in resources if r.status == ResourceStatus.AVAILABLE],
        "dispatched": [r.model_dump() for r in resources if r.status == ResourceStatus.DISPATCHED],
        "reserved": [r.model_dump() for r in resources if r.status == ResourceStatus.RESERVED]
    }
    return json.dumps(summary, indent=2)


@tool
def check_resource_status(resource_id: str) -> str:
    """
    Checks the real-time status and specifications of a specific community resource.

    Parameters:
        resource_id: Unique ID of the community equipment (e.g., 'res-pump-001').

    Returns:
        JSON string with resource details and availability.
    """
    resource = db_client.get_resource(resource_id)
    if not resource:
        return json.dumps({"error": f"Resource {resource_id} not found."})
    return json.dumps(resource.model_dump(), indent=2)
