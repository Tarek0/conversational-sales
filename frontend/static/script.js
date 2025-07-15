// Get configuration from config file
const CONFIG = window.TOBI_CONFIG || {
    API_BASE_URL: 'http://localhost:8000',
    CHAT_CONFIG: {
        TYPING_DELAY: 1000,
        MESSAGE_ANIMATION_DELAY: 300,
        SCROLL_DELAY: 100,
        HEALTH_CHECK_INTERVAL: 30000,
    },
    SUGGESTIONS: [
        "I'm looking for a new phone",
        "Show me iPhone deals", 
        "I need unlimited data",
        "What's the best Android phone?"
    ],
    DEBUG: true
};

const API_BASE_URL = CONFIG.API_BASE_URL;

class ChatManager {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.initializeElements();
        this.attachEventListeners();
        this.isLoading = false;
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.recommendationsPanel = document.getElementById('recommendationsPanel');
        this.recommendationsGrid = document.getElementById('recommendationsGrid');
        this.inputSuggestions = document.getElementById('inputSuggestions');
    }

    attachEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input suggestions
        this.inputSuggestions.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-button')) {
                this.messageInput.value = e.target.textContent;
                this.sendMessage();
            }
        });

        // Auto-resize input
        this.messageInput.addEventListener('input', () => {
            this.updateSendButton();
        });

        this.updateSendButton();
    }

    updateSendButton() {
        const hasMessage = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasMessage || this.isLoading;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Clear input
        this.messageInput.value = '';
        this.updateSendButton();

        // Add user message to chat
        this.addMessage(message, 'user');

        // Show loading indicator
        this.showLoading();

        try {
            // Send message to API
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Add bot response to chat
            this.addMessage(data.response, 'bot');

            // Display recommendations if any
            if (data.recommendations && data.recommendations.length > 0) {
                this.displayRecommendations(data.recommendations);
            }

        } catch (error) {
            window.debugLog('Error sending message:', error);
            this.addMessage('I apologize, but I encountered an error connecting to the server. Please try again.', 'bot');
        } finally {
            this.hideLoading();
        }
    }

    addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'bot' ? '🤖' : '👤';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        messageBubble.innerHTML = this.formatMessage(message);

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.formatTime(new Date());

        messageContent.appendChild(messageBubble);
        messageContent.appendChild(messageTime);

        messageElement.appendChild(avatar);
        messageElement.appendChild(messageContent);

        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    formatMessage(message) {
        // Basic formatting for links and line breaks
        return message
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    displayRecommendations(recommendations) {
        this.recommendationsGrid.innerHTML = '';
        
        recommendations.forEach(product => {
            const card = this.createRecommendationCard(product);
            this.recommendationsGrid.appendChild(card);
        });

        this.recommendationsPanel.style.display = 'block';
        this.scrollToBottom();
    }

    createRecommendationCard(product) {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        card.onclick = () => window.open(product.url, '_blank');

        card.innerHTML = `
            <h4>${product.name}</h4>
            <div class="recommendation-details">
                <span class="recommendation-price">${product.monthly_cost}</span>
                <span class="recommendation-brand">${product.brand}</span>
            </div>
            <div class="recommendation-features">
                <strong>Data:</strong> ${product.data_allowance}<br>
                <strong>Storage:</strong> ${product.storage}<br>
                <strong>Contract:</strong> ${product.contract_length}
            </div>
            ${product.features.length > 0 ? `<div class="recommendation-features">
                <strong>Features:</strong> ${product.features.slice(0, 3).join(', ')}
            </div>` : ''}
        `;

        return card;
    }

    showLoading() {
        this.isLoading = true;
        this.loadingIndicator.style.display = 'flex';
        this.updateSendButton();
    }

    hideLoading() {
        this.isLoading = false;
        this.loadingIndicator.style.display = 'none';
        this.updateSendButton();
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, CONFIG.CHAT_CONFIG.SCROLL_DELAY);
    }
}

// Health check functionality
class HealthMonitor {
    constructor() {
        this.statusIndicator = document.querySelector('.status-indicator');
        this.statusText = document.querySelector('.status-text');
        this.checkInterval = CONFIG.CHAT_CONFIG.HEALTH_CHECK_INTERVAL;
        this.init();
    }

    init() {
        this.checkHealth();
        setInterval(() => this.checkHealth(), this.checkInterval);
    }

    async checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (response.ok) {
                this.updateStatus('online');
            } else {
                this.updateStatus('offline');
            }
        } catch (error) {
            this.updateStatus('offline');
        }
    }

    updateStatus(status) {
        if (status === 'online') {
            this.statusIndicator.style.background = '#48bb78';
            this.statusText.textContent = 'Online';
        } else {
            this.statusIndicator.style.background = '#f56565';
            this.statusText.textContent = 'Offline';
        }
    }
}

// API Client for additional functionality
class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
    }

    async getProductCount() {
        try {
            const response = await fetch(`${this.baseUrl}/products/count`);
            return await response.json();
        } catch (error) {
            window.debugLog('Error fetching product count:', error);
            return null;
        }
    }

    async getBrands() {
        try {
            const response = await fetch(`${this.baseUrl}/products/brands`);
            return await response.json();
        } catch (error) {
            window.debugLog('Error fetching brands:', error);
            return null;
        }
    }

    async triggerScraping() {
        try {
            const response = await fetch(`${this.baseUrl}/scrape`, {
                method: 'POST'
            });
            return await response.json();
        } catch (error) {
            window.debugLog('Error triggering scraping:', error);
            return null;
        }
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        font-weight: 500;
        z-index: 1001;
        animation: slideIn 0.3s ease-out;
    `;
    
    if (type === 'error') {
        notification.style.background = '#f56565';
    } else if (type === 'success') {
        notification.style.background = '#48bb78';
    } else {
        notification.style.background = '#667eea';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Add necessary CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    const chatManager = new ChatManager();
    const healthMonitor = new HealthMonitor();
    const apiClient = new ApiClient();
    
    // Make API client globally available
    window.apiClient = apiClient;
    
    // Welcome message after a short delay
    setTimeout(() => {
        showNotification('Welcome to TOBI! I\'m here to help you find the perfect phone.', 'success');
    }, 1000);
    
    // Check if backend is available
    fetch(`${API_BASE_URL}/health`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Backend not available');
            }
        })
        .catch(error => {
            showNotification('Backend API is not available. Please start the backend server.', 'error');
        });
}); 