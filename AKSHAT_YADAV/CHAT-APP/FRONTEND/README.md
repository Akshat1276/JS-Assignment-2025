# LLM Chat App - Frontend

A modern web-based chat interface for interacting with Large Language Models through OpenRouter API.

## Features

- **Modern UI**: Clean, responsive design inspired by ChatGPT
- **Multiple Models**: Support for 5 different LLM models
- **Session Management**: Create new chats and browse chat history
- **Real-time Chat**: Instant messaging with typing indicators
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-save**: All conversations are automatically saved

## How to Run

### Prerequisites
- Backend server running on `http://localhost:8000`
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Running the Frontend

1. **Simple Method**: Just open `index.html` in your web browser
   - Double-click the `index.html` file
   - Or right-click and select "Open with browser"

2. **Local Server Method** (recommended for development):
   ```bash
   # Using Python (if you have Python installed)
   python -m http.server 8080
   
   # Or using Node.js live-server (if you have Node.js)
   npx live-server --port=8080
   
   # Then open http://localhost:8080 in your browser
   ```

3. **VS Code Live Server Extension**:
   - Install "Live Server" extension in VS Code
   - Right-click on `index.html` and select "Open with Live Server"

### Backend Setup
Make sure your FastAPI backend is running:
```bash
cd ../BACKEND
uvicorn main:app --reload
```

## File Structure

```
FRONTEND/
├── index.html      # Main HTML structure
├── styles.css      # All CSS styling
├── script.js       # JavaScript functionality
└── README.md       # This file
```

## Features Overview

### Chat Interface
- Clean, modern design with user and AI message bubbles
- Typing indicators when AI is responding
- Auto-scroll to latest messages
- Timestamp for each message

### Model Selection
- Dropdown to choose between 5 LLM models:
  - Mistral 7B Instruct
  - OpenChat 3.5
  - NeuralBeagle 7B
  - Meta LLaMA 3 8B Instruct
  - HuggingFace Zephyr 7B Beta

### Session Management
- Create new chat sessions
- View all previous sessions in sidebar
- Click on any session to load its history
- Sessions are automatically saved in the database

### User Experience
- **Enter key** to send messages
- **Shift+Enter** for new lines
- Auto-resizing text input
- Loading states and error handling
- Connection status indicator
- Mobile-responsive design

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Troubleshooting

### Common Issues

1. **"Failed to connect to backend"**
   - Make sure the backend server is running on `http://localhost:8000`
   - Check if there are any CORS issues in the browser console

2. **Messages not sending**
   - Verify your OpenRouter API key is set in the backend `.env` file
   - Check browser console for JavaScript errors

3. **Sessions not loading**
   - Ensure PostgreSQL database is running
   - Check if the database tables exist

4. **Styling issues**
   - Make sure all three files (HTML, CSS, JS) are in the same directory
   - Check browser console for any file loading errors

### Development Tips

- Open browser Developer Tools (F12) to debug issues
- Check the Network tab for API call failures
- Console tab will show JavaScript errors
- Use the responsive design mode to test mobile layout

## API Endpoints Used

The frontend communicates with these backend endpoints:

- `GET /` - Health check
- `POST /chat/session` - Create new session
- `GET /chat/sessions` - Get all sessions
- `POST /chat` - Send message
- `GET /chat/history` - Get chat history

## Customization

### Styling
Edit `styles.css` to customize:
- Colors and themes
- Layout and spacing
- Animation effects
- Mobile responsiveness

### Functionality
Edit `script.js` to modify:
- API endpoints
- Message formatting
- User interactions
- Error handling

### Layout
Edit `index.html` to change:
- Page structure
- UI components
- Meta tags and title
