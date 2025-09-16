# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache, which reduces the image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# Install Cloud SQL Auth Proxy
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
    && curl -L -o /usr/local/bin/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.13.0/cloud-sql-proxy.linux.amd64 \
    && chmod +x /usr/local/bin/cloud-sql-proxy

# Ensure entrypoint script is executable
RUN chmod +x ./serve.sh

# Default command: run FastAPI with PORT expansion (Railway/Cloud)
CMD ["./serve.sh"]
