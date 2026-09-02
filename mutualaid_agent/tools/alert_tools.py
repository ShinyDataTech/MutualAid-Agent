"""
Alert parsing and classification tools for Strands Agents SDK.
"""

import json
import uuid
from typing import Dict, Any
from strands import tool

from mutualaid_agent.db.models import (
    IncidentAlert,
    IncidentType,
    IncidentSeverity,
    ResourceType
)
from mutualaid_agent.db.dynamodb_client import db_client


@tool
def parse_and_register_weather_alert(alert_payload: str) -> str:
    """
    Parses a weather alert webhook or raw emergency broadcast payload,
    determines severity, identifies required mutual aid equipment,
    and registers the incident in DynamoDB.

    Parameters:
        alert_payload: Raw JSON string or text message describing the emergency/weather alert.

    Returns:
        A JSON string containing the registered incident details and recommended equipment.
    """
    try:
        data = json.loads(alert_payload)
    except Exception:
        data = {"event": "Emergency Weather Alert", "description": alert_payload}

    event_text = str(data.get("event", "")).lower()
    headline = str(data.get("headline", data.get("title", ""))).lower()
    description = str(data.get("description", alert_payload)).lower()
    full_text = f"{event_text} {headline} {description}"

    # Determine incident type & equipment
    if "flood" in full_text or "water" in full_text or "inundation" in full_text:
        incident_type = IncidentType.FLOOD
        required_resource = ResourceType.SUBMERSIBLE_PUMP
        severity = IncidentSeverity.SEVERE if "flash" in full_text or "warning" in full_text else IncidentSeverity.MODERATE
    elif "tree" in full_text or "blocked" in full_text or "chainsaw" in full_text or "debris" in full_text:
        incident_type = IncidentType.TREE_OBSTRUCTION
        required_resource = ResourceType.CHAINSAW
        severity = IncidentSeverity.MODERATE
    elif "power" in full_text or "outage" in full_text or "blackout" in full_text or "medical" in full_text:
        incident_type = IncidentType.POWER_OUTAGE
        required_resource = ResourceType.GENERATOR
        severity = IncidentSeverity.CRITICAL if "oxygen" in full_text or "medical" in full_text else IncidentSeverity.SEVERE
    elif "snow" in full_text or "blizzard" in full_text or "ice" in full_text:
        incident_type = IncidentType.BLIZZARD
        required_resource = ResourceType.FOUR_WHEEL_DRIVE
        severity = IncidentSeverity.SEVERE
    else:
        incident_type = IncidentType.FLOOD
        required_resource = ResourceType.SUBMERSIBLE_PUMP
        severity = IncidentSeverity.MODERATE

    # Extract location and coordinates (with defaults if missing)
    address = data.get("address", data.get("areaDesc", "10 Main St, Downtown"))
    latitude = float(data.get("latitude", data.get("lat", 40.7130)))
    longitude = float(data.get("longitude", data.get("lon", -74.0065)))
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"

    incident = IncidentAlert(
        incident_id=incident_id,
        source=data.get("source", "NWS_ALERT_WEBHOOK"),
        incident_type=incident_type,
        severity=severity,
        title=data.get("headline", data.get("event", "Severe Weather Emergency")),
        description=data.get("description", alert_payload),
        address=address,
        latitude=latitude,
        longitude=longitude,
        required_resource_type=required_resource,
        raw_payload=data if isinstance(data, dict) else None
    )

    db_client.put_incident(incident)

    result = {
        "status": "REGISTERED",
        "incident_id": incident.incident_id,
        "incident_type": incident.incident_type.value,
        "severity": incident.severity.value,
        "address": incident.address,
        "coordinates": {"lat": incident.latitude, "lon": incident.longitude},
        "required_resource_type": incident.required_resource_type.value,
        "action_required": f"Query DynamoDB for nearby {incident.required_resource_type.value} within 5 miles."
    }
    return json.dumps(result, indent=2)
