# GitHub Issue Classification System

A comprehensive system for classifying GitHub issues using SetFit and Ollama models, featuring a web-based UI for scraping and classifying issues.

## Project Structure

```
IRC-setfit-ollama-demo/
├── src/
│   └── irc_setfit_ollama_demo/     # Installable Python package
│       ├── common/                  # Common data models (Issue class)
│       ├── config/                  # Configuration managers
│       ├── models/                  # Model interfaces (Ollama, SetFit)
│       └── scraping/                # GitHub scraping utilities
├── services/                        # Service entrypoints (thin wrappers)
│   ├── ollama/                      # Ollama initialization
│   ├── setfit_inference/            # SetFit API service
│   └── ui/                          # Gradio web UI
├── scripts/                         # Utility scripts
│   └── pull_models.py              # Script to download models
├── tests/                           # Test directory
├── data/                            # Training and test data
├── config/                          # Configuration files
│   └── models_config.yaml          # Model configurations
├── dockerfiles/                     # Docker build files
├── pyproject.toml                   # Python package configuration
├── Makefile                         # Build and run automation
├── docker-compose.yaml             # Multi-service orchestration
└── README.md
```

## Prerequisites

- Python 3.12 or higher
- Docker (for containerized deployment)
- Ollama (optional, for local Ollama model usage)

## Installation

### Option 1: Local Development Setup

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/collab-uniba/IRC-setfit-ollama-demo.git
   cd IRC-setfit-ollama-demo
   ```

2. **Create Virtual Environment and Install Package**:
   ```sh
   make venv
   source venv/bin/activate
   make install
   ```
   
   Or manually:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

3. **Set Up Environment Variables** (optional):
   ```sh
   make setup-env
   ```
   
   This creates a `.env` file with default port configurations. You can edit it to customize:
   - UI_PORT: 7860
   - SETFIT_PORT: 8000
   - OLLAMA_PORT: 11434

4. **Install and Start Ollama** (for Ollama model support):
   ```sh
   make setup-ollama
   ```

5. **Run Services Locally**:
   
   Run all services:
   ```sh
   make run-all
   ```
   
   Or run services individually:
   ```sh
   make run-setfit  # Start SetFit API service
   make run-ui      # Start UI service
   ```

6. **Access the Web UI**:
   Open your browser and navigate to [http://localhost:7860](http://localhost:7860)

### Option 2: Docker Deployment

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/collab-uniba/IRC-setfit-ollama-demo.git
   cd IRC-setfit-ollama-demo
   ```

2. **Set Up Environment Variables**:
   ```sh
   make setup-env
   ```
   
   Edit `.env` if you need to customize ports.

3. **Build and Run with Docker Compose**:
   ```sh
   make docker-compose-up
   ```
   
   Or directly:
   ```sh
   docker-compose up --build -d
   ```

4. **Access the Web UI**:
   Open your browser and navigate to [http://localhost:7860](http://localhost:7860) (or your configured port)

5. **Stop Services**:
   ```sh
   make docker-compose-down
   ```

## Features

- **GitHub Issue Scraping**: Scrape issues from GitHub repositories or fetch individual issues
- **Multi-Model Classification**: Support for both SetFit and Ollama models
- **Configurable Labels**: Dynamic label management through the UI
- **Web Interface**: User-friendly Gradio-based interface
- **API Access**: RESTful API for SetFit classification
- **Docker Support**: Easy deployment with Docker Compose

## Development

### Package Structure

The codebase is organized as an installable Python package:

- **src/irc_setfit_ollama_demo/**: Main package containing all reusable code
  - **common/**: Shared data models (Issue class)
  - **config/**: Configuration management (labels, models)
  - **models/**: Model interfaces and utilities
  - **scraping/**: GitHub scraping functionality

- **services/**: Thin entrypoint wrappers that import from the main package
  - Each service only contains deployment-specific code (app.py, configs)
  - Business logic is imported from `src/irc_setfit_ollama_demo/`

### Adding New Features

When adding new features:
1. Add shared/reusable code to `src/irc_setfit_ollama_demo/`
2. Keep service entrypoints thin - they should only handle deployment concerns
3. Import and use functionality from the main package

### Running Tests

```sh
# Install with dev dependencies
make install-dev

# Run tests (when available)
pytest tests/
```

## Makefile Commands

The project includes a comprehensive Makefile for common tasks:

```sh
make help                  # Show all available commands
make venv                  # Create virtual environment
make install               # Install the package
make install-dev           # Install with dev dependencies
make setup-env             # Create .env file
make setup-ollama          # Install and start Ollama
make run-ui                # Run UI service locally
make run-setfit            # Run SetFit service locally
make run-all               # Run all services locally
make docker-compose-up     # Start Docker services
make docker-compose-down   # Stop Docker services
make clean                 # Clean up generated files and Docker resources
```

## Configuration

### Model Configuration

Models are configured in `config/models_config.yaml`:

```yaml
setfit_models:
  - name: "CFS Model"
    path: "collab-uniba/bert-finetuned-cfs"
    default: true
  - name: "F-Prime Model"
    path: "collab-uniba/setfit-fprime-binary-model"
    default: false

ollama_models:
  - name: "Llama 3.2"
    path: "llama3.2"
    default: true
```

### Label Configuration

Labels are managed through the UI or by editing `services/ui/labels_config.yaml`:

```yaml
labels:
  - name: "bug"
    description: "The 'bug' label identifies issue reports describing problems or errors."
  - name: "non-bug"
    description: "The 'non-bug' label is applied to any issue that is not a bug."
```

## API Documentation

The SetFit service provides a REST API:

- **POST /classify**: Classify issues
  ```json
  {
    "issues": [
      {
        "title": "Issue title",
        "body": "Issue description"
      }
    ],
    "model_name": "collab-uniba/bert-finetuned-cfs"
  }
  ```

- **GET /models**: Get available models and current model status

## Troubleshooting

### Port Already in Use
If you get a "port already in use" error, either:
1. Stop the conflicting service
2. Edit `.env` to use different ports
3. Set environment variables before running: `UI_PORT=8080 make run-ui`

### Module Not Found Errors
If you encounter import errors:
1. Ensure you've activated the virtual environment: `source venv/bin/activate`
2. Reinstall the package: `make install`
3. For Docker, rebuild images: `make docker-compose-up`

### Ollama Connection Issues
Ensure Ollama is running:
```sh
make setup-ollama
```

Or start it manually:
```sh
ollama serve
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:
1. Code follows the package structure guidelines
2. Shared logic goes in `src/irc_setfit_ollama_demo/`
3. Service entrypoints remain thin wrappers
4. Tests are added for new features (when applicable)

## Acknowledgments

- Built with [SetFit](https://github.com/huggingface/setfit)
- UI powered by [Gradio](https://gradio.app/)
- LLM support via [Ollama](https://ollama.ai/)
