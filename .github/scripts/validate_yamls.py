# .github/scripts/validate_yamls.py
import os
import sys
import requests
import yaml
from pathlib import Path

PORT_BASE_URL = os.getenv("PORT_BASE_URL", "https://api.getport.io/v1")
PORT_CLIENT_ID = os.getenv("PORT_CLIENT_ID")
PORT_CLIENT_SECRET = os.getenv("PORT_CLIENT_SECRET")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {PORT_CLIENT_SECRET}",
    "Port-Client-Id": PORT_CLIENT_ID,
}

def get_entity(identifier, blueprint):
    url = f"{PORT_BASE_URL}/blueprints/{blueprint}/entities/{identifier}"
    response = requests.get(url, headers=HEADERS)
    return response.status_code == 200

def validate_entity(payload):
    url = f"{PORT_BASE_URL}/entities?validation_only=true"
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.status_code == 200, response.json()

def main():
    errors = []
    changed_files = list(Path(".").rglob("*.yaml")) + list(Path(".").rglob("*.yml"))

    for file_path in changed_files:
        with open(file_path) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"YAML parse error in {file_path}: {str(e)}")
                continue

        entity = data.get("entity", {})
        identifier = entity.get("identifier")
        blueprint = entity.get("blueprint")

        if not identifier or not blueprint:
            errors.append(f"Missing identifier/blueprint in {file_path}")
            continue

        exists = get_entity(identifier, blueprint)
        if not exists:
            errors.append(f"Entity '{identifier}' of blueprint '{blueprint}' does not exist — updates only allowed")

        valid, response = validate_entity(data)
        if not valid:
            errors.append(f"Validation failed for {file_path}: {response}")

    if errors:
        for e in errors:
            print("❌", e)
        sys.exit(1)
    else:
        print("✅ All YAML files validated successfully.")

if __name__ == "__main__":
    main()
