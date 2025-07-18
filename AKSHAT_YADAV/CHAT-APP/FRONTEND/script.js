class ChatApp {
    constructor() {
        this.API_URL = 'http://localhost:8000';
        this.currentSessionId = null;
        this.currentModel = 'mistralai/mistral-7b-instruct';
        this.isTyping = false;
        this.sessions = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.initialize();
    }

    initializeElements() {
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.errorToast = document.getElementById('error-toast');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.modelSelect = document.getElementById('model-select');
        this.currentModelSpan = document.getElementById('current-model');
        this.sessionsList = document.getElementById('sessions-list');
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.connectionStatus = document.getElementById('connection-status');
    }

    setupEventListeners() {
        this.newChatBtn.addEventListener('click', () => this.createNewSession());
        this.modelSelect.addEventListener('change', (e) => {
            this.currentModel = e.target.value;
            this.updateModelDisplay();
        });
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.messageInput.addEventListener('focus', () => {
            this.messageInput.parentElement.classList.add('focused');
        });
        this.messageInput.addEventListener('blur', () => {
            this.messageInput.parentElement.classList.remove('focused');
        });
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
        const toastClose = document.querySelector('.toast-close');
        toastClose.addEventListener('click', () => this.hideError());
    }

    async initialize() {
        try {
            this.showLoading('Connecting to backend...');
            await this.testConnection();
            console.log('Backend connection successful');
            this.updateConnectionStatus(true);
            this.enableInterface();
            try {
                await this.loadSessions();
                console.log('Sessions loaded:', this.sessions.length);
                if (this.sessions.length == 0) {
                    console.log('Please Create a new session');
                    await this.createNewSession();
                } else {
                    console.log('Loading most recent session');
                    await this.selectSession(this.sessions[0]);
                }
            } catch (sessionError) {
                console.warn('Session loading failed, creating new session:', sessionError);
                await this.createNewSession();
            }
            
            console.log('Initialization complete');
            
        } catch (error) {
            console.error('Backend connection failed:', error);
            this.showError('Failed to connect to backend. Please make sure the server is running.');
            this.updateConnectionStatus(false);
            this.enableInterface();
        } finally {
            this.hideLoading();
        }
    }
    async testConnection() {
        const response = await fetch(`${this.API_URL}/`);
        if (!response.ok) {
            throw new Error('Backend connection failed');
        }
        return response.json();
    }
    async loadSessions() {
        try {
            const response = await fetch(`${this.API_URL}/chat/sessions`);
            if (!response.ok) throw new Error('Failed to load sessions');
            
            const data = await response.json();
            this.sessions = data.sessions || [];
            this.renderSessions();
            
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    async createNewSession() {
        try {
            console.log('Creating new session...');
            const response = await fetch(`${this.API_URL}/chat/session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            });
            
            if (!response.ok) throw new Error('Failed to create session');
            
            const data = await response.json();
            this.currentSessionId = data.session_id;
            console.log('New session created:', this.currentSessionId);
            this.sessions.unshift(data.session_id);
            this.renderSessions();
            this.clearMessages();
            this.showWelcomeMessage();
        } catch (error) {
            console.error('Failed to create session:', error);
            this.showError('Failed to create new chat session');
        }
    }
    async selectSession(sessionId) {
        try {
            this.currentSessionId = sessionId;
            this.renderSessions();
            await this.loadChatHistory(sessionId);
        } catch (error) {
            console.error('Failed to select session:', error);
            this.showError('Failed to load chat history');
        }
    }
    async loadChatHistory(sessionId) {
        try {
            const response = await fetch(`${this.API_URL}/chat/history?session_id=${sessionId}`);
            if (!response.ok) throw new Error('Failed to load history');
            
            const data = await response.json();
            this.renderMessages(data.history || []);
        } catch (error) {
            console.error('Failed to load chat history:', error);
            this.showError('Failed to load chat history');
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping || !this.currentSessionId) return;
        
        try {
            this.isTyping = true;
            this.updateSendButton(false);
            this.addMessage('user', message);
            this.messageInput.value = '';
            this.autoResizeTextarea();
            this.showTypingIndicator();
            const response = await fetch(`${this.API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    model: this.currentModel,
                    message: message,
                }),
            });
            
            if (!response.ok) throw new Error('Failed to send message');
            
            const data = await response.json();
            this.hideTypingIndicator();
            this.addMessage('assistant', data.response);
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.hideTypingIndicator();
            this.showError('Failed to send message. Please try again.');
        } finally {
            this.isTyping = false;
            this.updateSendButton(true);
        }
    }
    renderSessions() {
        this.sessionsList.innerHTML = '';   
        this.sessions.forEach(sessionId => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            if (sessionId == this.currentSessionId) {
                sessionItem.classList.add('active');
            }
            sessionItem.innerHTML = `
                <div>Chat Session</div>
                <div class="session-id">${sessionId.substring(0, 8)}...</div>
            `;
            
            sessionItem.addEventListener('click', () => this.selectSession(sessionId));
            this.sessionsList.appendChild(sessionItem);
        });
    }

    renderMessages(messages) {
        this.clearMessages();
        
        if (messages.length === 0) {
            this.showWelcomeMessage();
            return;
        }
        
        messages.forEach(message => {
            this.addMessage(message.role, message.content, false);
        });
    }

    addMessage(role, content, animate = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        if (animate) messageDiv.style.animation = 'slideIn 0.3s ease';
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(content)}
            </div>
            <div class="message-time">${time}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        return content.replace(/\n/g, '<br>');
    }
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    clearMessages() {
        this.chatMessages.innerHTML = '';
    }
    showWelcomeMessage() {
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <h3>LLM Chat</h3>
                <p>Select a model and start chatting. Your conversations are automatically saved.</p>
            </div>
        `;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    autoResizeTextarea() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    updateModelDisplay() {
        const modelName = this.modelSelect.options[this.modelSelect.selectedIndex].text;
        this.currentModelSpan.textContent = modelName;
    }

    updateSendButton(enabled) {
        this.sendBtn.disabled = !enabled;
        this.messageInput.disabled = !enabled;
    }

    updateConnectionStatus(connected) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (connected) {
            statusDot.classList.remove('disconnected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
        }
    }

    enableInterface() {
        this.messageInput.disabled = false;
        this.sendBtn.disabled = false;
        this.newChatBtn.disabled = false;
        this.modelSelect.disabled = false;
    }

    showLoading(message = 'Loading...') {
        this.loadingOverlay.querySelector('p').textContent = message;
        this.loadingOverlay.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingOverlay.classList.add('hidden');
    }

    showError(message) {
        const toastMessage = this.errorToast.querySelector('.toast-message');
        toastMessage.textContent = message;
        this.errorToast.classList.add('show');
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    hideError() {
        this.errorToast.classList.remove('show');
    }
}
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
