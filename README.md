# Stock Agent: Real-Time Market Notifications

## The Problem We Solve

Stock markets move fast, and information is currency. Traditional tracking tools are either overwhelming or insufficient. Stock Agent bridges this gap by delivering precise, timely notifications about market movements directly to your devices.

## How We Built It

Our approach combines robust Python backend infrastructure with real-time messaging technology. By leveraging Robyn's lightweight web framework, Firebase Cloud Messaging, and a modular JavaScript frontend, we've created a notification system that's both powerful and elegant.

The core philosophy is simple: transform complex market data into actionable, immediate insights. No noise, just signal.

## Technical Architecture

The system is built on a carefully chosen technology stack. Python handles backend logic and data processing, providing a stable and flexible foundation. Robyn serves as our web framework, ensuring low-latency communication. Firebase Cloud Messaging acts as our real-time notification conductor, pushing updates across devices with minimal overhead.

Our frontend uses vanilla JavaScript and HTMX, creating an interactive experience without unnecessary complexity. The entire system is managed through UV, ensuring clean and reproducible Python environments.

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
- Save credentials as `firebase-credentials.json`

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
