import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import qrcode from 'qrcode-terminal';
import axios from 'axios';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Configuration for stock agent integration
const CONFIG = {
    // Stock agent API URL
    stockAgentUrl: process.env.STOCK_AGENT_URL || 'http://localhost:8080',

    // Target group chat ID (will be logged when messages arrive - update this)
    targetGroupId: process.env.TARGET_GROUP_ID || null,

    // Allowed sender names or numbers (update these with actual sender info)
    allowedSenders: process.env.ALLOWED_SENDERS
        ? process.env.ALLOWED_SENDERS.split(',')
        : ['SenderName1', 'SenderName2'],

    // Regex to extract stock tickers (1-5 uppercase letters, optionally preceded by $)
    tickerRegex: /\$?([A-Z]{1,5})(?=\s|$|,|\.|\)|:)/g
};

// Function to extract stock tickers from message
function extractTickers(messageBody) {
    const tickers = new Set();
    const matches = messageBody.matchAll(CONFIG.tickerRegex);

    for (const match of matches) {
        tickers.add(match[1]);
    }

    return Array.from(tickers);
}

// Function to send message data to stock agent
async function sendToStockAgent(messageData, tickers) {
    try {
        const response = await axios.post(`${CONFIG.stockAgentUrl}/api/whatsapp/message`, {
            timestamp: messageData.timestamp,
            from: messageData.from,
            chatName: messageData.chatName,
            message: messageData.body,
            tickers: tickers
        });

        console.log(`✓ Sent to stock agent: ${tickers.join(', ')}`);
        return response.data;
    } catch (error) {
        console.error('✗ Failed to send to stock agent:', error.message);
    }
}

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// QR code for initial authentication
client.on('qr', (qr) => {
    console.log('Scan this QR code with WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// Connection established
client.on('ready', () => {
    console.log('WhatsApp client is ready and connected');
    console.log('Listening for incoming messages...\n');
});

// Authentication successful
client.on('authenticated', () => {
    console.log('Authentication successful');
});

// Authentication failed
client.on('auth_failure', (msg) => {
    console.error('Authentication failed:', msg);
});

// Disconnected
client.on('disconnected', (reason) => {
    console.log('Client disconnected:', reason);
});

// Incoming message handler
client.on('message', async (message) => {
    const contact = await message.getContact();
    const chat = await message.getChat();

    const messageData = {
        timestamp: new Date(message.timestamp * 1000).toISOString(),
        from: contact.pushname || contact.number,
        chatName: chat.name || contact.number,
        chatId: chat.id._serialized,
        isGroup: chat.isGroup,
        body: message.body,
        hasMedia: message.hasMedia,
        type: message.type
    };

    // Log incoming message
    console.log('--- New Message ---');
    console.log(`From: ${messageData.from}`);
    console.log(`Chat: ${messageData.chatName}${messageData.isGroup ? ' (Group)' : ''}`);
    console.log(`Chat ID: ${messageData.chatId}`);
    console.log(`Time: ${messageData.timestamp}`);
    console.log(`Message: ${messageData.body}`);
    if (messageData.hasMedia) {
        console.log(`Media Type: ${messageData.type}`);
    }

    // Filter: Check if message is from target group (if configured)
    if (CONFIG.targetGroupId && messageData.chatId !== CONFIG.targetGroupId) {
        console.log('⊘ Skipped: Not from target group');
        console.log('-------------------\n');
        return;
    }

    // Filter: Check if message is from allowed sender
    const isAllowedSender = CONFIG.allowedSenders.some(sender =>
        messageData.from.includes(sender)
    );

    if (!isAllowedSender) {
        console.log('⊘ Skipped: Not from allowed sender');
        console.log('-------------------\n');
        return;
    }

    // Extract stock tickers from message
    const tickers = extractTickers(messageData.body);

    if (tickers.length > 0) {
        console.log(`📈 Found tickers: ${tickers.join(', ')}`);
        await sendToStockAgent(messageData, tickers);
    } else {
        console.log('⊘ No tickers found in message');
    }

    console.log('-------------------\n');
});

// Start the client
console.log('Starting WhatsApp client...');
client.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nShutting down gracefully...');
    await client.destroy();
    process.exit(0);
});
