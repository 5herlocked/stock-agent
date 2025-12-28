# Stock Agent: Real-Time Market Notifications

## The Problem We Solve

Stock markets move fast, and information is currency. Traditional tracking tools are either overwhelming or insufficient. Stock Agent bridges this gap by delivering precise, timely notifications about market movements directly to your devices.

## How We Built It

Our approach combines robust Python backend infrastructure with real-time messaging technology. By leveraging Robyn's lightweight web framework, Firebase Cloud Messaging, and a modular JavaScript frontend, we've created a notification system that's both powerful and elegant.

The core philosophy is simple: transform complex market data into actionable, immediate insights. No noise, just signal.

## Technical Architecture

The system is built on a carefully chosen technology stack. Python handles backend logic and data processing, providing a stable and flexible foundation. Robyn serves as our web framework, ensuring low-latency communication. Firebase Cloud Messaging acts as our real-time notification conductor, pushing updates across devices with minimal overhead.

Our frontend uses vanilla JavaScript and HTMX, creating an interactive experience without unnecessary complexity. The entire system is managed through UV, ensuring clean and reproducible Python environments.

### Monorepo Structure

This project follows a monorepo architecture with multiple services:

```
stock-agent/
├── src/                    # Python backend (Robyn API, Firebase auth, stock data)
├── services/
│   └── whatsapp/          # Node.js WhatsApp integration service
└── ...
```

### WhatsApp Integration

The WhatsApp integration service monitors specific WhatsApp groups for stock ticker mentions. When configured senders discuss stocks, the system automatically extracts tickers, fetches real-time data from Polygon API, and displays them on the dashboard as "WhatsApp Stock Signals."

This creates a seamless bridge between informal stock discussions and structured market data tracking.

See [services/whatsapp/README.md](services/whatsapp/README.md) for detailed setup instructions.

## Setup and Installation

Setting up Stock Agent is straightforward. Follow these steps precisely:

1. Clone the repository
```bash
git clone [repository-url]
cd stock-agent
```

2. Initialize Python environment
```bash
pip install uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

3. Configure Firebase
- Create a Firebase project
- Generate service account credentials
- Save credentials as `firebase_creds.json`

4. Set environment variables in `.env`
```env
FIREBASE_CREDS_PATH=./firebase-credentials.json
FIREBASE_API_KEY=[your-key]
FIREBASE_PROJECT_ID=[your-project]
```

5. Launch the application
```bash
uv run python -m stock_agent.main
```

6. (Optional) Set up WhatsApp Integration
```bash
cd services/whatsapp
npm install
cp .env.example .env
# Edit .env with your configuration
npm start
```

See the [WhatsApp Integration README](services/whatsapp/README.md) for detailed instructions.

## Notification Strategy

We track two primary market dynamics: gainers and losers. When a stock crosses predefined thresholds, a notification is immediately dispatched. This approach cuts through market noise, delivering only what matters.

## Security Considerations

Security isn't an afterthought—it's fundamental. We implement:
- Dynamic configuration fetching
- Server-side VAPID key management
- Secure token registration protocols

## Contributing

This is an open system. If you see potential improvements, challenge our implementation. Fork the repository, implement your vision, and submit a pull request.

## Disclaimer

Stock markets involve inherent risks. Stock Agent provides information, not financial advice.

## License

MIT License. See [LICENSE](LICENSE) for details.
