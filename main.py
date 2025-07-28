#!/usr/bin/env python3
import os
import sys
import yaml
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import httpx
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PortSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    PORT_BASE_URL: str = "https://api.getport.io/v1"
    PORT_CLIENT_ID: str
    PORT_CLIENT_SECRET: str

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.PORT_CLIENT_SECRET}",
            "Port-Client-Id": self.PORT_CLIENT_ID,
        }


class EntityIdentifier(BaseModel):
    identifier: str
    blueprint: str


class Entity(BaseModel):
    entity: EntityIdentifier


class PortYaml(BaseModel):
    entity: EntityIdentifier
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    relations: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator("entity")
    def validate_entity_fields(cls, v):
        if not v.identifier or not v.blueprint:
            raise ValueError("Both identifier and blueprint must be provided")
        return v


async def get_entity(client: httpx.AsyncClient, settings: PortSettings, identifier: str, blueprint: str) -> bool:
    """Check if an entity exists in Port."""
    url = f"{settings.PORT_BASE_URL}/blueprints/{blueprint}/entities/{identifier}"
    response = await client.get(url, headers=settings.headers)
    return response.status_code == 200


async def validate_entity(client: httpx.AsyncClient, settings: PortSettings, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Validate an entity against Port's API."""
    url = f"{settings.PORT_BASE_URL}/entities?validation_only=true"
    response = await client.post(url, headers=settings.headers, json=payload)
    return response.status_code == 200, response.json()


async def process_file(client: httpx.AsyncClient, settings: PortSettings, file_path: Path) -> List[str]:
    """Process a single YAML file and return any errors."""
    errors = []
    
    try:
        with open(file_path) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                return [f"YAML parse error in {file_path}: {str(e)}"]
        
        try:
            port_yaml = PortYaml(**data)
        except ValueError as e:
            return [f"Invalid YAML structure in {file_path}: {str(e)}"]
            
        identifier = port_yaml.entity.identifier
        blueprint = port_yaml.entity.blueprint
        
        exists = await get_entity(client, settings, identifier, blueprint)
        if not exists:
            errors.append(f"Entity '{identifier}' of blueprint '{blueprint}' does not exist — updates only allowed")
        
        valid, response = await validate_entity(client, settings, data)
        if not valid:
            errors.append(f"Validation failed for {file_path}: {response}")
            
    except Exception as e:
        errors.append(f"Error processing {file_path}: {str(e)}")
        
    return errors


async def main():
    parser = argparse.ArgumentParser(description="Validate YAML files against Port API")
    parser.add_argument("--paths", nargs="+", help="Paths to YAML files or directories to scan")
    args = parser.parse_args()
    
    try:
        settings = PortSettings()
    except Exception as e:
        print(f"❌ Error loading environment variables: {str(e)}")
        sys.exit(1)
    
    errors = []
    changed_files = []
    
    # If paths are provided, use them; otherwise scan the current directory
    if args.paths:
        for path in args.paths:
            p = Path(path)
            if p.is_dir():
                changed_files.extend(list(p.rglob("*.yaml")))
                changed_files.extend(list(p.rglob("*.yml")))
            elif p.is_file() and p.suffix.lower() in (".yaml", ".yml"):
                changed_files.append(p)
            else:
                print(f"Warning: {path} is not a YAML file or directory")
    else:
        changed_files = list(Path(".").rglob("*.yaml")) + list(Path(".").rglob("*.yml"))
    
    if not changed_files:
        print("No YAML files found to validate")
        return
        
    print(f"Found {len(changed_files)} YAML files to validate")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [process_file(client, settings, file_path) for file_path in changed_files]
        results = await asyncio.gather(*tasks)
        
        for file_errors in results:
            errors.extend(file_errors)
    
    if errors:
        for e in errors:
            print("❌", e)
        sys.exit(1)
    else:
        print("✅ All YAML files validated successfully.")


if __name__ == "__main__":
    asyncio.run(main())
