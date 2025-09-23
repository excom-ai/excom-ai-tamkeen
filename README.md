# ExCom AI Chat Application

A modern AI chat application built with React and FastAPI, featuring a beautiful glassmorphism UI and powered by Claude AI.

## Features

- 💬 Real-time AI chat with Claude 3.5 Sonnet
- 🎨 8 customizable themes
- ⚡ Streaming responses support
- 🌐 Markdown rendering
- 💾 Persistent settings across sessions
- 🐳 Docker containerization

## Quick Start

### Using Docker (Recommended)

1. Clone the repository
2. Copy the environment file and add your API key:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. Run with Docker Compose:
```bash
docker-compose up
```

The application will be available at:
- Frontend: http://localhost:3002
- Backend API: http://localhost:9000
- API Docs: http://localhost:9000/docs

### Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend
```bash
npm install
npm start
```

## Environment Variables

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

## Available Themes

- Dark (default)
- Midnight
- Ocean
- Purple
- Forest
- Sunset
- Nord
- Dracula

## Tech Stack

- **Frontend**: React, CSS3 (Glassmorphism)
- **Backend**: FastAPI, LangChain, Anthropic Claude
- **Deployment**: Docker, Docker Compose

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/chat` - Send chat message
- `POST /api/chat/stream` - Stream chat response

## Development

To run in development mode:

```bash
# Backend
cd backend
uvicorn main:app --reload --port 9000

# Frontend
npm start
```