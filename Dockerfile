# Dockerfile for Weight Gurus API client
# Use an official lightweight Python runtime
FROM python:3.11-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy dependency file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py ./
COPY weightgurus-cron /defaults/weightgurus-cron.tmpl
COPY scripts/run_with_jitter.sh /app/scripts/run_with_jitter.sh
COPY scripts/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh
RUN chmod +x /app/scripts/run_with_jitter.sh
RUN chmod +x /app/scripts/docker-entrypoint.sh

CMD ["/app/scripts/docker-entrypoint.sh"]
