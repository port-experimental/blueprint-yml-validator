import httpx
import yaml
from typing import Dict, Any, Tuple, List
from pathlib import Path

from port_common.settings import PortSettings

def load_yaml(path: str) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


async def get_entity(client: httpx.AsyncClient, settings: PortSettings, identifier: str, blueprint: str) -> bool:
    """Check if an entity exists in Port."""
    # Check if token needs refresh
    if settings.token_expired:
        await settings.get_access_token(client)
        
    url = f"{settings.PORT_BASE_URL}/blueprints/{blueprint}/entities/{identifier}"
    response = await client.get(url, headers=settings.headers)
    return response.status_code == 200

async def get_blueprint_schema(client: httpx.AsyncClient, settings: PortSettings, blueprint: str) -> Dict[str, Any]:
    """Get the schema for a blueprint from Port."""
    # Check if token needs refresh
    if settings.token_expired:
        await settings.get_access_token(client)
    
    url = f"{settings.PORT_BASE_URL}/blueprints/{blueprint}"
    response = await client.get(url, headers=settings.headers)
    return response.json()


async def validate_required_fields(client: httpx.AsyncClient, settings: PortSettings, data: Dict[str, Any], blueprint_name: str) -> List[str]:
    """Validate that all required fields from the blueprint schema are present in the data."""
    errors = []
    
    try:
        # Get the blueprint schema from Port API
        blueprint_data = await get_blueprint_schema(client, settings, blueprint_name)
        
        # Extract required fields from the schema
        required_fields = blueprint_data.get("blueprint", {}).get("schema", {}).get("required", [])
        
        if required_fields:
            print(f"Required fields according to blueprint schema: {', '.join(required_fields)}")
            
            # Check if all required fields are present in the data
            properties = data.get("properties", {})
            missing_fields = [field for field in required_fields if field not in properties]
            
            if missing_fields:
                errors.append(f"Missing required fields: {', '.join(missing_fields)}")
                
    except Exception as e:
        errors.append(f"Error validating required fields: {str(e)}")
        
    return errors


async def validate_entity(client: httpx.AsyncClient, settings: PortSettings, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Validate an entity against Port's API."""
    # Check if token needs refresh
    if settings.token_expired:
        await settings.get_access_token(client)
    
    try:
        blueprint = payload.get("blueprint", "")
        identifier = payload.get("identifier", "")
        
        url = f"{settings.PORT_BASE_URL}/blueprints/{blueprint}/entities/{identifier}"
        print(f"Checking if entity exists at {url}")
        
        get_response = await client.get(url, headers=settings.headers)
        entity_exists = get_response.status_code == 200
        
        if entity_exists:
            print(f"Entity '{identifier}' of blueprint '{blueprint}' exists")
            return True, {"message": "Entity exists"}
        else:
            print(f"Entity '{identifier}' of blueprint '{blueprint}' does not exist — updates only allowed on existing entities")
            return False, {"error": "Entity does not exist. Only updates to existing entities are allowed."}
            
    except Exception as e:
        print(f"❌ Error during entity validation: {str(e)}")
        return False, {"error": str(e)}


def find_yaml_files(paths: List[str] = None) -> List[Path]:
    """Find YAML files to validate, excluding those in .github directory."""
    changed_files = []
    
    # If paths are provided, use them; otherwise scan the current directory
    if paths:
        for path in paths:
            p = Path(path)
            if p.is_dir():
                # Only include files directly in the specified directory, not in subdirectories
                changed_files.extend([f for f in p.glob("*.yaml") if ".github" not in str(f)])
                changed_files.extend([f for f in p.glob("*.yml") if ".github" not in str(f)])
            elif p.is_file() and p.suffix.lower() in (".yaml", ".yml") and ".github" not in str(p):
                changed_files.append(p)
            else:
                print(f"Warning: {path} is not a YAML file or directory")
    else:
        # Only include files directly in the root directory, not in subdirectories
        changed_files = [f for f in Path(".").glob("*.yaml") if ".github" not in str(f)]
        changed_files.extend([f for f in Path(".").glob("*.yml") if ".github" not in str(f)])
    
    return changed_files


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
            from port_common.models import PortYaml
            port_yaml = PortYaml(**data)
        except ValueError as e:
            return [f"Invalid YAML structure in {file_path}: {str(e)}"]
            
        identifier = port_yaml.identifier
        blueprint = port_yaml.blueprint
        
        # Validate required fields from blueprint schema
        print(f"Validating required fields for {file_path} against {blueprint} blueprint schema...")
        schema_errors = await validate_required_fields(client, settings, data, blueprint)
        if schema_errors:
            errors.extend(schema_errors)
            return errors
        
        # Check if entity exists
        exists = await get_entity(client, settings, identifier, blueprint)
        print(f"Entity '{identifier}' of blueprint '{blueprint}' exists: {exists}")
        if not exists:
            errors.append(f"Entity '{identifier}' of blueprint '{blueprint}' does not exist — updates only allowed")
            
    except Exception as e:
        errors.append(f"Error processing {file_path}: {str(e)}")
        
    return errors
