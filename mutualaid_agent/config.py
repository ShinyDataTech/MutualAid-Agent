"""
Configuration settings for MutualAid-Agent.
Handles environment variables, AWS Bedrock Model identifiers, and system defaults.
"""

import os
from pydantic import BaseModel, Field


class AgentSettings(BaseModel):
    # AWS & Bedrock Configurations
    aws_region: str = Field(default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    bedrock_model_id: str = Field(
        default=os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
    )
    
    # DynamoDB Tables
    resources_table_name: str = Field(
        default=os.getenv("RESOURCES_TABLE", "MutualAid-Resources")
    )
    incidents_table_name: str = Field(
        default=os.getenv("INCIDENTS_TABLE", "MutualAid-Incidents")
    )
    dispatches_table_name: str = Field(
        default=os.getenv("DISPATCHES_TABLE", "MutualAid-Dispatches")
    )
    
    # Emergency Logistics Rules
    default_search_radius_miles: float = Field(default=5.0)
    max_search_radius_miles: float = Field(default=15.0)
    auto_escalation_minutes: int = Field(default=10)
    
    # Coordinator & Twilio Configurations
    coordinator_phone: str = Field(
        default=os.getenv("COORDINATOR_PHONE", "+15550199283")
    )
    twilio_phone_number: str = Field(
        default=os.getenv("TWILIO_PHONE_NUMBER", "+15550100911")
    )
    
    # Execution mode (automatically fallback to mock in-memory store if no live AWS)
    use_mock_db: bool = Field(
        default=os.getenv("USE_MOCK_DB", "false").lower() in ("true", "1", "yes")
    )


settings = AgentSettings()
