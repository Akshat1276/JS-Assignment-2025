# LLM Chat Application

A full-stack chat application that allows users to interact with multiple Large Language Models (LLMs) through a clean, responsive web interface. The application supports multiple chat sessions, model selection, and persistent conversation history.

## Features

- 🤖 **Multiple LLM Models**: Support for 5 different models via OpenRouter API
  - Mistral 7B Instruct
  - OpenChat 3.5
  - NeuralBeagle 14B
  - Meta LLaMA 3.1 8B
  - HuggingFace Zephyr 7B

- 💬 **Session Management**: Create, switch between, and manage multiple chat sessions
- 🔄 **Persistent History**: Conversations are saved and can be resumed
- ⚡ **Real-time Chat**: Instant messaging with typing indicators
- 📱 **Responsive Design**: Clean, modern UI that works on all devices
- 🔌 **Connection Monitoring**: Real-time backend connection status
- 🎨 **Clean Interface**: Simple, distraction-free design

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Robust relational database for data persistence
- **OpenRouter API**: Access to multiple LLM models
- **Pydantic**: Data validation and settings management
- **CORS**: Cross-Origin Resource Sharing support

### Frontend
- **Vanilla JavaScript**: No frameworks, pure JS for maximum performance
- **HTML5 & CSS3**: Modern web standards
- **Responsive Design**: Mobile-first approach

## Prerequisites

Before setting up the application, ensure you have the following installed:

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 12+**: [Download PostgreSQL](https://www.postgresql.org/download/)
- **Git**: [Download Git](https://git-scm.com/downloads/)
- **OpenRouter API Key**: [Get API Key](https://openrouter.ai/keys)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Akshat1276/JS-Assignment-2025.git
cd JS-Assignment-2025/AKSHAT_YADAV/CHAT-APP
```

### 2. Database Setup

#### Start PostgreSQL Service
```bash
# Windows (Command Prompt as Administrator)
net start postgresql-x64-12

# macOS (using Homebrew)
brew services start postgresql

# Linux (Ubuntu/Debian)
sudo systemctl start postgresql
```

#### Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE llm_chat_db;

# Create user (optional, for security)
CREATE USER chat_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE llm_chat_db TO chat_user;

# Exit PostgreSQL
\q
```

### 3. Backend Setup

#### Navigate to Backend Directory
```bash
cd BACKEND
```

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in the `BACKEND` directory:

```bash
# Copy the example and edit
cp .env.example .env
```

Edit the `.env` file with your configurations:

```properties
# Database Configuration
POSTGRES_URL=postgresql://postgres:user123@localhost:5432/llm_chat_db

# OpenRouter API Configuration  
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Note: Replace 'your_openrouter_api_key_here' with your actual OpenRouter API key
# You can get an API key from: https://openrouter.ai/keys
```

**Important**: Replace the following values:
- `user123`: Your PostgreSQL password
- `your_openrouter_api_key_here`: Your actual OpenRouter API key

#### Initialize Database Tables
```bash
python -c "from db import init_db; init_db()"
```

### 4. Frontend Setup

#### Navigate to Frontend Directory
```bash
cd ../FRONTEND
```

The frontend uses vanilla JavaScript and doesn't require any build process or dependencies.

## Running the Application

### 1. Start the Backend Server

```bash
# Navigate to backend directory (if not already there)
cd BACKEND

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`

### 2. Start the Frontend

#### Option A: Using Live Server (Recommended)
If you have VS Code with Live Server extension:
1. Open the `FRONTEND` folder in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"

#### Option B: Using Python HTTP Server
```bash
# Navigate to frontend directory
cd FRONTEND

# Start a simple HTTP server
# Python 3
python -m http.server 3000

# Python 2 (if you have it)
python -m SimpleHTTPServer 3000
```

#### Option C: Using Node.js (if you have it)
```bash
# Install a simple HTTP server globally
npm install -g http-server

# Navigate to frontend directory
cd FRONTEND

# Start the server
http-server -p 3000
```

The frontend will be available at: `http://localhost:3000`

## API Endpoints

### Backend API Documentation

Once the backend is running, you can access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/chat/session` | Create new chat session |
| GET | `/chat/sessions` | Get all chat sessions |
| POST | `/chat` | Send message to LLM |
| GET | `/chat/history` | Get chat history for session |

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `OPENROUTER_API_KEY` | OpenRouter API key | `sk-or-v1-...` |

### Model Configuration

The application supports these models (configured in `models/openrouter.py`):

1. **mistralai/mistral-7b-instruct** - Fast and efficient
2. **openchat/openchat-3.5-1210** - Great for conversations
3. **cognitivecomputations/dolphin-2.6-mixtral-8x7b** - High quality responses
4. **meta-llama/llama-3.1-8b-instruct** - Meta's latest model
5. **huggingfaceh4/zephyr-7b-beta** - Fine-tuned for helpfulness

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: could not connect to server: Connection refused
```
**Solution**: Make sure PostgreSQL is running and the connection string in `.env` is correct.

#### 2. Missing API Key Error
```
Error: OpenRouter API key not found
```
**Solution**: Ensure you have set `OPENROUTER_API_KEY` in your `.env` file.

#### 3. CORS Error in Browser
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```
**Solution**: The backend already includes CORS middleware. Make sure the backend is running on port 8000.

#### 4. Virtual Environment Issues
```
'venv' is not recognized as an internal or external command
```
**Solution**: 
- Windows: Use `python -m venv venv` instead of `venv`
- Make sure Python is in your PATH

#### 5. Port Already in Use
```
Error: [Errno 48] Address already in use
```
**Solution**: Either stop the process using the port or use a different port:
```bash
# Use different port
uvicorn main:app --reload --port 8001
```

### Debug Mode

To run the backend in debug mode with detailed logging:

```bash
uvicorn main:app --reload --log-level debug
```

### Database Reset

If you need to reset the database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Drop and recreate database
DROP DATABASE llm_chat_db;
CREATE DATABASE llm_chat_db;

# Exit and reinitialize
\q
python -c "from db import init_db; init_db()"
```

## Development

### Project Structure
```
CHAT-APP/
├── BACKEND/
│   ├── main.py              # FastAPI application
│   ├── db.py                # Database connection and models
│   ├── models/
│   │   └── openrouter.py    # LLM model integration
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables
│   ├── .gitignore          # Git ignore rules
│   └── venv/               # Virtual environment
├── FRONTEND/
│   ├── index.html          # Main HTML file
│   ├── script.js           # JavaScript application
│   ├── styles.css          # CSS styles
│   └── .gitignore          # Git ignore rules
└── README.md               # This file
```

### Adding New Models

To add a new LLM model:

1. Edit `models/openrouter.py`
2. Add the model to the `AVAILABLE_MODELS` dictionary
3. Update the frontend model selector in `index.html`
