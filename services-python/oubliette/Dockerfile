# Use a slim, secure Python base
FROM python:3.11-slim

# Create a non-privileged user (Zero-Trust Rule: No Root)
RUN useradd -m agentuser
USER agentuser
WORKDIR /home/agentuser

# Pre-install basic data science tools for agent tasks
RUN pip install --no-cache-dir numpy pandas

# The entrypoint is Python, waiting for code as a string
ENTRYPOINT ["python", "-c"]
