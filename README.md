# RAGchatbot

![Build Status](https://github.com/Nimadli/Chatbot/actions/workflows/ci-build.yaml/badge.svg)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![3.13](https://img.shields.io/badge/Python-3.13-green.svg)](https://shields.io/)

---

### IP for testing: http://13.222.78.238:8501/

## Architecture

- **Backend**: FastAPI for ML model serving and API endpoints
- **Frontend**: Streamlit for interactive web interface
- **Containerization**: Docker and Docker Compose for service orchestration
- **CI/CD**: GitHub Actions with self-hosted runner deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Running the Application

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nimadli/Chatbot.git
   cd Chatbot
   ```

2. **Create a .env file inside the root folder**
    - Fill .env with the secret key and key ID

3. **Launch services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend (Streamlit): `http://localhost:8501`
   - Backend API (FastAPI): `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

5. **Stop the application**
   ```bash
   docker-compose down
   ```

## Project Structure

```
MLOps_example/
├── backend/              # FastAPI application
├── frontend/             # Streamlit application
├── docker-compose.yml    # Service orchestration
├── .github/workflows/    # CI/CD pipelines
└── README.md
```

## Development Setup

### For Server Deployment (Ubuntu)

1. **Add user to docker group** (to run docker commands without sudo)
   ```bash
   sudo usermod -aG docker ubuntu
   ```

2. **Create ACCESS_KEYS**
    - Go to AWS and sign in, then access IAM from the search bar
    - Create a new access key and choose the "for external usage" option
    - Copy the keys into a local file (do not share them)

2. **Create a GitHub repository secret**
    - Go to the repository > Settings > Secrets and Variables > Actions
    - Create a repository secret, name it AWS_ACCESS_KEY_ID and write the key from IAM inside it
    - Create another repository secret, name it AWS_SECRET_ACCESS_KEY and write the second key inside it
    - Create the final secret, name it AWS_DEFAULT_REGION and write us-east-1

3. **Create GitHub self-hosted runner**
   - Go to your repository **Settings** → **Actions** → **Runners**
   - Click **"New self-hosted runner"** and select **Linux**
   - Follow all the setup steps provided by GitHub **except the last step**
   - Don't run `./run.sh` directly as shown in GitHub instructions

4. **Launch GitHub runner in detached mode**
   ```bash
   nohup ./run.sh > runner.log 2>&1 &
   ```

## Key Features

- **Dockerized Services**: Both backend and frontend are containerized for consistent deployment
- **Service Communication**: Demonstrates proper inter-service communication patterns
- **CI/CD Pipeline**: Automated testing and deployment using GitHub Actions
- **Self-hosted Runner**: Shows how to set up and use self-hosted runners for deployment
- **Learning Playground**: Intended for exploring and practicing MLOps concepts

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://opensource.org/licenses/Apache-2.0) file for details.