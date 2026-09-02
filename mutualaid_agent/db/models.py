"""
Data models for MutualAid-Agent.
Represents community resources, incident alerts, dispatch proposals, and SMS interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    SUBMERSIBLE_PUMP = "submersible_pump"
    GENERATOR = "generator"
    CHAINSAW = "chainsaw"
    SANDBAGS = "sandbags"
    FOUR_WHEEL_DRIVE = "four_wheel_drive"
    MEDICAL_KIT = "medical_kit"
    DEBRIS_TARPS = "debris_tarps"
    BOAT = "boat"
    PORTABLE_HEATER = "portable_heater"


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    DISPATCHED = "dispatched"
    MAINTENANCE = "maintenance"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    FLOOD = "flood"
    STORM_WIND = "storm_wind"
    POWER_OUTAGE = "power_outage"
    TREE_OBSTRUCTION = "tree_obstruction"
    BLIZZARD = "blizzard"
    STRUCTURAL_DAMAGE = "structural_damage"


class ProposalStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CommunityResource(BaseModel):
    resource_id: str
    owner_name: str
    owner_phone: str
    resource_type: ResourceType
    title: str
    description: str
    capacity_specs: str = "Standard"
    address: str
    latitude: float
    longitude: float
    status: ResourceStatus = ResourceStatus.AVAILABLE
    contact_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IncidentAlert(BaseModel):
    incident_id: str
    source: str = "NWS_WEATHER_API"
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    address: str
    latitude: float
    longitude: float
    required_resource_type: ResourceType
    raw_payload: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"


class DispatchProposal(BaseModel):
    proposal_id: str
    incident_id: str
    resource_id: str
    resource_title: str
    owner_name: str
    owner_phone: str
    target_address: str
    distance_miles: float
    rationale: str
    single_decision_sms: str
    status: ProposalStatus = ProposalStatus.PENDING_APPROVAL
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    approved_at: Optional[str] = None
    coordinator_notes: Optional[str] = None


class SMSAction(str, Enum):
    APPROVE = "YES"
    REJECT = "NO"
    STATUS = "STATUS"
    HELP = "HELP"


class InboundSMS(BaseModel):
    from_number: str
    to_number: str
    body: str
    message_sid: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
