"""
Tests for individual Strands Agents SDK tools.
"""

import json
import pytest
from mutualaid_agent.tools.alert_tools import parse_and_register_weather_alert
from mutualaid_agent.tools.db_tools import (
    query_community_resources_by_proximity,
    get_community_inventory,
    check_resource_status
)
from mutualaid_agent.tools.notification_tools import (
    draft_and_send_coordinator_approval_sms,
    send_dispatch_confirmation
)
from mutualaid_agent.db.seed_data import seed_database
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import ResourceStatus


@pytest.fixture(autouse=True)
def setup_db():
    seed_database(db_client)


def test_tool_parse_and_register_alert():
    alert_text = json.dumps({
        "event": "Blizzard Warning",
        "description": "Heavy snowfall and impassable roads",
        "address": "88 Elm St, Downtown",
        "latitude": 40.7110,
        "longitude": -74.0020
    })
    result_str = parse_and_register_weather_alert(alert_text)
    data = json.loads(result_str)
    assert data["status"] == "REGISTERED"
    assert data["incident_type"] == "blizzard"
    assert data["required_resource_type"] == "four_wheel_drive"


def test_tool_query_community_resources():
    # Register an incident
    reg_str = parse_and_register_weather_alert(json.dumps({
        "event": "Flash Flood",
        "description": "Flooding",
        "address": "14 Maple St",
        "latitude": 40.7128,
        "longitude": -74.0060
    }))
    incident_id = json.loads(reg_str)["incident_id"]

    query_str = query_community_resources_by_proximity(incident_id=incident_id, max_radius_miles=5.0)
    data = json.loads(query_str)
    assert data["matches_found"] >= 1
    assert data["best_match"]["resource_id"] == "res-pump-001"
    assert data["best_match"]["distance_miles"] < 0.1


def test_tool_get_inventory():
    inv_str = get_community_inventory()
    inv_data = json.loads(inv_str)
    assert inv_data["total_resources"] >= 7
    assert len(inv_data["available"]) >= 7


def test_tool_draft_sms_and_dispatch_confirmation():
    # Register incident
    reg_str = parse_and_register_weather_alert(json.dumps({
        "event": "Flash Flood",
        "description": "Basement Flooding",
        "address": "10 Main St",
        "latitude": 40.7130,
        "longitude": -74.0065
    }))
    incident_id = json.loads(reg_str)["incident_id"]

    draft_str = draft_and_send_coordinator_approval_sms(
        incident_id=incident_id,
        resource_id="res-pump-001"
    )
    draft_data = json.loads(draft_str)
    assert draft_data["status"] == "SMS_SENT_AWAITING_APPROVAL"
    assert "Reply YES" in draft_data["single_decision_sms"]

    proposal_id = draft_data["proposal_id"]
    conf_str = send_dispatch_confirmation(proposal_id=proposal_id)
    conf_data = json.loads(conf_str)
    assert conf_data["status"] == "CONFIRMATIONS_DISPATCHED"
    assert "Neighbor Bob" in conf_data["coordinator_sms"]
