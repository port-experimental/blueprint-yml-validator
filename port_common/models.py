from pydantic import BaseModel, validator
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
