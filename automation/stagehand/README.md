## Stagehand AI Chat Automation

Multiple automation scripts for testing real-time chat with AI-driven personas.

---

## 1. Multi-Session Chat (Orchestrated)
**File:** `multi-session-chat.js`

Two AI personas (Alice and Bob) have a controlled 10-turn conversation in separate browser windows.

### Run
```bash
npm start
```

**Features:**
- Opens two Chrome windows simultaneously
- Alice starts, then alternates turns
- 10 total messages with full conversation log
- Each persona maintains independent conversation history

---

## 2. Independent Agents (Autonomous)
**Files:** `alice-agent.js`, `bob-agent.js`

Two independent, long-running agents that continuously monitor and respond to each other.

### Run (in separate terminals)

**Terminal 1 - Alice:**
```bash
npm run alice
```

**Terminal 2 - Bob:**
```bash
npm run bob
```

**Features:**
- **Alice:** Proactive - starts conversations if chat is empty, responds to Bob
- **Bob:** Reactive - waits for Alice's messages and responds
- Infinite loop - conversations continue indefinitely
- Each monitors for new messages every 3 seconds
- Natural pacing with thinking delays
- Independent browser windows

**Use Cases:**
- Long-running chat stress testing
- Real-time message synchronization validation
- WebSocket connection stability testing
- Continuous conversation flows

---

## Setup

### Environment Variables (`.env`)
```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
APP_BASE_URL=http://localhost:3000
CHAT_ID=demo
STAGEHAND_MODEL=openai/gpt-4o-mini
CHAT_MODEL=gpt-4o-mini
```

### Install Dependencies
```bash
cd automation/stagehand
npm install
```

---

## Architecture

### Multi-Session (Orchestrated)
- **Control Flow:** Sequential, predetermined turns
- **Termination:** After 10 messages
- **Best For:** Reproducible test scenarios

### Independent Agents (Autonomous)
- **Control Flow:** Event-driven, reactive
- **Termination:** Manual (Ctrl+C)
- **Best For:** Continuous testing, stress testing, emergent conversations

---

## Tips

- **Start Alice first** for independent agents (she initiates the conversation)
- **Start Bob ~5 seconds later** to give Alice time to send the first message
- **Watch both windows** to see real-time message exchange
- **Press Ctrl+C** in each terminal to stop the agents
- Use different `CHAT_ID` values to test multiple conversations
