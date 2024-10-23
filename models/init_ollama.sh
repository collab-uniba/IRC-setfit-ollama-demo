#!/bin/bash

# Function to wait for Ollama to be ready
wait_for_ollama() {
    echo "Waiting for Ollama service to be ready..."
    until curl -s "http://localhost:11434/api/version" > /dev/null; do
        sleep 1
    done
    echo "Ollama service is ready"
}

# Function to pull a model
pull_model() {
    local model=$1
    echo "Pulling model: $model"
    ollama pull "$model"
    return $?
}

# Main script
wait_for_ollama

# Read default model from config
DEFAULT_MODEL=$(yq e '.ollama_models[] | select(.default == true) | .path' /models_config.yaml)

if [ -n "$DEFAULT_MODEL" ]; then
    echo "Pulling default Ollama model: $DEFAULT_MODEL"
    if pull_model "$DEFAULT_MODEL"; then
        echo "✓ Successfully pulled default model: $DEFAULT_MODEL"
        exit 0
    else
        echo "✗ Failed to pull default model: $DEFAULT_MODEL"
        exit 1
    fi
else
    echo "No default Ollama model specified in config"
    exit 1
fi