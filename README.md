# Installation and Running Docker Containers

## Prerequisites
- Ensure Docker is installed on your system. You can download it from [Docker's official website](https://www.docker.com/get-started).

## Installation

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

2. **Build and Run Containers with Docker Compose**:
    ```sh
    docker-compose up --build
    ```

3. **Access the Web UI**:
    Open your web browser and navigate to [http://localhost:7680](http://localhost:7680).

To run the containers after the initial setup, use the following command:
```sh
docker-compose up
```
Add the `-d` flag to run the containers in detached mode:
```sh
docker-compose up -d
```


