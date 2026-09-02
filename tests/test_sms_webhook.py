"""
Tests for inbound Twilio SMS webhook handler and coordinator interactions.
"""

import json
import pytest
from mutualaid_agent.handlers.sms_webhook import lambda_handler as sms_handler
from mutualaid_agent.handlers.weather_webhook import lambda_handler as weather_handler
from mutualaid_agent.db.seed_data import seed_database
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import ResourceStatus, ProposalStatus


@pytest.fixture(autouse=True)
def setup_db():
    seed_database(db_client)


def test_coordinator_sms_approval_flow():
    # 1. Trigger an alert first to create a pending proposal
    weather_event = {
        "body": json.dumps({
            "event": "Flash Flood",
            "description": "Basement flooding at 10 Main St",
            "address": "10 Main St, Downtown",
            "latitude": 40.7130,
            "longitude": -74.0065
        })
    }
    weather_resp = weather_handler(weather_event, None)
    weather_body = json.loads(weather_resp["body"])
    proposal_id = weather_body["result"]["proposal"]["proposal_id"]
    resource_id = weather_body["result"]["best_match"]["resource_id"]

    # 2. Coordinator sends 'YES' via Twilio SMS Webhook
    sms_event = {
        "From": "+15550199283",
        "Body": "YES",
        "MessageSid": "SM9876543210"
    }
    sms_resp = sms_handler(sms_event, None)
    assert sms_resp["statusCode"] == 200
    assert "APPROVED" in sms_resp["body"]

    # 3. Check DynamoDB state
    proposal = db_client.get_proposal(proposal_id)
    assert proposal.status == ProposalStatus.APPROVED
    assert proposal.approved_at is not None

    resource = db_client.get_resource(resource_id)
    assert resource.status == ResourceStatus.DISPATCHED


def test_coordinator_sms_rejection_flow():
    # 1. Trigger alert
    weather_event = {
        "body": json.dumps({
            "event": "Flash Flood",
            "description": "Basement flooding at 10 Main St",
            "address": "10 Main St, Downtown",
            "latitude": 40.7130,
            "longitude": -74.0065
        })
    }
    weather_resp = weather_handler(weather_event, None)
    weather_body = json.loads(weather_resp["body"])
    proposal_id = weather_body["result"]["proposal"]["proposal_id"]

    # 2. Coordinator sends 'NO'
    sms_event = {
        "From": "+15550199283",
        "Body": "NO",
        "MessageSid": "SM111222333"
    }
    sms_resp = sms_handler(sms_event, None)
    assert sms_resp["statusCode"] == 200
    assert "rejected" in sms_resp["body"].lower()

    # 3. Check DynamoDB state
    proposal = db_client.get_proposal(proposal_id)
    assert proposal.status == ProposalStatus.REJECTED


def test_coordinator_sms_urlencoded_form():
    # Test standard Twilio form-urlencoded body
    sms_event = {
        "body": "From=%2B15550199283&Body=STATUS&MessageSid=SM333444"
    }
    sms_resp = sms_handler(sms_event, None)
    assert sms_resp["statusCode"] == 200
    assert "<Response><Message>" in sms_resp["body"]
