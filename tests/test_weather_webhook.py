"""
Tests for incoming weather alert webhook handler and normalization.
"""

import json
import pytest
from mutualaid_agent.handlers.weather_webhook import lambda_handler
from mutualaid_agent.db.seed_data import seed_database
from mutualaid_agent.db.dynamodb_client import db_client


@pytest.fixture(autouse=True)
def setup_db():
    seed_database(db_client)


def test_weather_webhook_flood_alert():
    event = {
        "body": json.dumps({
            "source": "NWS_ALERT_WEBHOOK",
            "event": "Flash Flood Warning",
            "headline": "Dangerous Flooding at 10 Main St",
            "description": "Basement flooding and street runoff.",
            "address": "10 Main St, Downtown",
            "latitude": 40.7130,
            "longitude": -74.0065
        })
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "result" in body
    assert body["result"]["incident"]["required_resource_type"] == "submersible_pump"
    assert "single_decision_sms" in body["result"]["proposal"]
    assert "Reply YES" in body["result"]["proposal"]["single_decision_sms"]


def test_weather_webhook_fallen_tree_alert():
    event = {
        "body": json.dumps({
            "source": "MUNICIPAL_DISPATCH",
            "event": "Severe Windstorm",
            "headline": "Large Oak Tree Down Blocking Road",
            "description": "Fallen tree blocking driveway and power line at 5 Pine Rd. Need chainsaw crew.",
            "address": "5 Pine Rd, Downtown",
            "latitude": 40.7180,
            "longitude": -74.0090
        })
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["incident"]["required_resource_type"] == "chainsaw"
    assert "Carlos" in body["result"]["proposal"]["single_decision_sms"] or "Chainsaw" in body["result"]["proposal"]["single_decision_sms"]


def test_weather_webhook_power_outage_alert():
    event = {
        "body": json.dumps({
            "source": "COMMUNITY_HOTLINE",
            "event": "Grid Failure",
            "headline": "Power Outage Life Support",
            "description": "Power outage in residential sector, neighbor requires generator for oxygen concentrator.",
            "address": "22 Oak Ave, Downtown",
            "latitude": 40.7150,
            "longitude": -74.0040
        })
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["incident"]["required_resource_type"] == "generator"
    assert body["result"]["incident"]["severity"] == "critical"
