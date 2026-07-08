FROM python:3.11-slim

WORKDIR /app

COPY hids_node/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto + generate stubs
COPY proto/ /proto/
RUN pip install --no-cache-dir 'grpcio-tools>=1.64.1' && \
    python /proto/generate.py

COPY hids_node/ .

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
