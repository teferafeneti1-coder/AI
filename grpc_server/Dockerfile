FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY grpc_server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto + generate stubs
COPY proto/ /proto/
RUN pip install --no-cache-dir 'grpcio-tools>=1.64.1' && \
    python /proto/generate.py

# Copy service source
COPY grpc_server/ .

ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]
