// Frontend Configuration for TOBI Chat Interface
const CONFIG = {
    // API Configuration
    API_BASE_URL: 'http://localhost:8000',  // Backend API URL
    
    // UI Configuration
    CHAT_CONFIG: {
        TYPING_DELAY: 1000,           // Delay before showing typing indicator
        MESSAGE_ANIMATION_DELAY: 300,  // Animation delay for messages
        SCROLL_DELAY: 100,            // Delay before scrolling to bottom
        HEALTH_CHECK_INTERVAL: 30000, // Health check interval in ms
    },
    
    // Chat Suggestions
    SUGGESTIONS: [
        "I'm looking for a new phone",
        "Show me iPhone deals",
        "I need unlimited data",
        "What's the best Android phone?"
    ],
    
    // Environment Configuration
    ENVIRONMENT: 'development',  // development, staging, production
    
    // Debug Configuration
    DEBUG: true,  // Enable debug logging
};

// Environment-specific configurations
const ENVIRONMENT_CONFIGS = {
    development: {
        API_BASE_URL: 'http://localhost:8000',
        DEBUG: true,
    },
    staging: {
        API_BASE_URL: 'https://staging-api.example.com',
        DEBUG: false,
    },
    production: {
        API_BASE_URL: 'https://api.example.com',
        DEBUG: false,
    }
};

// Apply environment-specific config
if (ENVIRONMENT_CONFIGS[CONFIG.ENVIRONMENT]) {
    Object.assign(CONFIG, ENVIRONMENT_CONFIGS[CONFIG.ENVIRONMENT]);
}

// Make config available globally
window.TOBI_CONFIG = CONFIG;

// Debug logging function
window.debugLog = function(message, ...args) {
    if (CONFIG.DEBUG) {
        console.log('[TOBI Debug]:', message, ...args);
    }
};

// Export for module systems (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} 