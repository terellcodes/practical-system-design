import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const requiredEnv = [
  "OPENAI_API_KEY",
];

const missing = requiredEnv.filter((key) => !process.env[key]);
if (missing.length) {
  throw new Error(`Missing required env vars: ${missing.join(", ")}`);
}

const APP_BASE_URL = process.env.APP_BASE_URL ?? "http://localhost:3000";
const CHAT_ID = process.env.CHAT_ID ?? "demo";
const CHAT_URL = process.env.CHAT_URL ?? `${APP_BASE_URL}/chat/${CHAT_ID}`;
const MODEL = process.env.STAGEHAND_MODEL ?? "openai/gpt-4o-mini";

// Create two separate Stagehand instances for two browser windows
const stagehandA = new Stagehand({
  env: "LOCAL",
  verbose: 1,
  headless: false,
  model: MODEL,
});

const stagehandB = new Stagehand({
  env: "LOCAL",
  verbose: 1,
  headless: false,
  model: MODEL,
});

const USER_A_ID =  "alice";
const USER_B_ID = "bob";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Generate an AI response using OpenAI
 * @param {string} persona - Either 'alice' or 'bob'
 * @param {Array} conversationHistory - Array of {role, content} messages
 * @returns {Promise<string>} Generated response
 */
async function generateAIResponse(persona, conversationHistory) {
  const systemPrompts = {
    alice: "You are Alice, a friendly and curious person having a casual conversation with Bob. Keep your responses natural, conversational, and brief (1-2 sentences). Be engaging and ask questions sometimes.",
    bob: "You are Bob, a helpful and witty person having a casual conversation with Alice. Keep your responses natural, conversational, and brief (1-2 sentences). Be friendly and share interesting thoughts."
  };

  try {
    const response = await openai.chat.completions.create({
      model: process.env.CHAT_MODEL || "gpt-4o-mini",
      messages: [
        { role: "system", content: systemPrompts[persona] },
        ...conversationHistory
      ],
      temperature: 0.8,
      max_tokens: 100,
    });

    return response.choices[0].message.content.trim();
  } catch (error) {
    console.error(`Error generating AI response for ${persona}:`, error.message);
    // Fallback response
    return persona === 'alice' 
      ? "That's interesting! Tell me more."
      : "I see what you mean. What do you think about that?";
  }
}

async function login(stagehand, page, user_id) {
  await page.goto(`${APP_BASE_URL}`);
  console.log(`Enter the user_id as ${user_id}. Click the continue button. Wait until the next page is loaded.`);
  await stagehand.act(
    `Enter the user_id as ${user_id}`,
    { page }
  );
  await stagehand.act(
    `Click continue and wait until next page is loaded.`,
    { page }
  );
}

async function openChat(stagehand, page) {
  await stagehand.act(
    `Click on chat called "My Chat. Wait for message panel to be visible.`,
    { page }
  );
}

async function sendMessage(stagehand, page, text) {
  // Split into two explicit steps
  await stagehand.act(
    `Type "${text}" into the message input field`,
    { page }
  );
  await stagehand.act(
    `Press Enter to send the message`,
    { page }
  );
  // Small delay to ensure message is sent
  await sleep(500);
}

/**
 * Waits for a new message from a specific user and extracts it
 * @param {Stagehand} stagehand - The Stagehand instance
 * @param {Page} page - The page to monitor
 * @param {string} fromUser - The username to wait for a message from (e.g., "bob", "alice")
 * @param {number} timeoutSeconds - How long to wait before timing out (default: 30 seconds)
 * @returns {Promise<string>} The extracted message text
 */
async function waitForMessageFrom(stagehand, page, fromUser, timeoutSeconds = 30) {
  const maxAttempts = Math.ceil(timeoutSeconds / 2);
  
  for (let i = 0; i < maxAttempts; i += 1) {
    try {
      // Extract all visible messages with sender names and text
      const messages = await stagehand.extract(
        `Extract all visible chat messages. For each message bubble, get the sender name and message text. Return as an array of objects with "sender" and "text" fields. The sender name appears above or near each message bubble (like "bob", "alice", etc). Return ONLY a JSON array.`,
        z.array(z.object({
          sender: z.string(),
          text: z.string()
        })),
        { page }
      );

      // Find the most recent message from the target user
      if (messages && messages.length > 0) {
        // Search from newest to oldest
        for (let j = messages.length - 1; j >= 0; j--) {
          const msg = messages[j];
          if (msg.sender && msg.sender.toLowerCase().includes(fromUser.toLowerCase())) {
            console.log(`✓ Found message from ${fromUser}: "${msg.text}"`);
            return msg.text;
          }
        }
      }

      console.log(`⏳ Waiting for message from ${fromUser}... (attempt ${i + 1}/${maxAttempts})`);
      await sleep(2000);
    } catch (error) {
      console.error(`Error extracting messages:`, error.message);
      await sleep(2000);
    }
  }

  throw new Error(`Timed out waiting for message from "${fromUser}" after ${timeoutSeconds}s`);
}

/**
 * Waits for a specific message text to appear (legacy version)
 */
async function waitForMessage(stagehand, page, expectedText, label) {
  const attempts = 6;
  for (let i = 0; i < attempts; i += 1) {
    const messages =
      (await stagehand.extract(
        `Return the last 15 chat message bubbles as an array of visible message texts in chronological order (oldest to newest). Respond ONLY with a JSON array of strings.`,
        z.array(z.string()),
        { page }
      )) ?? [];

    if (messages.some((m) => m.includes(expectedText))) {
      return;
    }

    await sleep(1500);
  }

  throw new Error(`Timed out waiting for "${expectedText}" in ${label}`);
}

async function main() {
  // Initialize both Stagehand instances
  await Promise.all([
    stagehandA.init(),
    stagehandB.init()
  ]);

  // Get the first page from each browser window
  const pageA = stagehandA.context.pages()[0];
  const pageB = stagehandB.context.pages()[0];

  try {
    await Promise.all([
      login(
        stagehandA,
        pageA,
        USER_A_ID,
      ),
      login(
        stagehandB,
        pageB,
        USER_B_ID,
      ),
    ]);

    await Promise.all([openChat(stagehandA, pageA), openChat(stagehandB, pageB)]);

    // Initialize conversation histories for both personas
    const aliceHistory = [];
    const bobHistory = [];
    const conversationLog = [];
    
    const totalTurns = 10;
    
    console.log("\n🤖 Starting AI-driven conversation (10 turns)...\n");
    
    // Alice starts the conversation
    console.log("📤 [Turn 1/10] Alice (AI) generating opening message...");
    const aliceOpening = await generateAIResponse('alice', []);
    aliceHistory.push({ role: "assistant", content: aliceOpening });
    conversationLog.push({ sender: "alice", message: aliceOpening, turn: 1 });
    
    console.log(`   Alice: "${aliceOpening}"`);
    await sendMessage(stagehandA, pageA, aliceOpening);
    
    // Bob receives and responds (turns 2-10)
    for (let turn = 2; turn <= totalTurns; turn++) {
      const isAliceTurn = turn % 2 === 0; // Even turns = Bob responds, Odd = Alice responds
      
      if (!isAliceTurn) {
        // Alice's turn to respond to Bob's message
        console.log(`\n📥 [Turn ${turn}/${totalTurns}] Alice waiting for Bob's message...`);
        const bobMsg = await waitForMessageFrom(stagehandA, pageA, "bob", 60);
        console.log(`   Bob said: "${bobMsg}"`);
        
        // Update Bob's history and Alice's context
        bobHistory.push({ role: "assistant", content: bobMsg });
        aliceHistory.push({ role: "user", content: bobMsg });
        conversationLog.push({ sender: "bob", message: bobMsg, turn: turn - 1 });
        
        // Generate Alice's AI response
        console.log(`📤 [Turn ${turn}/${totalTurns}] Alice (AI) generating response...`);
        const aliceResponse = await generateAIResponse('alice', aliceHistory);
        aliceHistory.push({ role: "assistant", content: aliceResponse });
        conversationLog.push({ sender: "alice", message: aliceResponse, turn });
        
        console.log(`   Alice: "${aliceResponse}"`);
        await sendMessage(stagehandA, pageA, aliceResponse);
        
      } else {
        // Bob's turn to respond to Alice's message
        console.log(`\n📥 [Turn ${turn}/${totalTurns}] Bob waiting for Alice's message...`);
        const aliceMsg = await waitForMessageFrom(stagehandB, pageB, "alice", 60);
        console.log(`   Alice said: "${aliceMsg}"`);
        
        // Update Alice's history and Bob's context
        aliceHistory.push({ role: "assistant", content: aliceMsg });
        bobHistory.push({ role: "user", content: aliceMsg });
        
        // Generate Bob's AI response
        console.log(`📤 [Turn ${turn}/${totalTurns}] Bob (AI) generating response...`);
        const bobResponse = await generateAIResponse('bob', bobHistory);
        bobHistory.push({ role: "assistant", content: bobResponse });
        conversationLog.push({ sender: "bob", message: bobResponse, turn });
        
        console.log(`   Bob: "${bobResponse}"`);
        await sendMessage(stagehandB, pageB, bobResponse);
      }
      
      // Small delay between turns for natural pacing
      await sleep(1000);
    }

    console.log("\n" + "=".repeat(60));
    console.log("🎉 AI Conversation Complete!");
    console.log("=".repeat(60));
    console.log("\n📝 Full Conversation Log:\n");
    
    conversationLog.forEach((entry, idx) => {
      const prefix = entry.sender === 'alice' ? '👩 Alice:' : '👨 Bob:';
      console.log(`${idx + 1}. ${prefix} ${entry.message}`);
    });
    
    console.log("\n" + "=".repeat(60));
    await sleep(10000); // Keep browsers open to review
  } finally {
    await Promise.allSettled([
      stagehandA?.close?.(),
      stagehandB?.close?.()
    ]);
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});

