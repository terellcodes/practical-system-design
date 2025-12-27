# Browser-Use AI Chat Agents

Two independent AI agents (Alice and Bob) that continuously chat with each other using [Browser-Use](https://github.com/browser-use/browser-use).

## What is Browser-Use?

[Browser-Use](https://github.com/browser-use/browser-use) is a Python library that makes websites accessible for AI agents. It uses Playwright for browser automation and integrates with LLMs to automate tasks online with natural language instructions.

## Setup

### 1. Install Python Dependencies

```bash
cd automation/browser-use

# Install browser-use and dependencies
pip install browser-use python-dotenv langchain-openai

# Install Chromium browser
uvx browser-use install
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
# Required - OpenAI for browser automation AND conversation generation
OPENAI_API_KEY=your-openai-api-key

# App Configuration
APP_BASE_URL=http://localhost:3000
```

**Note:** This setup uses **only OpenAI** (no Browser-Use API key needed). OpenAI handles both:
- Browser automation tasks (via Browser-Use Agent)
- AI conversation generation (for Alice/Bob responses)

## Run the Agents

### Start Alice (Proactive Agent)

```bash
python alice_agent.py
```

Alice will:
- Log in and open the chat
- Start a conversation if the chat is empty
- Monitor for messages from Bob every 5 seconds
- Generate AI responses and send them

### Start Bob (Reactive Agent)

**Wait 5 seconds after starting Alice, then:**

```bash
python bob_agent.py
```

Bob will:
- Log in and open the chat
- Wait for Alice's messages
- Add a 2-second "thinking" delay
- Generate AI responses and send them

## Features

✅ **Browser-Use Integration** - Uses natural language tasks for browser automation  
✅ **AI-Powered Conversations** - OpenAI generates contextual responses  
✅ **Continuous Operation** - Agents run indefinitely until stopped  
✅ **Independent Execution** - Each agent runs in its own browser window  
✅ **Conversation History** - Maintains context across messages  
✅ **Error Recovery** - Continues running even if errors occur

## Architecture

### Alice Agent (alice_agent.py)
- **Role:** Proactive initiator
- **Behavior:** Starts conversations, responds to Bob
- **Check Interval:** 5 seconds
- **AI Model:** gpt-4o-mini (via OpenAI)

### Bob Agent (bob_agent.py)
- **Role:** Reactive responder
- **Behavior:** Waits for Alice, adds thinking delay
- **Check Interval:** 5 seconds
- **AI Model:** gpt-4o-mini (via OpenAI)

## Browser-Use Tasks

Each agent uses Browser-Use's Agent with natural language tasks:

1. **Login:** `"Go to {URL}, enter '{user_id}' as user_id, click continue..."`
2. **Open Chat:** `"Click on chat called 'My Chat'..."`
3. **Extract Message:** `"Find most recent message from '{friend}'..."`
4. **Send Message:** `"Type '{message}' and press Enter..."`

## Optional: Use Browser-Use Cloud

For better performance and stealth features:

1. Get API key from [Browser-Use Cloud](https://browser-use.com) ($10 free credits)
2. Add to `.env`: `BROWSER_USE_API_KEY=your-key`
3. Uncomment in code: `use_cloud=True`

Benefits:
- Faster execution
- Stealth browser fingerprinting
- Scalable infrastructure
- No local Chrome needed

## Stopping the Agents

Press `Ctrl+C` in each terminal to gracefully shut down the agents.

## Troubleshooting

**"Chromium not found"**
```bash
uvx browser-use install
```

**"No messages from friend"**
- Ensure both agents are logged into the same chat
- Check that `APP_BASE_URL` points to your running app

**"Rate limits"**
- Increase sleep intervals between checks
- Use Browser-Use Cloud for better rate limit handling

## Comparison with Stagehand

| Feature | Browser-Use | Stagehand |
|---------|------------|-----------|
| Language | Python | JavaScript |
| Browser | Playwright | Playwright/Puppeteer |
| LLM Integration | Built-in | Manual |
| Cloud Option | ✅ Browser-Use Cloud | ✅ Browserbase |
| Natural Language | ✅ Native | ✅ Via act() |

## Learn More

- [Browser-Use GitHub](https://github.com/browser-use/browser-use)
- [Browser-Use Docs](https://docs.browser-use.com)
- [Browser-Use Cloud](https://browser-use.com)

