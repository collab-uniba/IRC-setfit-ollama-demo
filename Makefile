.PHONY: venv activate install run dev docker-build docker-run docker-compose-up docker-compose-down

venv:
	python3 -m venv venv

activate: venv
	. venv/bin/activate

install: activate
	pip install -r requirements.txt

# Local development with manual Ollama setup
setup-ollama:
	curl -fsSL https://ollama.com/install.sh | sh
	ollama serve > /dev/null 2>&1 &

run: install setup-ollama
	python -m ui.app

dev:
	python -m ui.app

# Docker commands
docker-build:
	docker build -t github-issue-classifier .

docker-run: docker-build
	docker run -p 7860:7860 github-issue-classifier

# Docker Compose commands
docker-compose-up:
	docker-compose up --build -d

docker-compose-down:
	docker-compose down

# Clean up
clean:
	docker-compose down -v
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -r {} +