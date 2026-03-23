# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python API client for Weight Gurus (a weight tracking service). It provides an interface to:
- Fetch complete weight history
- Fetch weight history since a specific date
- Get the latest weight entry
- Manually add new weight entries
- Clean operations to remove deleted entries

The Weight Gurus API doesn't have public documentation, so the client implements workarounds for their unique data format (e.g., weights stored as integers with decimals in the last digit).

## Architecture

### Single-File Python Application (`main.py`)

The entire application is contained in a single Python file with the following structure:

**Main Class: `WeightGurus`**
- `__init__(username, password)`: Initializes credentials, sets default start date (1970-01-01)
- `__do_login()`: Private method that logs in and stores Bearer token headers
- `__get_weight_history(start_date=None)`: Private method that fetches weight data from the API
- `get_all()`: Public method to fetch all weight history
- `get_since_date(start_date)`: Public method to fetch weights since a date
- `get_latest()`: Public method to get only the most recent entry
- `get_unremoved_entries()`: Public method to clean and return entries (filtering out deleted operations)
- `manual_entry(weight, bmi, body_fat, muscle_mass, water)`: Public method to add a new weight entry

**Key Methods:**
- `_clean_operations()`, `_remove_deleted_operations()`, `_remove_operation_deleted()`, `_is_deleted_operation()`, `_is_operation_earlier()`: Static methods that work together to identify and remove deleted weight entries by comparing timestamps and weights

**Weight Transformation:**
- `transform_weight(weight)`: Converts standard weight format (e.g., "150.5") to Weight Gurus format (e.g., 1505)
- `_wg_num_to_float(number)`: Converts Weight Gurus integer format back to decimal (e.g., 1505 → 150.5)

**API Endpoints:**
- POST `https://api.weightgurus.com/v3/account/login` - Login with email, password, web flag
- GET `https://api.weightgurus.com/v3/operation/?start={date}` - Fetch weight history
- POST `https://api.weightgurus.com/v3/operation` - Create new weight entry

### Docker Setup (`Dockerfile`)

The Docker container includes:
- Python 3.11-slim base image
- Cron installed for scheduled execution
- Main application and cron job configuration

### Cron Job Configuration (`weightgurus-cron`)

Runs daily at 10 AM with up to 30 minutes of random jitter to distribute load across servers. The jitter is applied in `run_with_jitter.sh` before executing the Python script.

### Build System (`Makefile`)

Provides Docker build targets:
- `docker` - Build single-arch image
- `docker-local` - Build with `latest-local` tag
- `docker-multi` - Build multi-arch (amd64, arm64) and push to registry
- `docker-multi-local` - Build multi-arch locally without pushing
- `clean-docker` - Remove the Docker image

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application directly
python main.py username password

# Get all weight history
python main.py | get_all

# Get weight since a date
python main.py | get_since_date 2024-01-01T00:00:00Z

# Get latest weight
python main.py | get_latest

# Build Docker image
make docker

# Build and push multi-arch Docker image
make docker-multi

# Build multi-arch image locally
make docker-multi-local
```

## Key Implementation Details

### Weight Gurus Data Format
- Weights are stored as integers where the last digit represents tenths (e.g., 150.5 lbs is stored as 1505)
- Operations have timestamps in ISO format with Z timezone suffix
- Deleted operations have `operationType: "delete"` and are identified by matching weight and having an earlier timestamp than the deleted operation

### Manual Entry Format
- `operationType`: "create"
- `source`: "manual"
- Weight must be converted to integer format
- Optional fields: `bmi`, `bodyFat`, `muscleMass`, `water` (all as integers)
- `entryTimestamp`: Current timestamp in string format