# Use a lightweight, secure Python base
FROM python:3.11-slim

# Install necessary testing libraries for the Analyzer
RUN pip install --no-cache-dir pytest

# Create a non-root user for extreme execution safety
RUN useradd -m -s /bin/bash agentuser

# Set up the workspace directory (this is where Oubliette mounts the volume)
WORKDIR /home/agentuser/workspace

# Drop root privileges immediately
USER agentuser

# Default command (overridden by our FastAPI app anyway)
CMD ["python"]
