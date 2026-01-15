import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const APP_BASE_URL = process.env.APP_BASE_URL ?? "http://localhost:3000";
const CHAT_ID = process.env.CHAT_ID ?? "demo";
const MODEL = process.env.STAGEHAND_MODEL ?? "openai/gpt-4o-mini";
const CHAT_MODEL = process.env.CHAT_MODEL ?? "gpt-4o-mini";

const stagehand = new Stagehand({
  env: "LOCAL",
  verbose: 1,
  headless: false,
  model: MODEL,
});

const PERSONA = "bob";
const FRIEND = "alice";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Generate an AI response for Bob
 */
async function generateResponse(conversationHistory) {
  const systemPrompt = `You are Bob, having a casual ongoing conversation with your friend Alice via chat. 
Be natural, helpful, and witty. Keep responses conversational and brief (1-2 sentences).
Share interesting thoughts, respond thoughtfully, and be engaging. Be a good friend!`;

  try {
    const response = await openai.chat.completions.create({
      model: CHAT_MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        ...conversationHistory
      ],
      temperature: 0.8,
      max_tokens: 100,
    });

    return response.choices[0].message.content.trim();
  } catch (error) {
    console.error(`❌ Error generating AI response:`, error.message);
    return "I see what you mean! What do you think about that?";
  }
}

/**
 * Extract the most recent message from friend
 */
async function getLatestMessageFrom(page, fromUser) {
  try {
    const messages = await stagehand.extract(
      `Extract all visible chat messages. For each message bubble, get the sender name and message text. Return as an array of objects with "sender" and "text" fields. Return ONLY a JSON array.`,
      z.array(z.object({
        sender: z.string(),
        text: z.string()
      })),
      { page }
    );

    if (messages && messages.length > 0) {
      // Find most recent message from target user
      for (let j = messages.length - 1; j >= 0; j--) {
        const msg = messages[j];
        if (msg.sender && msg.sender.toLowerCase().includes(fromUser.toLowerCase())) {
          return msg.text;
        }
      }
    }
  } catch (error) {
    console.error(`Error extracting messages:`, error.message);
  }
  return null;
}

/**
 * Send a message
 */
async function sendMessage(page, text) {
  await stagehand.act(`Type "${text}" into the message input field`, { page });
  await stagehand.act(`Press Enter to send the message`, { page });
  await sleep(500);
}

/**
 * Login as Bob
 */
async function login(page) {
  await page.goto(APP_BASE_URL);
  console.log(`🔐 Logging in as ${PERSONA}...`);
  await stagehand.act(`Enter the user_id as ${PERSONA}`, { page });
  await stagehand.act(`Click continue and wait until next page is loaded.`, { page });
  console.log(`✅ Logged in as ${PERSONA}`);
}

/**
 * Open the chat
 */
async function openChat(page) {
  console.log(`💬 Opening chat...`);
  await stagehand.act(
    `Click on chat called "My Chat". Wait for message panel to be visible.`,
    { page }
  );
  console.log(`✅ Chat opened`);
}

/**
 * Main agent loop
 */
async function main() {
  console.log(`\n👨 Starting Bob Agent...`);
  console.log(`   Friend: ${FRIEND}`);
  console.log(`   Chat: ${CHAT_ID}\n`);

  await stagehand.init();
  const page = stagehand.context.pages()[0];

  try {
    await login(page);
    await openChat(page);

    const conversationHistory = [];
    let lastMessageText = null;

    console.log(`\n🤖 Bob is now active and monitoring for messages...\n`);

    // Main loop - Bob is reactive, waits for Alice to start
    while (true) {
      try {
        // Check for new message from Alice
        const latestMessage = await getLatestMessageFrom(page, FRIEND);

        if (latestMessage && latestMessage !== lastMessageText) {
          // New message received!
          console.log(`\n📥 Alice: "${latestMessage}"`);
          lastMessageText = latestMessage;
          
          // Update conversation history
          conversationHistory.push({ role: "user", content: latestMessage });

          // Wait a moment (simulate reading/thinking)
          await sleep(2000);

          // Generate response
          console.log(`💭 Bob thinking...`);
          const response = await generateResponse(conversationHistory);
          conversationHistory.push({ role: "assistant", content: response });

          // Send response
          console.log(`📤 Bob: "${response}"`);
          await sendMessage(page, response);

        } else {
          // No new messages, wait and check again
          await sleep(3000);
        }

      } catch (error) {
        console.error(`❌ Error in agent loop:`, error.message);
        await sleep(5000);
      }
    }

  } catch (error) {
    console.error(`❌ Fatal error:`, error);
  } finally {
    console.log(`\n👋 Bob agent shutting down...`);
    await stagehand.close?.();
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});



