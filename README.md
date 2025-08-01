# GitHub YAML Validator for Port

A tool for validating YAML files against Port's API. This validator ensures that your YAML files are properly formatted and that the entities they reference exist in your Port instance.

## Features

- Validates YAML files against Port's API
- Asynchronous processing for faster validation
- Supports custom YAML file paths
- Pydantic validation for entities and settings
- Modular code structure for better maintainability

## Requirements

- Python 3.9+
- Port API credentials (CLIENT_ID and CLIENT_SECRET)

## Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/your-org/github-validator.git
cd github-validator

# Install dependencies
pip install -r requirements.txt
```

### Docker

You can also use the Docker image:

```bash
docker pull ghcr.io/your-org/github-validator:latest
```

## Project Structure

```
.
├── main.py                      # Main script for validating all YAML files
├── validate_artifact_blueprint.py # Script for validating devportal-api.yaml
├── port_common/                 # Shared modules
│   ├── __init__.py             # Package initialization
│   ├── settings.py             # Port API settings and authentication
│   ├── models.py               # Pydantic models for validation
│   └── api.py                  # API interaction functions
├── .github/workflows/          # GitHub Actions workflows
└── requirements.txt            # Python dependencies
```

## Usage

### Local Usage

```bash
# Set environment variables
export PORT_CLIENT_ID="your-client-id"
export PORT_CLIENT_SECRET="your-client-secret"

# Run with default settings (scans current directory)
python main.py

# Run with specific YAML files or directories
python main.py --paths path/to/file.yaml path/to/directory

# Run validation for devportal-api.yaml only
python validate_artifact_blueprint.py
```

### Docker Usage

```bash
docker run --rm \
  -e PORT_CLIENT_ID="your-client-id" \
  -e PORT_CLIENT_SECRET="your-client-secret" \
  -v $(pwd):/data \
  ghcr.io/your-org/github-validator:latest --paths /data
```

## GitHub Actions Integration

This validator can be integrated into your GitHub Actions workflow to validate YAML files before they are merged.

```yaml
# Example workflow usage
- name: Validate YAML files
  uses: your-org/github-validator@main
  with:
    client_id: ${{ secrets.PORT_CLIENT_ID }}
    client_secret: ${{ secrets.PORT_CLIENT_SECRET }}
```

## License

MIT
