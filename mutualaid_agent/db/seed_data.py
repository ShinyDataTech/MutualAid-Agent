"""
Seed data module for initializing community resources in DynamoDB.
"""

from typing import List
from mutualaid_agent.db.models import CommunityResource, ResourceType, ResourceStatus
from mutualaid_agent.db.dynamodb_client import db_client


COMMUNITY_RESOURCES: List[CommunityResource] = [
    CommunityResource(
        resource_id="res-pump-001",
        owner_name="Neighbor Bob (Robert Martinez)",
        owner_phone="+15550112233",
        resource_type=ResourceType.SUBMERSIBLE_PUMP,
        title="2-inch Submersible Heavy Duty Pump",
        description="Electric 3,000 GPH water pump with 50ft discharge hose. Ideal for flooded basements and driveways.",
        capacity_specs="3000 GPH / 120V",
        address="14 Maple St, Downtown",
        latitude=40.7128,
        longitude=-74.0060,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Call or text anytime during weather emergencies. Pump stored in side shed."
    ),
    CommunityResource(
        resource_id="res-pump-002",
        owner_name="Neighbor Dave (David Wilson)",
        owner_phone="+15550117788",
        resource_type=ResourceType.SUBMERSIBLE_PUMP,
        title="3-inch High-Flow Sump Pump",
        description="Gas-powered high-capacity water evacuation pump. 5,500 GPH capability with heavy-duty hoses.",
        capacity_specs="5500 GPH / Gas Powered",
        address="50 River Rd, Downtown",
        latitude=40.7145,
        longitude=-74.0055,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Text before pickup. Extra gas can included."
    ),
    CommunityResource(
        resource_id="res-gen-001",
        owner_name="Neighbor Sarah (Sarah Jenkins)",
        owner_phone="+15550114455",
        resource_type=ResourceType.GENERATOR,
        title="Honda 7000W Inverter Generator",
        description="Quiet, reliable generator with 30A twist lock and standard 120V outlets. Full fuel tank.",
        capacity_specs="7000W / Dual Fuel",
        address="22 Oak Ave, Downtown",
        latitude=40.7150,
        longitude=-74.0040,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Priority reserved for neighbors with medical devices or refrigeration needs."
    ),
    CommunityResource(
        resource_id="res-saw-001",
        owner_name="Neighbor Carlos (Carlos Ramirez)",
        owner_phone="+15550116677",
        resource_type=ResourceType.CHAINSAW,
        title="Stihl 18-inch Gas Chainsaw & Chaps",
        description="Professional wood cutting chainsaw with extra chains, bar oil, and full PPE gear.",
        capacity_specs="18-inch bar / 50cc",
        address="5 Pine Rd, Downtown",
        latitude=40.7180,
        longitude=-74.0090,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Carlos is certified in tree clearing and can assist in operation."
    ),
    CommunityResource(
        resource_id="res-sand-001",
        owner_name="Community Center Staging Area",
        owner_phone="+15550119900",
        resource_type=ResourceType.SANDBAGS,
        title="Pre-Filled Sandbags (Bundle of 100)",
        description="Heavy-duty woven polypropylene sandbags pre-filled and palletized for flood diversion.",
        capacity_specs="100 bags (approx 40 lbs each)",
        address="100 Main St, Downtown",
        latitude=40.7135,
        longitude=-74.0070,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Loading dock open 24/7 during municipal storm warnings."
    ),
    CommunityResource(
        resource_id="res-truck-001",
        owner_name="Neighbor Elena (Elena Rostova)",
        owner_phone="+15550113322",
        resource_type=ResourceType.FOUR_WHEEL_DRIVE,
        title="Ford F-250 4x4 High-Clearance Truck with Winch",
        description="4WD heavy-duty truck equipped with 12,000 lb front winch, recovery straps, and high air intake.",
        capacity_specs="4WD / 12000 lb Winch",
        address="88 Elm St, Downtown",
        latitude=40.7110,
        longitude=-74.0020,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Available for towing and emergency transport through flooded roads."
    ),
    CommunityResource(
        resource_id="res-med-001",
        owner_name="Neighbor Dr. Marcus (Marcus Vance)",
        owner_phone="+15550115544",
        resource_type=ResourceType.MEDICAL_KIT,
        title="Comprehensive Trauma First Aid Kit & AED",
        description="BLS medical kit, automated external defibrillator (AED), tourniquets, burn dressings, splints.",
        capacity_specs="BLS Level / Portable AED",
        address="34 Birch Ln, Downtown",
        latitude=40.7160,
        longitude=-74.0080,
        status=ResourceStatus.AVAILABLE,
        contact_notes="Physician on-site; can provide direct medical oversight if needed."
    )
]


def seed_database(client=None) -> int:
    """Seeds the community resources into DynamoDB / local store."""
    target_client = client or db_client
    count = 0
    for res in COMMUNITY_RESOURCES:
        if target_client.put_resource(res):
            count += 1
    return count


if __name__ == "__main__":
    count = seed_database()
    print(f"Successfully seeded {count} community resources.")
