FROM python:3.11-slim

WORKDIR /app

# Install Node for building the React login UI
RUN apt-get update && apt-get install -y nodejs npm --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY agent_node/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Proto stubs
COPY proto/ /proto/
RUN pip install --no-cache-dir 'grpcio-tools>=1.64.1' && \
    python /proto/generate.py

# Build React login UI
COPY agent_node/login_ui/ ./login_ui/
RUN cd login_ui && npm install --silent && npm run build

# Copy agent source
COPY agent_node/ .

EXPOSE 50052 8080
ENV PYTHONUNBUFFERED=1

# Start both the gRPC agent and the login API
CMD ["sh", "-c", "python agent.py & python login_api.py"]
