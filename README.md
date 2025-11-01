# Rift Rewind: League of Legends AI Coach

> An AI-powered personalized insights agent for League of Legends players

**Hackathon:** [Rift Rewind - AWS x Riot Games](https://riftrewind.devpost.com/)  

## Team

| Member | Role | Responsibilities |
|--------|------|------------------|
| **ThierryB** | AWS & Backend Lead | Database architecture, DynamoDB design & optimization, AWS Bedrock integration, backend development |
| **AymericL** | API Integration | Riot Games API integration, data pipeline management |
| **HugoP** | Frontend Lead | Frontend development, UI/UX design, user interface implementation |

## Project Overview

We're building an intelligent agent that transforms raw League of Legends match data into personalized, actionable insights. Our goal is to help players reflect on their gameplay, identify growth opportunities, and celebrate their achievements through AI-powered analysis.

## Tech Stack

### Backend
- **Language:** Python
  - Chosen for its boto3 library that is maintained by AWS themselves
  - Already used by each member of this team on multiple projects

- **Database:** AWS DynamoDB
  - Chosen for its scalability and seamless AWS ecosystem integration
  - Excellent Python support via boto3
  - NoSQL flexibility perfect for varying match data structures
  - Future-proof solution as the project scales

### AI/ML
- **AI Model:** Claude Sonnet 4.5 via Amazon Bedrock
  - Provides intelligent League of Legends coaching and customer service
  - Delivers personalized gameplay analysis and improvement recommendations
  - Integrates seamlessly with AWS infrastructure for scalable AI-powered insights

- **Under Evaluation:** Lightweight AI classifier
  - Fast pre-processing to determine if user queries require RAG/additional data
  - Returns simple "yes"/"no" responses for optimized routing
  - Enables faster responses for basic queries while preserving Claude for complex analysis

- **Under Evaluation:** Content moderation AI
  - Real-time monitoring of user input for toxic/violent content detection
  - Ensures safe and positive community interactions
  - Automatic filtering and escalation for inappropriate content

### APIs
- Riot Games League of Legends API for match history and player data

## Project Goals

Our agent aims to provide:
- **Long-term Performance Analysis:** Identify persistent strengths and weaknesses
- **Progress Visualization:** Track improvement over time
- **Personalized Insights:** Generate meaningful, actionable recommendations
- **Social Features:** Enable comparisons and shareable moments
- **End-of-Year Recaps:** Create engaging summaries of player achievements

## License

This project is open source under the [MIT License](https://opensource.org/licenses/MIT).

---

**Note:** This README will be updated regularly as the project progresses. Check back for the latest developments!

*Last Updated: October 2025*