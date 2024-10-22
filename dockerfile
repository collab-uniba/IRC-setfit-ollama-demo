# Dockerfile
FROM python:3.12.7-slim

WORKDIR /app

# Install curl and other dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY requirements.txt .
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your Gradio app will run on
EXPOSE 7860

# Command to run the application
CMD ["python", "-m", "ui.app"]
