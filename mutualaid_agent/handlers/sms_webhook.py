"""
AWS Lambda Handler for incoming SMS Webhooks (Twilio / Pinpoint).
Triggered when the human coordinator replies (e.g. YES, NO, STATUS).
"""

import json
import logging
import urllib.parse
from typing import Dict, Any
from mutualaid_agent.agent import coordinator

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _parse_incoming_payload(event: Dict[str, Any]) -> Dict[str, str]:
    """Extracts From and Body parameters from Twilio form-data or JSON."""
    if "From" in event and "Body" in event:
        return {"From": event["From"], "Body": event["Body"]}

    body = event.get("body", "")
    if not body:
        return {}

    # Check if base64 encoded
    if event.get("isBase64Encoded", False):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    # Try parsing URL-encoded form data (standard Twilio webhook)
    if "=" in body:
        parsed_qs = urllib.parse.parse_qs(body)
        from_val = parsed_qs.get("From", [""])[0]
        body_val = parsed_qs.get("Body", [""])[0]
        if from_val or body_val:
            return {"From": from_val, "Body": body_val}

    # Try JSON
    try:
        data = json.loads(body)
        return {
            "From": data.get("From", data.get("from_number", "")),
            "Body": data.get("Body", data.get("body", ""))
        }
    except Exception:
        return {"From": "", "Body": body}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Processes incoming SMS replies from the human-in-the-loop coordinator.
    """
    logger.info(f"Received SMS Webhook Event: {json.dumps(event)}")
    params = _parse_incoming_payload(event)

    from_number = params.get("From", "")
    sms_body = params.get("Body", "")

    if not sms_body:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing SMS body in payload"})
        }

    try:
        decision_result = coordinator.handle_inbound_sms(
            from_number=from_number,
            body=sms_body
        )

        reply_sms = decision_result.get("reply_sms", "")
        # TwiML formatted XML response for Twilio
        twiml_response = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply_sms}</Message></Response>'

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/xml",
                "Access-Control-Allow-Origin": "*"
            },
            "body": twiml_response
        }
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
