# Team & Credits

**The Team Behind RiftRewind**

## Development Team


### Thierry B.

**Role:** Backend & Cloud Infrastructure Lead

**Responsibilities:**
- Python/Flask backend architecture and implementation
- Database design and management (SQLite + DynamoDB)
- AWS infrastructure setup and deployment
  - AWS Elastic Beanstalk configuration
  - DynamoDB table design and optimization
  - AWS Bedrock AI integration
- AI integration with Claude Sonnet 4.5
  - Tool system for data requisition from SQLite and DynamoDB
  - System prompt formatting and personality design
  - League of Legends coaching logic and strategy implementation
  - Conversation memory and context management
- API endpoint development
- Session management and authentication
- Backend optimization and caching strategies
- CLI testing tools for individual component testing and manual database operations

**Key Contributions:**
- Designed the dual-database architecture
- Implemented conversation memory system for AI coaching
- Set up AWS Bedrock integration for Claude
- Built the repository pattern for data access
- Deployed and maintained production environment on AWS

**Technologies:** Python, Flask, AWS (Elastic Beanstalk, DynamoDB, Bedrock), SQLite, boto3, LangChain

---

### Aymeric L.

**Role:** Riot API Integration & Frontend Lead

**Responsibilities:**
- Riot Games API integration and data scraping
- Player data fetching and processing pipeline
- Match history and timeline analysis
- Frontend development and UI/UX
- Interactive map implementation
  - Zone-based feedback system
  - Camera controls and smooth navigation
  - Map animations and interactions
- AI Coaching session interface
- Frontend-backend integration

**Key Contributions:**
- Built the `API/` module for Riot API access using Pulsefire
- Designed the Player model for data aggregation
- Created zone analyzer for map-based performance breakdown
- Developed the interactive Summoner's Rift map with clickable zones
- Implemented smooth camera movement and zoom controls
- Built the coaching chat interface with match history sidebar

**Technologies:** Python (Pulsefire, aiohttp), HTML5, CSS3, JavaScript (ES6+), Canvas API, Riot Games API

---

### Hugo P.

**Role:** Image Generation & DevOps Lead

**Responsibilities:**
- Player card generation system
  - Custom card design and layout
  - Champion art integration
  - Text rendering with custom fonts
  - Base64 encoding for web delivery
- Docker containerization
  - Dockerfile creation and optimization
  - Font installation and system dependencies
- Docker Compose setup for local development
- Image processing pipeline

**Key Contributions:**
- Designed and implemented the player card generation system using Pillow
- Set up custom font rendering (Teko font family)
- Created Docker container with all necessary dependencies
- Configured Docker Compose for easy local testing
- Optimized image generation for performance
- Implemented card caching system

**Technologies:** Python (Pillow), Docker, Docker Compose, Font rendering (freetype), Image processing

---

## Project Structure

The team collaborated on a well-organized codebase:

```
├── API/              # Aymeric - Riot API integration
├── app/
│   ├── backend/      # Thierry - Flask server and AI
│   └── frontend/     # Aymeric - HTML/CSS/JS
├── db/               # Thierry - Database layer
├── Dockerfile        # Hugo - Containerization
├── docker-compose.yml # Hugo - Local dev environment
└── requirements.txt  # Team - Shared dependencies
```

## Technologies Used

**Team-Wide:**
- Python 3.12 (primary language)
- Docker (containerization)
- Git/GitHub (version control)
- AWS (cloud infrastructure)
- Riot Games API (game data)

**Specialized:**
- Thierry: Flask, DynamoDB, Bedrock, LangChain
- Aymeric: Pulsefire, aiohttp, Vanilla JS, Canvas
- Hugo: Pillow, Docker, freetype, fontconfig

---

**Built during a hackathon. From League players, for League players.**

## Special Thanks

**Riot Games:**
We extend our deepest gratitude to Riot Games for organizing this incredible hackathon and providing us with the opportunity to build tools for the League of Legends community. Access to the Riot Games API and Data Dragon enabled us to create a truly data-driven coaching platform. Thank you for fostering innovation and supporting developers who want to enhance the player experience.

**Amazon Web Services (AWS):**
Special thanks to Amazon Web Services for sponsoring this hackathon and providing the cloud infrastructure that powers RiftRewind. AWS Elastic Beanstalk, DynamoDB, and Bedrock (Claude AI) were essential to bringing our vision to life. The accessibility of these services allowed us to focus on building features rather than managing infrastructure. Thank you for empowering developers with world-class tools.
