#!/bin/bash

# Get the absolute path to the directory containing this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Build the Docker image
docker build -t mechart:latest "${SCRIPT_DIR}"

# Start the Docker container
docker run -it \
    --rm \
    --net host \
    -v "/${SCRIPT_DIR}:/app" \
    mechart:latest \
    bash