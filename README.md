# ExCom AI Tamkeen Assistant

An intelligent AI chat assistant built for Tamkeen, featuring Microsoft Azure Active Directory authentication and powered by Claude AI. This modern web application provides a clean, professional interface for AI-powered conversations with advanced features like streaming responses and markdown rendering.

## Features

- 🔐 **Secure Authentication** - Microsoft Entra (Azure AD) integration
- 💬 **Real-time AI Chat** - Powered by Claude 3.5 Sonnet with streaming responses
- 🎨 **Modern UI** - Clean, professional dark theme optimized for readability
- 📝 **Rich Text Support** - Full markdown rendering with syntax highlighting
- 🌐 **HTML Preview** - Interactive HTML rendering for code blocks
- 🔧 **Tool Integration** - Support for AI tool calls and function execution
- 📱 **Responsive Design** - Mobile-friendly interface
- 🚀 **Production Ready** - Docker containerization and cloud deployment support

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Microsoft Azure AD tenant for authentication
- Anthropic API key for Claude AI

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/excom-ai/excom-ai-tamkeen.git
cd excom-ai-tamkeen
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
# Backend
ANTHROPIC_API_KEY=your_anthropic_api_key
AZURE_CLIENT_ID=your_azure_client_id
AZURE_TENANT_ID=your_azure_tenant_id

# Frontend (React)
REACT_APP_CLIENT_ID=your_azure_client_id
REACT_APP_TENANT_ID=your_azure_tenant_id
```

### Running with Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the deployment script
./deploy-direct.sh
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Installation

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend Setup
```bash
npm install --legacy-peer-deps
npm start
```

## Deployment

### Google Cloud Run

1. Build and push to Google Container Registry:
```bash
./deploy.sh
```

2. Or use Cloud Build:
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Docker Hub

```bash
./deploy-dockerhub.sh
```

## Architecture

```
excom-ai-tamkeen/
├── backend/              # FastAPI backend
│   ├── main.py          # Application entry point
│   ├── routes/          # API endpoints
│   └── requirements.txt # Python dependencies
├── src/                 # React frontend
│   ├── components/      # React components
│   │   ├── Chat.js     # Main chat interface
│   │   ├── AuthProvider.js # Azure AD auth
│   │   └── EnhancedMarkdown.js # Markdown renderer
│   └── ExcomApp.js     # Main application
├── public/             # Static assets
├── Dockerfile          # Container configuration
└── docker-compose.yml  # Multi-container setup
```

## API Endpoints

- `GET /api/health` - Health check endpoint
- `POST /api/chat` - Send chat message (non-streaming)
- `POST /api/chat/stream` - Stream chat response with SSE
- `GET /api` - API information

## Security Features

- Azure Active Directory authentication
- Secure token handling
- CORS configuration
- Environment variable management
- No secrets in version control

## Technologies

### Frontend
- React 19
- Azure MSAL for authentication
- React Markdown with syntax highlighting
- Server-Sent Events for streaming

### Backend
- FastAPI
- LangChain
- Anthropic Claude AI
- Python 3.9+

### Infrastructure
- Docker & Docker Compose
- Google Cloud Run
- GitHub Actions (CI/CD ready)

## Development

### Running Tests
```bash
# Frontend tests
npm test

# Backend tests
cd backend
pytest
```

### Code Quality
```bash
# Frontend linting
npm run lint

# Backend formatting
black backend/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential.

## Support

For issues and questions, please contact the ExCom AI team or create an issue in the GitHub repository.

---

Built with ❤️ by ExCom AI for Tamkeen