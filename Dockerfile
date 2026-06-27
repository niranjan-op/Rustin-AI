FROM python:3.11-slim

# Install bash, curl, git, and other common utilities
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /workspace

# Keep container running in the background
CMD ["tail", "-f", "/dev/null"]
