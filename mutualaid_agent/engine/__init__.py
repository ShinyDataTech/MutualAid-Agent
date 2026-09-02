"""
Engine package for MutualAid-Agent.
"""

from mutualaid_agent.engine.matcher import (
    haversine_distance_miles,
    MatchResult,
    find_matching_resources
)
from mutualaid_agent.engine.dispatch_planner import (
    format_single_decision_sms,
    build_dispatch_proposal,
    process_coordinator_decision
)

__all__ = [
    "haversine_distance_miles",
    "MatchResult",
    "find_matching_resources",
    "format_single_decision_sms",
    "build_dispatch_proposal",
    "process_coordinator_decision"
]
