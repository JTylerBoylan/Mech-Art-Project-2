#!/bin/bash
xhost +local:docker

# Get the absolute path to the directory containing this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Build the Docker image
docker build -t mechart:latest "${SCRIPT_DIR}"

# Start the Docker container with access to the host's display server
docker run -it \
    --rm \
    --net host \
    -e DISPLAY=$DISPLAY \
    -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    -v "/${SCRIPT_DIR}:/app" \
    mechart:latest \
    bash
