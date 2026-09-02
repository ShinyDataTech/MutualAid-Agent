"""
Tests for matchmaking engine and geospatial proximity calculations.
"""

import pytest
from mutualaid_agent.engine.matcher import haversine_distance_miles, find_matching_resources
from mutualaid_agent.db.models import (
    IncidentAlert,
    IncidentType,
    IncidentSeverity,
    ResourceType,
    ResourceStatus,
    CommunityResource
)
from mutualaid_agent.db.dynamodb_client import DynamoDBClient


def test_haversine_distance_accuracy():
    # NYC Coordinates: Times Square (40.7580, -73.9855) to Empire State Building (40.7484, -73.9857)
    # Approx 0.66 miles
    dist = haversine_distance_miles(40.7580, -73.9855, 40.7484, -73.9857)
    assert 0.60 <= dist <= 0.75


def test_matchmaking_ranking_by_proximity():
    client = DynamoDBClient(use_mock=True)

    # Put two pumps at different distances
    close_pump = CommunityResource(
        resource_id="pump-close",
        owner_name="Neighbor Close",
        owner_phone="+15550001111",
        resource_type=ResourceType.SUBMERSIBLE_PUMP,
        title="Close Sump Pump",
        description="Near pump",
        address="10 Main St",
        latitude=40.7130,
        longitude=-74.0060,
        status=ResourceStatus.AVAILABLE
    )
    far_pump = CommunityResource(
        resource_id="pump-far",
        owner_name="Neighbor Far",
        owner_phone="+15550002222",
        resource_type=ResourceType.SUBMERSIBLE_PUMP,
        title="Far Sump Pump",
        description="Far pump",
        address="99 Distant Rd",
        latitude=40.7500,
        longitude=-73.9500,
        status=ResourceStatus.AVAILABLE
    )
    client.put_resource(close_pump)
    client.put_resource(far_pump)

    incident = IncidentAlert(
        incident_id="inc-test-01",
        incident_type=IncidentType.FLOOD,
        severity=IncidentSeverity.SEVERE,
        title="Flash Flood",
        description="Water in basement",
        address="10 Main St",
        latitude=40.7130,
        longitude=-74.0060,
        required_resource_type=ResourceType.SUBMERSIBLE_PUMP
    )

    matches = find_matching_resources(incident, max_radius_miles=10.0, client=client)
    assert len(matches) >= 2
    assert matches[0].resource.resource_id == "pump-close"
    assert matches[0].distance_miles < matches[1].distance_miles


def test_matchmaking_respects_max_radius():
    client = DynamoDBClient(use_mock=True)

    far_away_pump = CommunityResource(
        resource_id="pump-very-far",
        owner_name="Neighbor Outback",
        owner_phone="+15550009999",
        resource_type=ResourceType.SUBMERSIBLE_PUMP,
        title="Outback Pump",
        description="Very far away",
        address="100 Far Away",
        latitude=41.5000,
        longitude=-73.0000,
        status=ResourceStatus.AVAILABLE
    )
    client.put_resource(far_away_pump)

    incident = IncidentAlert(
        incident_id="inc-test-02",
        incident_type=IncidentType.FLOOD,
        severity=IncidentSeverity.SEVERE,
        title="Basement Flood",
        description="Flood",
        address="10 Main St",
        latitude=40.7130,
        longitude=-74.0060,
        required_resource_type=ResourceType.SUBMERSIBLE_PUMP
    )

    matches = find_matching_resources(incident, max_radius_miles=5.0, client=client)
    outback_matches = [m for m in matches if m.resource.resource_id == "pump-very-far"]
    assert len(outback_matches) == 0
