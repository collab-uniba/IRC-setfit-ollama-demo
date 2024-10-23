FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . .

# Install Python dependencies and run model pull script
RUN pip install --no-cache-dir -r requirements.txt 
RUN chmod +x models/pull_models.py && \
    ./models/pull_models.py

EXPOSE 7860

CMD ["python", "-m", "ui.app"]