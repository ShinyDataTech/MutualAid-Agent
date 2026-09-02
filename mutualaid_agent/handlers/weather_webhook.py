"""
AWS Lambda Handler for incoming Weather & Emergency Alert Webhooks.
Triggered by API Gateway when severe weather or disaster alerts arrive.
"""

import json
import logging
from typing import Dict, Any
from mutualaid_agent.agent import coordinator

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for processing incoming emergency weather alerts.

    Expected event:
    - API Gateway proxy event with JSON string in 'body'
    - Or direct invocation event payload
    """
    logger.info(f"Received Weather Webhook Event: {json.dumps(event)}")

    # Extract body from API Gateway proxy format or direct invoke
    body = event.get("body")
    if body is None:
        raw_payload = json.dumps(event)
    elif isinstance(body, str):
        raw_payload = body
    else:
        raw_payload = json.dumps(body)

    try:
        result = coordinator.process_incoming_alert(raw_payload)
        status_code = 200 if result.get("status") != "NO_MATCH_FOUND" else 202

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Emergency alert processed autonomously by MutualAid-Agent",
                "result": result
            })
        }
    except Exception as e:
        logger.error(f"Error processing weather alert webhook: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Failed to process emergency alert",
                "details": str(e)
            })
        }
