# Start from the official Ubuntu image
FROM python:latest

# Install necessary packages
RUN apt-get update && \
    apt-get install -y \
        python3-pip

RUN pip3 install \
        numpy  \
        opencv-python-headless  \
        flask

# Create a new user with a specific UID and GID, and set up the workspace
RUN useradd -m -u 1000 -s /bin/bash user && \
    mkdir -p /app && \
    chown -R user:user /app
WORKDIR /app

# Switch to the new non-root user
USER user

# Set the default command to execute when creating a new container
CMD ["bash"]
