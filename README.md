# Installation and Running Docker Containers

## Prerequisites
- Ensure Docker is installed on your system. You can download it from [Docker's official website](https://www.docker.com/get-started).

## Installation

If you want to run the application in a Docker container, follow the instructions below.

1. **Install Docker**:
    - For Windows and macOS, download and run the Docker Desktop installer.
    - For Linux, use the package manager to install Docker. For example, on Ubuntu:
      ```sh
      sudo apt-get update
      sudo apt-get install -y docker.io
      ```

2. **Verify Docker Installation**:
    ```sh
    docker --version
    ```

## Running the Application

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/collab-uniba/IRC-setfit-ollama-demo.git
    cd IRC-setfit-ollama-demo
    ```

2. **Set Up Environment Variables**:
    Before running the application, you need to create the `.env` file with the required port configurations. The easiest way to do this is using the Makefile:
    ```sh
    make setup-env
    ```
    This will create a `.env` file with default values:
    - UI_PORT: 7860
    - SETFIT_PORT: 8000
    - OLLAMA_PORT: 11434
    
    You can edit the `.env` file to customize these ports if needed.

3. **Build and Run Containers with Docker Compose**:
    
    **Option A: Using Docker Compose directly**
    ```sh
    docker-compose up --build
    ```
    
    **Option B: Using the Makefile (recommended)**
    ```sh
    make docker-compose-up
    ```
    The Makefile will automatically set up the environment if needed and start the containers in detached mode.

4. **Access the Web UI**:
    Open your web browser and navigate to [http://localhost:7860](http://localhost:7860) (or the port you configured in `.env`).

To run the containers after the initial setup, use the following command:
```sh
docker-compose up
```
Add the `-d` flag to run the containers in detached mode:
```sh
docker-compose up -d
```

To stop the containers:
```sh
docker-compose down
```
Or using the Makefile:
```sh
make docker-compose-down
```

## Additional Makefile Commands

The project includes a Makefile with helpful commands for managing the application. To see all available commands:
```sh
make help
```

Some useful commands include:
- `make setup-env` - Create `.env` file with default port configurations
- `make docker-compose-up` - Build and start all services with Docker Compose
- `make docker-compose-down` - Stop all running services
- `make clean` - Remove all generated files and Docker resources


