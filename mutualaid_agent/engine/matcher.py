"""
Matchmaking Engine for MutualAid-Agent.
Calculates geospatial proximity using the Haversine formula and scores available equipment against incident needs.
"""

import math
from typing import List, Tuple, Optional
from mutualaid_agent.db.models import (
    CommunityResource,
    IncidentAlert,
    ResourceType,
    ResourceStatus
)
from mutualaid_agent.db.dynamodb_client import db_client


def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in miles between two coordinates on Earth.
    """
    # Earth radius in miles
    R = 3958.8

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return round(distance, 2)


class MatchResult:
    def __init__(self, resource: CommunityResource, distance_miles: float, match_score: float):
        self.resource = resource
        self.distance_miles = distance_miles
        self.match_score = match_score

    def to_dict(self):
        return {
            "resource_id": self.resource.resource_id,
            "title": self.resource.title,
            "owner_name": self.resource.owner_name,
            "owner_phone": self.resource.owner_phone,
            "address": self.resource.address,
            "distance_miles": self.distance_miles,
            "match_score": self.match_score,
            "capacity_specs": self.resource.capacity_specs
        }


def find_matching_resources(
    incident: IncidentAlert,
    max_radius_miles: float = 10.0,
    client=None
) -> List[MatchResult]:
    """
    Queries DynamoDB for resources matching the incident's required equipment type,
    calculates distance to the incident location, and ranks candidates.
    """
    target_client = client or db_client
    available_resources = target_client.list_resources(
        resource_type=incident.required_resource_type,
        status=ResourceStatus.AVAILABLE
    )

    matches: List[MatchResult] = []
    for res in available_resources:
        dist = haversine_distance_miles(
            incident.latitude,
            incident.longitude,
            res.latitude,
            res.longitude
        )
        if dist <= max_radius_miles:
            # Score formula: closer distance produces higher score (e.g. 100 - dist * 5)
            score = max(0.0, round(100.0 - (dist * 5.0), 1))
            matches.append(MatchResult(resource=res, distance_miles=dist, match_score=score))

    # Sort matches by distance ascending (closest first)
    matches.sort(key=lambda m: m.distance_miles)
    return matches
