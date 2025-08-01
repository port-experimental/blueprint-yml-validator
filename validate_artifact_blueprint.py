import sys
import asyncio
import httpx
from pydantic import ValidationError

from port_common.settings import PortSettings
from port_common.models import DevPortalAPI
from port_common.api import load_yaml, validate_entity

FILE_PATH = "devportal-api.yaml"


async def main():
    try:
        print("🔍 Loading YAML...")
        data = load_yaml(FILE_PATH)

        print("🔎 Validating required fields...")
        try:
            api_data = DevPortalAPI(**data)
            print("✅ All required fields are valid")
        except ValidationError as e:
            print(f"❌ Validation error: {e}")
            sys.exit(1)

        print("🔍 Setting up authentication...")
        settings = PortSettings()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await settings.get_access_token(client)
            except Exception as e:
                print(f"❌ Error obtaining access token: {str(e)}")
                sys.exit(1)
                
            print("🔍 Sending to Port for validation...")
            valid, response = await validate_entity(client, settings, api_data.model_dump())
            
            if not valid:
                print(f"❌ Validation failed: {response}")
                sys.exit(1)
                
            print("✅ All validations passed!")

    except Exception as e:
        print(f"❌ {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
