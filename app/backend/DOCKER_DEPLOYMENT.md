# Docker Deployment Guide for Rift Rewind

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t rift-rewind .
```

### 2. Run Locally with Docker

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your actual API keys and credentials
nano .env

# Run the container
docker run -p 5000:5000 --env-file .env rift-rewind
```

### 3. Test with Docker Compose (Recommended)

```bash
# Start the application
docker-compose up

# Stop the application
docker-compose down
```

Access the app at: http://localhost:5000

---

## Elastic Beanstalk Deployment

### Prerequisites
- AWS CLI installed (`aws configure`)
- EB CLI installed (`pip install awsebcli`)

### Deploy Steps

1. **Initialize Elastic Beanstalk** (first time only):
   ```bash
   eb init -p docker rift-rewind --region us-east-1
   ```

2. **Create environment** (first time only):
   ```bash
   eb create rift-rewind-prod
   ```

3. **Set environment variables** in EB:
   ```bash
   eb setenv \
     RIOT_API_KEY=your-key \
     AWS_REGION=us-east-1 \
     USE_MOCK_DB=false \
     USE_MOCK_AI=false \
     ALLOWED_ORIGINS=https://your-app.elasticbeanstalk.com
   ```

4. **Deploy**:
   ```bash
   eb deploy
   ```

5. **Open your app**:
   ```bash
   eb open
   ```

### Useful EB Commands

```bash
# Check status
eb status

# View logs
eb logs

# SSH into instance
eb ssh

# Terminate environment (careful!)
eb terminate
```

---

## Project Structure (After Reorganization)

```
hackathon_rift-rewind/
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Local testing with Docker
├── .dockerignore             # Files to exclude from Docker
├── requirements.txt          # Python dependencies
├── API/                      # Riot API client & analytics
├── db/                       # Database layer
├── app/
│   ├── backend/
│   │   └── src/
│   │       └── main.py       # Flask server (API + static files)
│   └── frontend/
│       └── public/           # All static files (HTML, CSS, JS, assets)
│           ├── index.html
│           ├── interactive_map.html
│           ├── coaching_session.html
│           ├── js/
│           ├── assets/
│           └── favicon.ico
└── testing/                  # Test utilities & mocks
```

---

## Troubleshooting

### Issue: Container won't start
```bash
# Check logs
docker logs <container-id>

# Run interactively to debug
docker run -it --env-file .env rift-rewind /bin/bash
```

### Issue: Can't connect to AWS
- Verify AWS credentials in `.env`
- Check AWS IAM permissions (DynamoDB, Bedrock)
- Verify security groups allow outbound HTTPS

### Issue: Health check failing
```bash
# Test health endpoint
curl http://localhost:5000/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "dynamodb",
  "ai": "bedrock"
}
```

---

## Development Mode (Zero AWS Costs)

For frontend development without AWS costs:

```bash
# Set in .env
USE_MOCK_DB=true
USE_MOCK_AI=true

# Then run
docker-compose up
```

This uses in-memory mock data and mock AI responses.

