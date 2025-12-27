"""
Alice Agent - Proactive chat agent using Browser-Use
Monitors chat and responds to Bob using AI
Uses OpenAI for all tasks (browser automation + conversation generation)
"""

import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent, Browser
from langchain_openai import ChatOpenAI

load_dotenv()

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000")
PERSONA = "alice"
FRIEND = "bob"

# Track last message to avoid duplicates
last_message_text = None
conversation_history = []


class OpenAIWrapper:
    """Wrapper to add provider attribute for Browser-Use compatibility"""
    def __init__(self, llm):
        self._llm = llm
        self.provider = 'openai'
        self.model = llm.model_name  # Browser-Use also needs this
    
    def __getattr__(self, name):
        return getattr(self._llm, name)


def get_llm():
    """Create and wrap OpenAI LLM for Browser-Use"""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    return OpenAIWrapper(llm)


async def login_and_open_chat(browser):
    """Login as Alice and open the chat"""
    print(f"🔐 Logging in as {PERSONA}...")
    
    llm = get_llm()
    
    # Login task
    login_agent = Agent(
        task=f"Go to {APP_BASE_URL}, enter '{PERSONA}' as the user_id, click continue, and wait for the next page to load.",
        llm=llm,
        browser=browser,
    )
    await login_agent.run()
    print(f"✅ Logged in as {PERSONA}")
    
    # Open chat task
    print("💬 Opening chat...")
    chat_agent = Agent(
        task="Click on the chat called 'My Chat' and wait for the message panel to be visible.",
        llm=llm,
        browser=browser,
    )
    await chat_agent.run()
    print("✅ Chat opened")


async def get_latest_message_from_friend(browser):
    """Extract the latest message from Bob"""
    llm = get_llm()
    
    extract_agent = Agent(
        task=f"Look at the chat messages and find the most recent message from '{FRIEND}'. Return only the message text, nothing else. If there are no messages from {FRIEND}, return 'NO_MESSAGES'.",
        llm=llm,
        browser=browser,
    )
    
    history = await extract_agent.run()
    
    # Extract the final result from the agent
    if history and len(history) > 0:
        final_result = history[-1].result
        if final_result and final_result != "NO_MESSAGES":
            return final_result.strip()
    
    return None


async def send_message(browser, message_text):
    """Send a message in the chat"""
    llm = get_llm()
    
    send_agent = Agent(
        task=f"Type '{message_text}' in the message input field and press Enter to send it.",
        llm=llm,
        browser=browser,
    )
    await send_agent.run()


async def generate_ai_response(message_from_friend):
    """Generate an AI response to friend's message"""
    global conversation_history
    
    # Use OpenAI to generate a contextual response
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)
    
    system_prompt = """You are Alice, having a casual ongoing conversation with your friend Bob via chat. 
Be natural, friendly, and engaging. Keep responses conversational and brief (1-2 sentences).
Sometimes ask questions, share thoughts, or respond to what Bob says. Be a good friend!"""
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add conversation history
    for msg in conversation_history:
        messages.append(msg)
    
    # Add the new message from friend
    messages.append({"role": "user", "content": message_from_friend})
    
    response = await llm.ainvoke(messages)
    response_text = response.content.strip()
    
    # Update history
    conversation_history.append({"role": "user", "content": message_from_friend})
    conversation_history.append({"role": "assistant", "content": response_text})
    
    return response_text


async def start_conversation(browser):
    """Start the conversation if no messages exist"""
    global conversation_history
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)
    
    system_prompt = """You are Alice, starting a casual conversation with your friend Bob via chat. 
Write a friendly opening message (1-2 sentences). Be natural and conversational."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Write a friendly opening message to Bob."}
    ]
    
    response = await llm.ainvoke(messages)
    opening_text = response.content.strip()
    
    conversation_history.append({"role": "assistant", "content": opening_text})
    
    return opening_text


async def main():
    global last_message_text
    
    print("\n👩 Starting Alice Agent (Browser-Use)...")
    print(f"   Friend: {FRIEND}")
    print(f"   App: {APP_BASE_URL}\n")
    
    # Initialize browser
    print("💻 Using local browser")
    browser = Browser()
    
    try:
        # Login and setup
        await login_and_open_chat(browser)
        
        should_start_conversation = True
        
        print("\n🤖 Alice is now active and monitoring for messages...\n")
        
        # Main loop
        while True:
            try:
                # Check for new message from Bob
                latest_message = await get_latest_message_from_friend(browser)
                
                if latest_message and latest_message != last_message_text:
                    # New message from Bob!
                    print(f"\n📥 Bob: \"{latest_message}\"")
                    last_message_text = latest_message
                    
                    # Generate AI response
                    print("💭 Alice thinking...")
                    response = await generate_ai_response(latest_message)
                    
                    print(f"📤 Alice: \"{response}\"")
                    await send_message(browser, response)
                    
                    should_start_conversation = False
                    
                elif should_start_conversation and len(conversation_history) == 0:
                    # Start conversation
                    print("💭 Alice starting conversation...")
                    opening = await start_conversation(browser)
                    
                    print(f"📤 Alice: \"{opening}\"")
                    await send_message(browser, opening)
                    should_start_conversation = False
                    
                else:
                    # No new messages, wait
                    await asyncio.sleep(5)
                    
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error in agent loop: {e}")
                await asyncio.sleep(5)
                
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Alice agent shutting down...")


if __name__ == "__main__":
    asyncio.run(main())

