#!/usr/bin/env python3
from pydantic import BaseModel, field_validator, validator

class EntityIdentifier(BaseModel):
    """Basic entity identifier with blueprint and identifier fields."""
    identifier: str
    blueprint: str


class Entity(BaseModel):
    """Entity wrapper for Port API."""
    entity: EntityIdentifier


class PortYaml(BaseModel):
    """Basic validation model for Port YAML files."""
    identifier: str
    blueprint: str
    
    @validator("identifier")
    def validate_identifier(cls, v):
        if not v:
            raise ValueError("Identifier must be provided")
        return v

    @validator("blueprint")
    def validate_blueprint(cls, v):
        if not v:
            raise ValueError("Blueprint must be provided")
        return v


class DevPortalAPI(BaseModel):
    """Detailed validation model for DevPortal API YAML files."""
    identifier: str
    blueprint: str
    description: str
    qos: str
    tier: int | str  # Allow either integer or string for tier
    product_manager: str
    owning_team: str
    exec_sponsor: str
    name: str
    repository: str
    
    @field_validator('identifier', 'blueprint', 'description', 'qos', 'product_manager', 'owning_team', 'exec_sponsor', 'name', 'repository')
    def check_string_not_empty(cls, v, info):
        if not v or not isinstance(v, str) or v.strip() == "":
            raise ValueError(f"❌ Field '{info.field_name}' must not be null or empty")
        return v

    @field_validator('tier')
    def check_tier_not_empty(cls, v):
        if v is None:
            raise ValueError("❌ Field 'tier' must not be null")
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str) and v.strip() == "":
            raise ValueError("❌ Field 'tier' must not be empty")
        return v
