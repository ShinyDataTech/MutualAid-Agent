"""
Interactive Local Demo for MutualAid-Agent.
Simulates end-to-end autonomous background emergency logistics:
1. Community DynamoDB registry initialization.
2. Ingestion of a severe flash flood alert via webhook.
3. Autonomous matchmaking and single-decision SMS drafting by Strands Agents SDK.
4. Human-in-the-loop coordinator approval via simulated SMS reply ('YES').
5. Final dispatch execution and status update in DynamoDB.
"""

import os
import sys
import json
import time

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mutualaid_agent.db.seed_data import seed_database
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import ResourceStatus
from mutualaid_agent.handlers.weather_webhook import lambda_handler as weather_handler
from mutualaid_agent.handlers.sms_webhook import lambda_handler as sms_handler


def print_banner():
    banner = """
================================================================================
           MUTUALAID-AGENT: AUTONOMOUS EMERGENCY LOGISTICS AGENT
      Agents for Humans Hackathon 2026 | Track: Good Neighbor Agents
                 Powered by AWS Bedrock & Strands Agents SDK
================================================================================
"""
    print(banner)


def run_demo():
    print_banner()

    # Step 1: Seed local community resources
    print("\n[PHASE 1] Initializing Community Inventory in DynamoDB...")
    count = seed_database()
    print(f" -> Successfully seeded {count} neighborhood mutual aid assets into DynamoDB.")

    # Show available assets
    resources = db_client.list_resources(status=ResourceStatus.AVAILABLE)
    print(f"\n[ACTIVE COMMUNITY ASSETS REGISTERED ({len(resources)})]")
    print(f"{'Resource ID':<16} | {'Resource Name':<38} | {'Owner':<22} | {'Status'}")
    print("-" * 90)
    for r in resources:
        print(f"{r.resource_id:<16} | {r.title[:38]:<38} | {r.owner_name[:22]:<22} | {r.status.value.upper()}")

    time.sleep(1)

    # Step 2: Simulate incoming weather alert webhook
    print("\n" + "=" * 80)
    print("[PHASE 2] Ingesting Live Severe Weather Alert via API Gateway / Lambda Webhook...")
    print("=" * 80)

    simulated_weather_webhook_event = {
        "body": json.dumps({
            "source": "NWS_STORM_RADAR_FEED",
            "event": "Flash Flood Warning",
            "headline": "Flash Flood Warning issued for Downtown River Basin",
            "description": "Rapid water accumulation observed at 10 Main St. Basement inundation and driveway flooding imminent. Rapid pumping required.",
            "address": "10 Main St, Downtown",
            "latitude": 40.7130,
            "longitude": -74.0065,
            "severity": "severe"
        })
    }

    print(f" [Incoming Webhook Payload]:\n{simulated_weather_webhook_event['body']}\n")
    print(" -> MutualAid-Agent is autonomously analyzing the alert in the background...")
    time.sleep(1)

    # Execute Lambda Weather Webhook
    weather_response = weather_handler(simulated_weather_webhook_event, None)
    response_body = json.loads(weather_response["body"])
    result = response_body["result"]

    print("\n" + "-" * 80)
    print("[AGENT AUTONOMOUS REASONING COMPLETE]")
    print("-" * 80)
    print(f" Incident ID        : {result['incident']['incident_id']}")
    print(f" Classified Need    : {result['incident']['required_resource_type']}")
    print(f" Severity Rating    : {result['incident']['severity'].upper()}")
    print(f" Matched Resource   : {result['best_match']['title']}")
    print(f" Resource Distance  : {result['best_match']['distance_miles']} miles away")
    print(f" Equipment Owner    : {result['best_match']['owner_name']} ({result['best_match']['owner_phone']})")

    # Step 3: Human-in-the-Loop SMS
    proposal_sms = result["proposal"]["single_decision_sms"]
    proposal_id = result["proposal"]["proposal_id"]

    print("\n" + "=" * 80)
    print("[PHASE 3] Single-Decision SMS Sent to Neighborhood Coordinator:")
    print("=" * 80)
    print(f"\n >>> SMS TO COORDINATOR (+1-555-019-9283) <<<\n \"{proposal_sms}\"\n")

    time.sleep(1)

    # Step 4: Simulate Coordinator Approval
    print("=" * 80)
    print("[PHASE 4] Coordinator Responds via Inbound Twilio SMS Webhook:")
    print("=" * 80)
    print(" Coordinator replies: 'YES'\n")

    simulated_sms_event = {
        "From": "+15550199283",
        "Body": "YES",
        "MessageSid": "SM1234567890abcdef"
    }

    sms_response = sms_handler(simulated_sms_event, None)

    print(" [Lambda Webhook TwiML Response]:")
    print(f" {sms_response['body']}\n")

    # Step 5: Verify DynamoDB State
    print("=" * 80)
    print("[PHASE 5] Verifying Post-Approval DynamoDB State:")
    print("=" * 80)
    updated_proposal = db_client.get_proposal(proposal_id)
    matched_resource = db_client.get_resource(result["best_match"]["resource_id"])

    print(f" Proposal Status    : {updated_proposal.status.value.upper()} (Approved at {updated_proposal.approved_at})")
    print(f" Equipment Status   : {matched_resource.title} -> {matched_resource.status.value.upper()}")
    print(f" Resource Owner     : {matched_resource.owner_name} notified for emergency staging.")
    print("\n================================================================================")
    print(" DEMO COMPLETE: Autonomous Background Agent successfully coordinated emergency")
    print(" response with single-decision human-in-the-loop oversight!")
    print("================================================================================\n")


if __name__ == "__main__":
    run_demo()
