"""
Tools package for Strands Agents SDK in MutualAid-Agent.
"""

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

ALL_AGENT_TOOLS = [
    parse_and_register_weather_alert,
    query_community_resources_by_proximity,
    get_community_inventory,
    check_resource_status,
    draft_and_send_coordinator_approval_sms,
    send_dispatch_confirmation
]

__all__ = [
    "parse_and_register_weather_alert",
    "query_community_resources_by_proximity",
    "get_community_inventory",
    "check_resource_status",
    "draft_and_send_coordinator_approval_sms",
    "send_dispatch_confirmation",
    "ALL_AGENT_TOOLS"
]
