# Vi's Direct Coaching

**Your Personal AI League Coach with Memory**

## Overview

Vi's Direct Coaching is an AI-powered chat interface that provides personalized League of Legends coaching. Unlike generic chatbots, Vi has access to comprehensive game knowledge, your personal match data, and most importantly, memory of your previous conversations.

## Key Features

### 1. Comprehensive League Knowledge

Our AI has access to complete, up-to-date information about:

- **All Champions** - Abilities, matchups, power spikes, combos
- **Items** - Stats, build paths, situational choices
- **Runes** - Optimal setups for different champions and matchups

This data is stored in a local SQLite database that updates bi-weekly to stay current with patches.

### 2. Your Personal Match Data

While you chat, our AI displays your recent match history on the left sidebar, showing:

- Last few games played
- Performance metrics
- Champions used

This data is pulled from DynamoDB in real-time, giving our AI context about your actual gameplay.

### 3. Persistent Memory

This is what makes our AI truly special. The AI has access to your previous coaching sessions, allowing it to:

- **Remember past advice** - Won't repeat what it already told you
- **Track your progress** - Can reference improvements or ongoing struggles
- **Build a relationship** - Becomes more personalized over time
- **Continue conversations** - Pick up where you left off, even days later

This persistent memory is powered by conversation history stored and retrieved for each unique player.

### 4. Powered by Claude Sonnet 4.5

Our AI uses Anthropic's Claude Sonnet 4.5, one of the most advanced AI models available, ensuring:

- Natural, conversational responses
- Deep understanding of complex questions
- Nuanced advice that considers multiple factors
- Ability to explain concepts at different skill levels

## How to Use Our AI

### Starting a Session

1. Complete the initial setup (summoner name, region, mode selection)
2. Navigate to "Vi's Direct Coaching"
3. Your recent match data loads automatically
4. Start chatting

### Example Questions

Our AI can help with virtually anything League-related:

**Champion-Specific:**
- "How do I lane against Darius as Garen?"
- "What's the optimal combo for Zed?"
- "When should I roam as Twisted Fate?"

**Strategy:**
- "How do I improve my CS?"
- "When should we prioritize Drake vs Baron?"
- "How do I play from behind?"

**Personal Performance:**
- "Why do I keep losing on Yasuo?" (Our AI will check your match history)
- "What should I focus on improving next?"
- "Am I building the right items?"

**Meta Questions:**
- "What are the best supports this patch?"
- "Is lethality or crit better on Varus right now?"

### Ongoing Coaching

The real power comes from continued use:

- Come back after implementing advice and report results
- Ask follow-up questions days later
- Get accountability and progress tracking
- Build a personalized improvement plan over time

## Technical Architecture

Our AI's coaching system integrates multiple data sources:

```
User Question
    ↓
Claude Sonnet 4.5 (with conversation history)
    ↓
Queries: (we use tools due to the time constrain, objective was a RAG)
- SQLite (Static game data)
- DynamoDB (Player match data)
- Conversation history (Previous sessions)
    ↓
Contextualized, Personalized Response
```

## Data Management

### Static Data (SQLite)
- Champions, items, runes, abilities
- Updates every 2 weeks with new patches
- Ensures accuracy with current game state

### Dynamic Data (DynamoDB)
- Player match history
- Performance statistics
- Real-time updates after each game
- Conversation history per unique player

## What Makes It Different

Most AI coaching tools either:
- Have no memory (every conversation starts fresh)
- Have no access to your data (generic advice only)
- Have outdated game knowledge

Our AI combines all three: memory, your data, and current game knowledge, creating a truly personalized coaching experience that improves over time.

## Future Enhancements

Potential improvements being considered:

- RAG implementation
- Much better security
- Deeper statistical match access (Premium Feature)