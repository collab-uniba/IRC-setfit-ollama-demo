FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the rest of the application code
COPY . .

# Run model pull script
RUN chmod +x models/pull_models.py && \
    ./models/pull_models.py

EXPOSE 7860

CMD ["python", "-m", "ui.app"]
