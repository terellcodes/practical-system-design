## Stagehand AI-Driven Multi-User Chat Test

Two AI personas (Alice and Bob) have an autonomous 10-turn conversation in separate browser windows using OpenAI for response generation.

### Setup
- Set env vars in `.env`:
  - `OPENAI_API_KEY` (required)
  - Optional: `APP_BASE_URL` (default `http://localhost:3000`), `CHAT_ID` (default `demo`), `CHAT_URL` (overrides chat link), `STAGEHAND_MODEL` (default `openai/gpt-4o-mini`), `CHAT_MODEL` (LLM for conversation, default `gpt-4o-mini`).
- Install deps:
  ```bash
  cd automation/stagehand
  npm install
  ```

### Run
```bash
npm start
```

The script:
1. Opens **two separate Chrome windows** (Alice and Bob)
2. Logs both users in and opens the chat
3. **Alice (AI) generates an opening message** using OpenAI
4. **Bob and Alice take turns** (10 total messages), each:
   - Waiting for the other's message using `waitForMessageFrom()`
   - Generating a contextual AI response based on conversation history
   - Sending the response via Stagehand
5. Displays full conversation log at the end

Each persona maintains independent conversation context and generates natural, engaging responses.

