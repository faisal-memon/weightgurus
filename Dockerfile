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
# Copy cron job file and script
COPY weightgurus-cron /etc/cron.d/weightgurus-cron
COPY run_with_jitter.sh /app/run_with_jitter.sh
RUN chmod 0644 /etc/cron.d/weightgurus-cron
RUN chmod +x /app/run_with_jitter.sh

CMD ["/bin/sh", "-c", "printenv > /etc/environment && cron -f"]
