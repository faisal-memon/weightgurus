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
COPY run_with_jitter.sh /app/run_with_jitter.sh
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/run_with_jitter.sh
RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
