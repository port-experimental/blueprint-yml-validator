import sys
import asyncio
import argparse
import httpx

from port_common.settings import PortSettings
from port_common.api import find_yaml_files, process_file


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
    
    # Find YAML files to validate using our shared function
    changed_files = find_yaml_files(args.paths if args.paths else None)
    
    if not changed_files:
        print("No YAML files found to validate")
        return
        
    print(f"Found {len(changed_files)} YAML files to validate")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First obtain the access token
        try:
            await settings.get_access_token(client)
        except Exception as e:
            print(f"❌ Error obtaining access token: {str(e)}")
            sys.exit(1)
            
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
