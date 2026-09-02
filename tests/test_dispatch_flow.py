"""
End-to-end integration test validating autonomous background dispatch flow.
"""

import json
import pytest
from mutualaid_agent.agent import coordinator
from mutualaid_agent.db.seed_data import seed_database
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import ResourceStatus, ProposalStatus


@pytest.fixture(autouse=True)
def setup_db():
    seed_database(db_client)


def test_full_autonomous_emergency_dispatch_lifecycle():
    # 1. Ingest alert payload
    raw_alert = json.dumps({
        "source": "NWS_ALERT_SYSTEM",
        "event": "Flash Flood Warning",
        "headline": "Severe flooding reported near River Rd",
        "description": "High water levels threatening homes. High flow pump needed urgently.",
        "address": "50 River Rd, Downtown",
        "latitude": 40.7145,
        "longitude": -74.0055
    })

    # 2. Process alert autonomously
    result = coordinator.process_incoming_alert(raw_alert)

    assert result["status"] == "PROPOSAL_PENDING_APPROVAL"
    assert result["incident"]["required_resource_type"] == "submersible_pump"
    assert result["best_match"]["resource_id"] == "res-pump-002"  # Closest to 50 River Rd
    proposal_id = result["proposal"]["proposal_id"]

    # Verify SMS format contains the single-decision structure
    sms = result["proposal"]["single_decision_sms"]
    assert "Reply YES to approve" in sms
    assert "Neighbor Dave" in sms

    # 3. Simulate coordinator responding YES
    decision = coordinator.handle_inbound_sms(
        from_number="+15550199283",
        body="YES"
    )

    assert decision["status"] == "APPROVED"
    assert "APPROVED" in decision["reply_sms"]

    # 4. Verify DynamoDB data integrity
    saved_proposal = db_client.get_proposal(proposal_id)
    assert saved_proposal.status == ProposalStatus.APPROVED
    assert saved_proposal.approved_at is not None

    dispatched_resource = db_client.get_resource("res-pump-002")
    assert dispatched_resource.status == ResourceStatus.DISPATCHED


def test_rejection_and_fallback_to_alternative_asset():
    # 1. Ingest alert near 10 Main St
    raw_alert = json.dumps({
        "source": "CITIZEN_APP",
        "event": "Basement Flooding",
        "headline": "Water entering basement",
        "description": "Submersible pump needed immediately",
        "address": "10 Main St, Downtown",
        "latitude": 40.7130,
        "longitude": -74.0065
    })

    result = coordinator.process_incoming_alert(raw_alert)
    assert result["best_match"]["resource_id"] == "res-pump-001"  # Bob's pump is closest

    # 2. Coordinator rejects Bob's pump (e.g. Bob is out of town)
    decision = coordinator.handle_inbound_sms(
        from_number="+15550199283",
        body="NO"
    )

    assert decision["status"] == "REJECTED"
    assert decision["alternative_proposal"] is not None
    # Next alternative should be Dave's pump (res-pump-002)
    assert decision["alternative_proposal"]["resource_id"] == "res-pump-002"
