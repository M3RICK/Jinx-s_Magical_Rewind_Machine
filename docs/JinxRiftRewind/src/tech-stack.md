# Tech Stack

**Technologies and Libraries Powering RiftRewind**

## Overview

RiftRewind is built using a modern Python backend with vanilla JavaScript frontend, leveraging AWS services for scalability and AI capabilities.

## Backend Technologies

### Core Framework

**Flask 3.1.2**
- Lightweight Python web framework
- RESTful API endpoints
- Static file serving
- CORS support via flask-cors 6.0.1

**Python 3.12**
- Latest stable Python release
- Native async/await support
- Type hints and modern syntax
- Performance improvements over 3.10+

### League of Legends API Integration

**Pulsefire**
- Python wrapper for Riot Games API
- Async/await support with aiohttp
- Rate limiting built-in
- Type-safe champion, match, and summoner data

**aiohttp**
- Async HTTP client/server framework
- Used by Pulsefire for concurrent API calls
- Significantly faster than synchronous requests

### AI and Machine Learning

**AWS Bedrock**
- Managed AI service for Claude Sonnet 4.5
- Serverless inference
- Pay-per-use pricing
- No model hosting required

**LangChain + LangChain-AWS**
- AI application framework
- Tool calling abstraction
- Message history management
- Streaming support

**Claude Sonnet 4.5 (via Bedrock)**
- Advanced language model by Anthropic
- Function/tool calling capabilities
- Long context window
- Natural conversation flow

### Database Technologies

**SQLite 3**
- Embedded database for static League data
- Zero configuration
- Fast local queries
- File-based storage (league_data.db)
- Tables: champions, items, runes, builds, counters

**AWS DynamoDB**
- NoSQL database for player data
- Serverless and auto-scaling
- Low latency queries
- Global/Local secondary indexes
- Tables: Players, MatchHistory, Conversations, Sessions, MapStories, PlayerTitles

**Boto3 1.40.53**
- AWS SDK for Python
- DynamoDB operations
- Bedrock API access
- S3 integration (future)

### Data Processing

**Pandas 2.3.3**
- Data analysis and manipulation
- Match statistics aggregation
- Time series analysis for trends
- DataFrame operations for performance metrics

**NumPy**
- Numerical computing
- Array operations
- Statistical calculations
- Performance optimizations

### Image Generation

**Pillow (PIL)**
- Python Imaging Library
- Player card generation
- Text rendering with custom fonts (Teko)
- Image composition and overlays
- Base64 encoding for web delivery

### Utilities and Supporting Libraries

**python-dotenv 1.2.1**
- Environment variable management
- .env file loading
- Configuration separation

**requests 2.32.5**
- HTTP library for external APIs
- Synchronous requests when needed
- Simple API for REST calls

**python-dateutil 2.9.0**
- Date/time parsing and manipulation
- Timezone handling
- Relative date calculations

## Frontend Technologies

### Core Web Technologies

**HTML5**
- Semantic markup
- Modern form elements
- Canvas API for map rendering

**CSS3**
- Flexbox and Grid layouts
- Custom animations
- Responsive design
- Dark theme styling

**Vanilla JavaScript (ES6+)**
- No framework dependencies
- Async/await for API calls
- Fetch API for HTTP requests
- LocalStorage for session management
- DOM manipulation

### Frontend Pages

- **index.html** - Landing page with authentication
- **interactive_map.html** - Summoner's Rift interactive map
- **coaching_session.html** - AI chat interface

## DevOps and Deployment

### Containerization

**Docker**
- Single Dockerfile for entire application
- Python 3.12-slim base image
- Multi-stage build process
- Custom font installation (Teko family)
- Health check configuration

**Docker Compose**
- Local development environment
- Environment variable management
- Port mapping (80:5000)
- Mock database options

### Cloud Infrastructure

**AWS Elastic Beanstalk**
- Platform as a Service (PaaS)
- Docker single-container platform
- Auto-scaling and load balancing
- Health monitoring
- Environment variable management
- Rolling deployments

**AWS Services Used:**
- **DynamoDB** - NoSQL database
- **Bedrock** - AI model inference
- **Elastic Beanstalk** - Application hosting
- **Route 53** - DNS (planned)
- **CloudFront** - CDN (planned)

### Version Control

**Git**
- Source code management
- GitHub repository
- Branch-based workflow
- Pull request reviews

## External APIs

### Riot Games API

**Endpoints Used:**
- **Summoner-V4** - Player lookup by Riot ID
- **Match-V5** - Match history and details
- **League-V4** - Ranked information
- **Champion-Mastery-V4** - Champion statistics

**Authentication:**
- API key via environment variable
- Rate limiting: 20 requests/second, 100 requests/2 minutes

### Data Dragon (Riot Static Data)

**Purpose:**
- Champion images and icons
- Item assets
- Spell and ability data
- Patch version tracking

**Update Frequency:**
- Every 2 weeks (patch cycle)
- Automated sync to SQLite database

## Development Tools

### Python Package Management

**pip**
- Package installation
- requirements.txt for dependencies
- Virtual environment (venv) support

### System Dependencies

**gcc** - C compiler for Python packages
**curl** - HTTP client for health checks
**fontconfig** - Font management system
**libfreetype6** - Font rendering library
**libjpeg-dev** - JPEG image support
**zlib1g-dev** - Compression library

## Security Libraries

**botocore**
- AWS request signing
- Credential management
- Error handling

**certifi 2025.10.5**
- SSL certificate verification
- HTTPS security

**urllib3 2.5.0**
- HTTP client with security features
- Connection pooling
- Retry logic

## Performance Considerations

### Async Operations

- Pulsefire uses aiohttp for concurrent Riot API calls
- Flask wraps async calls with asyncio event loop
- Multiple matches fetched in parallel

### Caching

- DynamoDB stores computed zone stories (24h TTL)
- Match history cached per player
- Static League data in SQLite (no network calls)

### Database Optimization

- DynamoDB secondary indexes for fast lookups
- SQLite primary keys and indexed queries
- Connection pooling where applicable

## Why These Technologies?

### Python/Flask Choice

- **Rapid Development** - Quick API implementation
- **Strong Ecosystem** - Excellent libraries for data processing
- **AWS Integration** - Native boto3 support
- **Async Support** - Handles concurrent Riot API calls efficiently

### Vanilla JS Choice

- **No Build Step** - Faster development iteration
- **Simplicity** - Easy to understand and maintain
- **Performance** - No framework overhead
- **Flexibility** - Direct DOM manipulation when needed

### AWS Choice

- **Scalability** - DynamoDB auto-scales, Elastic Beanstalk handles load
- **Cost Efficiency** - Pay only for usage
- **Managed Services** - Less infrastructure management
- **AI Access** - Bedrock provides Claude without self-hosting

### SQLite + DynamoDB Choice

- **Best of Both Worlds** - Local static data + cloud dynamic data
- **Performance** - SQLite is extremely fast for reads
- **Cost** - SQLite is free, DynamoDB charges per request
- **Flexibility** - Easy to update League data without cloud costs

## Future Technology Considerations

**Potential Additions:**
- **Redis** - Session caching and rate limiting
- **React/Vue** - More dynamic frontend
- **WebSockets** - Real-time AI streaming
- **PostgreSQL** - More complex relational queries
- **Kubernetes** - Advanced container orchestration
- **CDN** - CloudFront for asset delivery
- **Monitoring** - CloudWatch, Datadog, or New Relic
