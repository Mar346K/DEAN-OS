FROM python:3.11-slim
RUN useradd -m agentuser
USER agentuser
WORKDIR /home/agentuser
RUN pip install --no-cache-dir numpy pandas beautifulsoup4
ENTRYPOINT ["python", "-c"]
