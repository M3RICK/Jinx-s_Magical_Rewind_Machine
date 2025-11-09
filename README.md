# RiftRewind: AI-Powered League of Legends Coaching Platform

> Personalized AI coaching with interactive map analysis and persistent conversation memory

**Hackathon:** [Rift Rewind - AWS x Riot Games](https://riftrewind.devpost.com/)
**Live Demo:** [http://riftrewind-production.eba-enkdvi6d.eu-west-3.elasticbeanstalk.com/](http://riftrewind-production.eba-enkdvi6d.eu-west-3.elasticbeanstalk.com/)
**Documentation:** [Coming Soon - MdBook Documentation](#) <!-- TODO: Add deployed mdbook URL -->

## Team

| Member | Role | Responsibilities |
|--------|------|------------------|
| **Thierry B.** | Backend & Cloud Infrastructure Lead | Python/Flask backend, AWS infrastructure (Elastic Beanstalk, DynamoDB, Bedrock), AI integration with Claude Sonnet 4.5, database architecture, CLI testing tools |
| **Aymeric L.** | Riot API Integration & Frontend Lead | Riot Games API integration with Pulsefire, match data processing, interactive map implementation, frontend development (HTML/CSS/JS), coaching session interface |
| **Hugo P.** | Image Generation & DevOps Lead | Player card generation with Pillow, Docker containerization, custom font rendering, Docker Compose setup |

## What is RiftRewind?

RiftRewind is a next-generation League of Legends coaching platform that goes beyond traditional stat-tracking sites. We provide:

- **Interactive Map Analysis:** Explore your gameplay on Summoner's Rift with zone-specific feedback
- **AI Personal Coach:** Chat with Claude Sonnet 4.5 that remembers your progress across sessions
- **Shareable Player Cards:** AI-generated custom cards featuring your playstyle and favorite champions
- **Two Feedback Modes:** Choose between professional coaching or entertaining roasts

Built during the AWS x Riot Games hackathon, RiftRewind transforms match data into actionable insights that help you improve while having fun.

## Tech Stack

### Backend
- **Python 3.12** with Flask web framework
- **AWS Elastic Beanstalk** for deployment and auto-scaling
- **SQLite** for static League data (champions, items, runes)
- **AWS DynamoDB** for dynamic player data and conversations
- **Riot Games API** via Pulsefire library for match data

### AI & Machine Learning
- **Claude Sonnet 4.5** via AWS Bedrock for AI coaching
- **LangChain** for AI application framework and tool calling
- **Tool System** allowing Claude to query game data and player statistics
- **Conversation Memory** storing chat history per player for continuity

### Frontend
- **Vanilla HTML/CSS/JavaScript** for simplicity and performance
- **Canvas API** for interactive Summoner's Rift map
- **Responsive Design** with smooth camera controls

### DevOps
- **Docker** for containerization
- **Docker Compose** for local development
- **Custom Font Integration** (Teko family) for player cards

### Data Processing
- **Pandas** for match statistics aggregation
- **Pillow** for player card image generation
- **aiohttp** for async API calls

## Features

### 1. Ignite the Rewind - Interactive Map
Navigate an interactive Summoner's Rift with clickable zones:
- Click on lanes, jungle, dragon, and baron for specific feedback
- Zone-based performance analysis from your recent matches
- Smooth camera controls and zoom functionality

### 2. AI Coaching with Memory
Chat with your personal AI coach powered by Claude Sonnet 4.5:
- Remembers your previous conversations and progress
- Accesses complete League knowledge (champions, items, builds, counters)
- Can query your match history for personalized advice
- Tool calling system for real-time data retrieval

### 3. Player Cards
Generate and share beautiful custom cards:
- AI-generated titles based on your playstyle
- Personalized descriptions in Coach or Roast mode
- Your most-played champion as background
- Shareable on Discord, Twitter, and other platforms

### 4. Dual Feedback Modes
- **Coach Mode:** Professional, constructive feedback
- **Roast Mode:** Humorous, brutally honest (but still helpful!)

## Quick Start

### Try It Live
Visit [http://riftrewind-production.eba-enkdvi6d.eu-west-3.elasticbeanstalk.com/](http://riftrewind-production.eba-enkdvi6d.eu-west-3.elasticbeanstalk.com/)

Note: Site may be temporarily down. Try again later if unavailable.

### Run Locally

```bash
# Clone the repository
git clone <repository-url>
cd G-PRO-500-TLS-5-1-professionalwork-23

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run with Docker Compose (recommended)
docker-compose up --build

# Or run Flask directly
export FLASK_APP=app/backend/src/main.py
flask run --port=5000
```

### Environment Variables
Create a `.env` file:
```bash
AWS_REGION=eu-west-3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
RIOT_API_KEY=your_riot_key
```

See [Getting Started Documentation](#) for detailed setup instructions.

## Documentation

**Comprehensive documentation is available in our MdBook:**
- [Documentation](https://your-deployed-mdbook-url-here.com) <!-- TODO: Update with actual URL -->

**Quick Links:**
- Architecture Overview
- Tech Stack Details
- Data Management
- AI Integration Guide
- Team & Credits
- Challenges & Learnings

## Acknowledgments

**Special Thanks:**
- **Riot Games** for organizing this hackathon and providing API access
- **Amazon Web Services** for cloud infrastructure and sponsorship
- **Anthropic** for Claude Sonnet 4.5 via AWS Bedrock

**Open Source Libraries:**
- Pulsefire (Riot API wrapper)
- Flask, LangChain, Pillow, Pandas, and many more

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built during a hackathon. From League players, for League players.**

*Last Updated: January 2025*