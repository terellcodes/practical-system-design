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

const PERSONA = "alice";
const FRIEND = "bob";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Generate an AI response for Alice
 */
async function generateResponse(conversationHistory) {
  const systemPrompt = `You are Alice, having a casual ongoing conversation with your friend Bob via chat. 
Be natural, friendly, and engaging. Keep responses conversational and brief (1-2 sentences).
Sometimes ask questions, share thoughts, or respond to what Bob says. Be a good friend!`;

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
    return "That's interesting! Tell me more.";
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
 * Login as Alice
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
  console.log(`\n👩 Starting Alice Agent...`);
  console.log(`   Friend: ${FRIEND}`);
  console.log(`   Chat: ${CHAT_ID}\n`);

  await stagehand.init();
  const page = stagehand.context.pages()[0];

  try {
    await login(page);
    await openChat(page);

    const conversationHistory = [];
    let lastMessageText = null;
    let shouldStartConversation = true;

    console.log(`\n🤖 Alice is now active and monitoring for messages...\n`);

    // Main loop
    while (true) {
      try {
        // Check for new message from Bob
        const latestMessage = await getLatestMessageFrom(page, FRIEND);

        if (latestMessage && latestMessage !== lastMessageText) {
          // New message received!
          console.log(`\n📥 Bob: "${latestMessage}"`);
          lastMessageText = latestMessage;
          
          // Update conversation history
          conversationHistory.push({ role: "user", content: latestMessage });

          // Generate response
          console.log(`💭 Alice thinking...`);
          const response = await generateResponse(conversationHistory);
          conversationHistory.push({ role: "assistant", content: response });

          // Send response
          console.log(`📤 Alice: "${response}"`);
          await sendMessage(page, response);

          // Reset the flag since Bob has responded
          shouldStartConversation = false;

        } else if (shouldStartConversation && conversationHistory.length === 0) {
          // Alice starts the conversation if no messages yet
          console.log(`💭 Alice starting conversation...`);
          const opening = await generateResponse([]);
          conversationHistory.push({ role: "assistant", content: opening });

          console.log(`📤 Alice: "${opening}"`);
          await sendMessage(page, opening);
          shouldStartConversation = false;

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
    console.log(`\n👋 Alice agent shutting down...`);
    await stagehand.close?.();
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});



