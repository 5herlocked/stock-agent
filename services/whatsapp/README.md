# WhatsApp Stock Signal Integration

This service monitors WhatsApp messages for stock tickers and forwards them to the Stock Agent dashboard.

## Features

- Monitors WhatsApp messages in real-time using whatsapp-web.js
- Filters messages by specific group chat and allowed senders
- Extracts stock tickers from messages (e.g., AAPL, $TSLA, NVDA)
- Forwards ticker data to Stock Agent API
- Stock Agent fetches real-time data from Polygon API
- Displays signals on the dashboard with context (sender, chat, original message)

## Setup

### 1. Install Dependencies

```bash
cd services/whatsapp
npm install
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Stock Agent API URL (default: http://localhost:8080)
STOCK_AGENT_URL=http://localhost:8080

# Target WhatsApp group chat ID
# Leave empty initially - it will be logged when messages arrive
TARGET_GROUP_ID=

# Allowed senders (comma-separated names or phone numbers)
ALLOWED_SENDERS=John Doe,Jane Smith
```

### 3. First Run - Get Group Chat ID

Run the service without configuring `TARGET_GROUP_ID`:

```bash
npm start
```

1. Scan the QR code with WhatsApp on your phone
2. Send a test message in the group you want to monitor
3. Check the console output - you'll see the Chat ID logged
4. Copy the Chat ID and add it to your `.env` file

Example output:
```
--- New Message ---
From: John Doe
Chat: Stock Discussion (Group)
Chat ID: 1234567890@g.us  ← Copy this
Message: Check out AAPL and TSLA today!
```

### 4. Configure Allowed Senders

Update the `ALLOWED_SENDERS` in your `.env` file with the exact names or numbers of people whose messages you want to monitor. The service checks if the sender's name contains any of these values.

### 5. Run the Service

```bash
npm start
```

The service will now:
- Monitor messages from allowed senders in the target group
- Extract stock tickers from messages
- Send them to the Stock Agent API
- Stock data will appear on your dashboard under "WhatsApp Stock Signals"

## How It Works

### Message Filtering

1. **Group Filter**: Only processes messages from the configured `TARGET_GROUP_ID`
2. **Sender Filter**: Only processes messages where the sender's name includes one of the `ALLOWED_SENDERS`
3. **Ticker Extraction**: Uses regex to find stock tickers (1-5 uppercase letters, optionally prefixed with $)

### Ticker Detection

The service detects tickers in these formats:
- `AAPL` - Simple ticker
- `$TSLA` - Dollar-prefixed ticker
- `Check out NVDA, MSFT and GOOGL` - Multiple tickers in a sentence

### Data Flow

```
WhatsApp Message
    ↓
whatsapp-web.js (this service)
    ↓
Filter by group and sender
    ↓
Extract tickers with regex
    ↓
POST to Stock Agent API (/api/whatsapp/message)
    ↓
Stock Agent fetches data from Polygon API
    ↓
Stores in SQLite (whatsapp_recommendations table)
    ↓
Displays on Dashboard
```

## Troubleshooting

### QR Code Not Appearing
- Make sure the terminal supports displaying the QR code
- Try running in a different terminal emulator
- Check that whatsapp-web.js is properly installed

### Messages Not Being Forwarded
1. Verify `TARGET_GROUP_ID` is correct (check console logs)
2. Confirm sender names in `ALLOWED_SENDERS` match exactly (case-insensitive partial match)
3. Check that the Stock Agent is running on the configured URL
4. Look for error messages in the console

### No Tickers Detected
- Make sure tickers are in UPPERCASE
- Tickers must be 1-5 letters
- Check the console for "No tickers found in message"

### Authentication Issues
- Delete the `.wwebjs_auth/` directory and scan the QR code again
- Make sure you're not running multiple instances

## Development

The service logs all incoming messages with their metadata. To debug:

1. Watch the console output for all messages
2. Check which messages pass the filters
3. See which tickers are extracted
4. Monitor the POST requests to Stock Agent

## Notes

- This is a read-only integration - the service never sends messages
- WhatsApp connection must stay active for monitoring
- The service uses Puppeteer in headless mode
- Authentication tokens are cached in `.wwebjs_auth/`
- Multiple tickers in a single message are all processed
