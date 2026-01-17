# Copilot Service

AI-powered assistant for the messaging application using LangGraph and Claude.

## Overview

The copilot service is a ReAct (Reasoning + Acting) agent that helps users manage their contacts, invites, and chats through natural language conversation. It uses LangGraph for agent orchestration and Claude for reasoning.

## Features

- **Contact Management**: Invite users by connect PIN, accept pending invites, list contacts
- **Chat Management**: Create chats, add participants, send messages, list chats
- **Persistent Conversations**: Per-user conversation history stored in PostgreSQL
- **Context-Aware**: Maintains user context across tool executions

## Future Capabilities

These are potential areas to expand the agent's capabilities and push the boundaries of what's possible:

### 1. Content Intelligence & Knowledge Management
- **Semantic Search**: Search across all messages using natural language queries ("find conversations about project deadlines")
- **Auto-Summarization**: Generate summaries of long conversations or chat threads
- **Knowledge Extraction**: Extract action items, decisions, and key information from chats
- **Topic Clustering**: Automatically organize conversations by themes
- **Smart Pinning**: AI-suggested important messages based on context

### 2. Automation & Workflow Orchestration
- **Scheduled Actions**: Set reminders, delayed messages, recurring notifications
- **Custom Workflows**: Create IFTTT-style automations ("when someone mentions 'urgent', notify me immediately")
- **Batch Operations**: Bulk message sending, mass invite management
- **Event Triggers**: React to specific events (new member joins → send welcome message)
- **Smart Routing**: Automatically forward messages to relevant chats based on content

### 3. Advanced Analytics & Insights
- **Conversation Analytics**: Track response times, engagement patterns, peak activity hours
- **Sentiment Analysis**: Gauge conversation tone and mood
- **Network Analysis**: Visualize communication patterns between users
- **Predictive Insights**: Suggest optimal times to send messages, predict user availability
- **Engagement Scoring**: Identify your most active contacts and important conversations

### 4. Multimodal Capabilities
- **Image Analysis**: Describe images, extract text (OCR), identify objects
- **Document Processing**: Parse PDFs, extract data from spreadsheets
- **Voice Integration**: Transcribe voice messages, text-to-speech for accessibility
- **File Intelligence**: Summarize documents, answer questions about uploaded files
- **Screenshot Analysis**: Extract and understand information from shared screens

### 5. External Integration Hub
- **Calendar Sync**: Schedule meetings directly from chat ("set up a meeting with John tomorrow")
- **Email Bridge**: Send emails, read inbox, respond to messages
- **Task Manager Integration**: Create tasks in Asana, Jira, Todoist
- **Web Search**: Fetch real-time information from the internet
- **API Executor**: Make HTTP requests to external services with authentication
- **Cloud Storage**: Access and share files from Google Drive, Dropbox, etc.

### 6. Intelligent Communication
- **Multi-Language Translation**: Real-time translation of messages
- **Writing Assistant**: Improve message tone, fix grammar, suggest rephrasings
- **Context Completion**: Auto-suggest message completions based on conversation context
- **Meeting Coordination**: Find common availability, send invites, manage RSVPs
- **Polling & Surveys**: Create and analyze polls within chats

### 7. Security & Governance
- **Content Moderation**: Flag inappropriate content automatically
- **Anomaly Detection**: Identify suspicious activity patterns
- **Access Control**: Manage permissions, create private groups with rules
- **Data Retention Policies**: Auto-archive or delete based on rules
- **Audit Logging**: Track all agent actions for compliance

### 8. Personalization & Learning
- **Preference Learning**: Remember user preferences over time
- **Custom Commands**: Create shortcuts ("@copilot daily" → show daily summary)
- **Context Awareness**: Remember project context, ongoing conversations
- **Proactive Suggestions**: "You haven't responded to Jane in 3 days"
- **Smart Defaults**: Learn common patterns (always CC Bob on project updates)

### 9. Collaborative Features
- **Shared To-Do Lists**: Manage team tasks within chats
- **Brainstorming Mode**: Facilitate ideation sessions with structured prompts
- **Decision Making**: Track proposals, votes, consensus building
- **Project Tracking**: Link chats to projects, track milestones
- **Resource Sharing**: Create shared knowledge bases from conversations

### 10. Advanced Data Operations
- **Database Queries**: Query application data with natural language
- **Report Generation**: Create custom reports from conversation data
- **Data Export**: Export conversations in various formats (PDF, CSV, JSON)
- **Cross-Service Actions**: Orchestrate actions across multiple microservices
- **Webhooks**: Trigger external systems based on chat events

### 11. Context-Aware Assistance
- **Smart Notifications**: Only notify based on importance and context
- **Auto-Categorization**: Tag messages by type (question, action item, FYI)
- **Follow-up Tracking**: Remind about unanswered questions
- **Reference Resolution**: "Show me what Sarah mentioned earlier about the budget"
- **Temporal Reasoning**: Handle time-based queries ("messages from last week about marketing")

### 12. Meta & Self-Improvement
- **Usage Analytics**: Track how users interact with the agent
- **Feedback Loop**: Learn from user corrections and preferences
- **A/B Testing**: Test different response styles
- **Tool Recommendations**: Suggest capabilities users might not know about
- **Performance Monitoring**: Track response quality and success rates

### Priority Quick Wins
1. **Semantic search** across all conversations
2. **Document/image analysis** for shared content
3. **Task extraction** and management from conversations
4. **Smart summarization** of long threads
5. **External API integration** framework for extensibility

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Copilot Service                        │
├─────────────────────────────────────────────────────────────┤
│  FastAPI                                                    │
│  ├── POST /api/copilot/chat      → Process user message     │
│  ├── GET  /api/copilot/history   → Get conversation history │
│  └── DELETE /api/copilot/history → Clear history            │
├─────────────────────────────────────────────────────────────┤
│  LangGraph ReAct Agent                                      │
│  ├── Claude (LLM) ─────────────────────────────────────┐    │
│  │                                                     │    │
│  │   Reason → Act → Observe → Reason → ...             │    │
│  │                                                     │    │
│  ├── Tools ────────────────────────────────────────────┤    │
│  │   ├── invite_user          (action)                 │    │
│  │   ├── accept_invite        (action)                 │    │
│  │   ├── create_chat          (action)                 │    │
│  │   ├── add_chat_participants(action)                 │    │
│  │   ├── send_chat_message    (action)                 │    │
│  │   ├── list_contacts        (read-only)              │    │
│  │   ├── list_pending_invites (read-only)              │    │
│  │   └── list_chats           (read-only)              │    │
│  │                                                     │    │
│  └── AsyncPostgresSaver (checkpointer) ────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
   ┌──────────┐                  ┌──────────────┐
   │  user-   │                  │    chat-     │
   │ service  │                  │   service    │
   └──────────┘                  └──────────────┘
```

## Tech Stack

- **LangGraph** - Agent orchestration with ReAct pattern
- **LangChain Anthropic** - Claude integration
- **FastAPI** - REST API framework
- **PostgreSQL** - Conversation checkpoint persistence
- **httpx** - Async HTTP client for inter-service communication

## Project Structure

```
copilot-service/
├── src/
│   ├── agent/
│   │   ├── graph.py        # CopilotAgent class and ReAct agent setup
│   │   ├── state.py        # Agent state definitions
│   │   ├── context.py      # User context management (contextvars)
│   │   ├── prompts.py      # System prompt templates
│   │   └── tools/
│   │       ├── invite_tools.py   # invite_user, accept_invite
│   │       ├── chat_tools.py     # create_chat, add_chat_participants
│   │       ├── message_tools.py  # send_chat_message
│   │       └── context_tools.py  # list_contacts, list_pending_invites, list_chats
│   ├── routes/
│   │   ├── copilot.py      # /api/copilot endpoints
│   │   └── health.py       # Health check endpoint
│   ├── services/
│   │   ├── user_service_client.py   # HTTP client for user-service
│   │   └── chat_service_client.py   # HTTP client for chat-service
│   ├── main.py             # FastAPI app entry point
│   └── config.py           # Configuration from environment
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | (required) |
| `ANTHROPIC_MODEL` | Model to use | `claude-sonnet-4-20250514` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://dapruser:daprpassword@postgres:5432/daprdb` |
| `USER_SERVICE_URL` | User service base URL | `http://user-service:8001` |
| `CHAT_SERVICE_URL` | Chat service base URL | `http://chat-service:8002` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |

## API Endpoints

### Send Message

```http
POST /api/copilot/chat
Content-Type: application/json
X-User-Id: 1
X-Username: johndoe
X-User-Name: John Doe
X-Conversation-Version: 0

{
  "message": "Show me my contacts"
}
```

Response:
```json
{
  "response": "Here are your contacts:\n\n1. **Jane Smith** (@janesmith)\n2. **Bob Wilson** (@bobwilson)"
}
```

### Get History

```http
GET /api/copilot/history
X-User-Id: 1
```

### Clear History

```http
DELETE /api/copilot/history
X-User-Id: 1
```

## How It Works

1. **User sends message** via `/api/copilot/chat`
2. **Agent receives message** with user context (ID, username, name)
3. **LangGraph ReAct loop**:
   - Claude reasons about what action to take
   - Executes appropriate tool(s)
   - Observes tool results
   - Continues reasoning or returns response
4. **Conversation persisted** to PostgreSQL via AsyncPostgresSaver
5. **Response returned** to user

### Conversation Threading

Each user has their own conversation thread identified by:
```
copilot-user-{user_id}-v{conversation_version}
```

Clearing history increments the version, effectively starting a fresh conversation.

## Development

### Prerequisites

- Python 3.11+
- PostgreSQL
- Anthropic API key

### Local Setup

```bash
# Install dependencies
pip install -e .

# Set environment variables
export ANTHROPIC_API_KEY="your-api-key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"

# Run the service
uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Running with Docker

```bash
docker build -f services/copilot-service/Dockerfile -t copilot-service .
docker run -p 8003:8003 -e ANTHROPIC_API_KEY=your-key copilot-service
```

## Adding New Tools

1. Create a new file in `src/agent/tools/` or add to an existing one
2. Define the tool using `@tool` decorator from `langchain_core.tools`
3. Import and add to `TOOLS` list in `src/agent/graph.py`

Example:
```python
from langchain_core.tools import tool
from src.agent.context import get_user_context

@tool
async def my_new_tool(param: str) -> str:
    """Description of what this tool does."""
    user_ctx = get_user_context()
    # Implement tool logic
    return "Result"
```
