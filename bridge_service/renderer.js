// DOM Elements
const elements = {
    // Form inputs
    username: document.getElementById('username'),
    
    // Buttons
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    clearLogBtn: document.getElementById('clear-log-btn'),
    themeToggle: document.getElementById('theme-toggle'),
    
    // Status
    connectionStatus: document.getElementById('connection-status'),
    clientCount: document.getElementById('client-count'),
    currentUser: document.getElementById('current-user'),
    
    
    // Log
    logContainer: document.getElementById('log-container'),
    autoScroll: document.getElementById('auto-scroll')
};

// State
let isConnected = false;
let currentConfig = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Check if electronAPI is available
    if (!window.electronAPI) {
        console.error('Electron API not available - preload script failed to load');
        addLogEntry({
            type: 'error',
            message: 'Electron API not available - application may not function properly',
            timestamp: new Date().toISOString(),
            stack: 'Preload script (preload.js) failed to load or contextBridge.exposeInMainWorld failed'
        });
        return;
    }
    
    console.log('Electron API loaded successfully');
    
    // Initialize theme detection
    initializeThemeDetection();
    
    setupEventListeners();
    updateStatus();
    startStatusPolling();
    
    // Initialize gift configuration
    initializeGiftConfiguration().catch(error => {
        console.error('Failed to initialize gift configuration:', error);
    });
    
    // Load saved username
    loadSavedUsername();
});

function setupEventListeners() {
    // Bridge controls
    elements.startBtn.addEventListener('click', startBridge);
    elements.stopBtn.addEventListener('click', stopBridge);
    
    // Log controls
    elements.clearLogBtn.addEventListener('click', clearLog);
    
    // Theme toggle
    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Listen for log messages from main process
    window.electronAPI.onLogMessage((logMessage) => {
        addLogEntry(logMessage);
    });
}

async function loadSavedUsername() {
    try {
        const result = await window.electronAPI.getLastTikTokUsername();
        if (result.success && result.username) {
            elements.username.value = result.username;
            addLogEntry({
                type: 'info',
                message: `Loaded saved username: ${result.username}`,
                timestamp: new Date().toISOString()
            });
        }
    } catch (error) {
        console.error('Failed to load saved username:', error);
        addLogEntry({
            type: 'warning',
            message: 'Could not load saved username from previous session',
            timestamp: new Date().toISOString()
        });
    }
}

async function startBridge() {
    const username = elements.username.value.trim();
    const port = 8765; // Default port, configurable via config.json
    const manualMode = false;
    
    if (!username && !manualMode) {
        showError('TikTok username is required unless using manual mode');
        return;
    }
    
    // Update UI
    elements.startBtn.disabled = true;
    elements.startBtn.innerHTML = 'Starting... <span class="loading"></span>';
    
    try {
        const config = { username, port, manualMode };
        const result = await window.electronAPI.startBridge(config);
        
        if (result.success) {
            isConnected = true;
            currentConfig = config;
            elements.startBtn.style.display = 'none';
            elements.stopBtn.style.display = 'inline-flex'; // Use inline-flex to match button styling
            elements.stopBtn.disabled = false;
            
            // Update status display
            elements.currentUser.textContent = username || 'Manual Mode';
            
            addLogEntry({
                type: 'success',
                message: result.message,
                timestamp: new Date().toISOString()
            });
            
            showSuccess(result.message);
        } else {
            throw new Error(result.message || 'Failed to start bridge');
        }
    } catch (error) {
        // Update status to error
        elements.connectionStatus.textContent = 'Error';
        elements.connectionStatus.className = 'status-value status-error';
        
        addLogEntry({
            type: 'error',
            message: `Failed to start bridge: ${error.message}`,
            timestamp: new Date().toISOString(),
            stack: error.stack
        });
        
        showError(`Failed to start bridge: ${error.message}`);
    } finally {
        elements.startBtn.disabled = false;
        elements.startBtn.innerHTML = 'Start Bridge';
    }
}

async function stopBridge() {
    elements.stopBtn.disabled = true;
    elements.stopBtn.innerHTML = 'Stopping... <span class="loading"></span>';
    
    try {
        const result = await window.electronAPI.stopBridge();
        
        if (result.success) {
            isConnected = false;
            currentConfig = null;
            elements.startBtn.style.display = 'inline-flex'; // Use inline-flex to match button styling
            elements.stopBtn.style.display = 'none';
            
            // Reset status display
            elements.currentUser.textContent = 'None';
            
            addLogEntry({
                type: 'success',
                message: result.message,
                timestamp: new Date().toISOString()
            });
            
            showSuccess(result.message);
        } else {
            throw new Error(result.message || 'Failed to stop bridge');
        }
    } catch (error) {
        addLogEntry({
            type: 'error',
            message: `Failed to stop bridge: ${error.message}`,
            timestamp: new Date().toISOString(),
            stack: error.stack
        });
        
        showError(`Failed to stop bridge: ${error.message}`);
    } finally {
        elements.stopBtn.disabled = false;
        elements.stopBtn.innerHTML = 'Stop Bridge';
    }
}

function clearLog() {
    elements.logContainer.innerHTML = '';
    addLogEntry({
        type: 'info',
        message: 'Log cleared',
        timestamp: new Date().toISOString()
    });
}

function addLogEntry(logMessage) {
    // Determine log type based on message content
    let logType = logMessage.type;
    
    // Check if this should be a blue info message
    if (logMessage.type === 'manual' || logMessage.type === 'ai') {
        const messageText = logMessage.message;
        if (messageText.includes('🎮 Manually triggering sim creation') ||
            messageText.includes('🤖 AI enabled - analyzing appearance') ||
            messageText.includes('🎨 Starting appearance analysis') ||
            messageText.includes('🔍 Analyzing profile picture') ||
            messageText.includes('📤 Sending sim creation event')) {
            logType = 'info-blue';
        }
    }
    
    const entry = document.createElement('div');
    entry.className = `log-entry log-${logType}`;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    
    // Handle invalid or missing timestamps
    let timeString;
    try {
        const date = logMessage.timestamp ? new Date(logMessage.timestamp) : new Date();
        timeString = date.toLocaleTimeString();
    } catch (error) {
        timeString = new Date().toLocaleTimeString();
    }
    timestamp.textContent = `[${timeString}]`;
    
    const messageContainer = document.createElement('div');
    messageContainer.className = 'log-message-container';
    
    const message = document.createElement('span');
    message.className = 'log-message';
    message.textContent = logMessage.message;
    messageContainer.appendChild(message);
    
    // Add stack trace toggle if available
    if (logMessage.stack && logMessage.type === 'error') {
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'stack-controls';
        
        const toggleButton = document.createElement('button');
        toggleButton.className = 'stack-toggle';
        toggleButton.textContent = 'Show Details';
        toggleButton.onclick = (e) => {
            e.stopPropagation();
            const stackTrace = entry.querySelector('.stack-trace');
            const copyButton = entry.querySelector('.stack-copy');
            const isVisible = stackTrace.style.display !== 'none';
            stackTrace.style.display = isVisible ? 'none' : 'block';
            copyButton.style.display = isVisible ? 'none' : 'inline-block';
            toggleButton.textContent = isVisible ? 'Show Details' : 'Hide Details';
        };
        
        const copyButton = document.createElement('button');
        copyButton.className = 'stack-copy';
        copyButton.textContent = 'Copy';
        copyButton.style.display = 'none';
        copyButton.onclick = async (e) => {
            e.stopPropagation();
            try {
                const fullErrorText = `${logMessage.message}\n\nStack Trace:\n${logMessage.stack}`;
                await navigator.clipboard.writeText(fullErrorText);
                
                // Show feedback
                const originalText = copyButton.textContent;
                copyButton.textContent = 'Copied!';
                copyButton.style.background = 'rgba(52, 199, 89, 0.2)';
                
                setTimeout(() => {
                    copyButton.textContent = originalText;
                    copyButton.style.background = '';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy to clipboard:', err);
                copyButton.textContent = 'Copy Failed';
                setTimeout(() => {
                    copyButton.textContent = 'Copy';
                }, 2000);
            }
        };
        
        const stackTrace = document.createElement('pre');
        stackTrace.className = 'stack-trace';
        stackTrace.textContent = logMessage.stack;
        stackTrace.style.display = 'none';
        
        controlsContainer.appendChild(toggleButton);
        controlsContainer.appendChild(copyButton);
        messageContainer.appendChild(controlsContainer);
        messageContainer.appendChild(stackTrace);
    }
    
    entry.appendChild(timestamp);
    entry.appendChild(messageContainer);
    elements.logContainer.appendChild(entry);
    
    // Auto-scroll if enabled
    if (elements.autoScroll.checked) {
        elements.logContainer.scrollTop = elements.logContainer.scrollHeight;
    }
    
    // Limit log entries to prevent memory issues
    const maxEntries = 1000;
    const entries = elements.logContainer.children;
    if (entries.length > maxEntries) {
        entries[0].remove();
    }
}

async function updateStatus() {
    try {
        const status = await window.electronAPI.getBridgeStatus();
        
        // Update bridge status
        if (status.connected) {
            elements.connectionStatus.textContent = 'Running';
            elements.connectionStatus.className = 'status-value status-running';
            
            // Show stop button, hide start button if bridge is running
            if (!isConnected) {
                elements.startBtn.style.display = 'none';
                elements.stopBtn.style.display = 'inline-flex';
                elements.stopBtn.disabled = false;
            }
        } else {
            elements.connectionStatus.textContent = 'Stopped';
            elements.connectionStatus.className = 'status-value status-stopped';
            
            // Show start button, hide stop button if bridge is stopped
            if (isConnected) {
                elements.startBtn.style.display = 'inline-flex';
                elements.stopBtn.style.display = 'none';
            }
        }
        
        // Update client count
        elements.clientCount.textContent = status.clientCount;
        
        isConnected = status.connected;
    } catch (error) {
        console.error('Failed to update status:', error);
        // Show error status if we can't get status
        elements.connectionStatus.textContent = 'Error';
        elements.connectionStatus.className = 'status-value status-error';
        
        // On error, ensure we show start button and hide stop button
        elements.startBtn.style.display = 'inline-flex';
        elements.stopBtn.style.display = 'none';
        isConnected = false;
    }
}

function startStatusPolling() {
    // Update status every 2 seconds
    setInterval(updateStatus, 2000);
}

// Utility functions for showing messages
function showSuccess(message) {
    // You could implement a toast notification system here
    console.log('SUCCESS:', message);
}

function showInfo(message) {
    // You could implement a toast notification system here
    console.log('INFO:', message);
}

function showError(message) {
    // You could implement a toast notification system here
    console.error('ERROR:', message);
    window.electronAPI.showErrorDialog({
        title: 'Error',
        message: message
    });
}

function showWarning(message) {
    // You could implement a toast notification system here
    console.warn('WARNING:', message);
    window.electronAPI.showInfoDialog({
        type: 'warning',
        title: 'Warning',
        message: message
    });
}

// Gift Configuration Data - Updated from streamtoearn.io/gifts with actual icon URLs
const TIKTOK_GIFTS = [
    // Basic Gifts (1-10 diamonds)
    { name: 'Rose', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/eba3a9bb85c33e017f3648eaf88d7189~tplv-obj.webp', cost: 1, tier: 'basic', id: 'rose' },
    { name: 'Music on Stage', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/d2a59d961490de4c72fed3690e44d1ec.png~tplv-obj.webp', cost: 1, tier: 'basic', id: 'music_on_stage' },
    { name: 'GG', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/3f02fa9594bd1495ff4e8aa5ae265eef~tplv-obj.webp', cost: 1, tier: 'basic', id: 'gg' },
    { name: 'You\'re awesome', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/e9cafce8279220ed26016a71076d6a8a.png~tplv-obj.webp', cost: 1, tier: 'basic', id: 'youre_awesome' },
    { name: 'TikTok', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/802a21ae29f9fae5abe3693de9f874bd~tplv-obj.webp', cost: 1, tier: 'basic', id: 'tiktok' },
    { name: 'Love you so much', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/fc549cf1bc61f9c8a1c97ebab68dced7.png~tplv-obj.webp', cost: 1, tier: 'basic', id: 'love_you_so_much' },
    { name: 'Ice Cream Cone', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/968820bc85e274713c795a6aef3f7c67~tplv-obj.webp', cost: 1, tier: 'basic', id: 'ice_cream_cone' },
    { name: 'Heart Me', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/d56945782445b0b8c8658ed44f894c7b~tplv-obj.webp', cost: 1, tier: 'basic', id: 'heart_me' },
    { name: 'Thumbs Up', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/570a663e27bdc460e05556fd1596771a~tplv-obj.webp', cost: 1, tier: 'basic', id: 'thumbs_up' },
    { name: 'Heart', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/dd300fd35a757d751301fba862a258f1~tplv-obj.webp', cost: 1, tier: 'basic', id: 'heart' },
    { name: 'Cake Slice', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/f681afb4be36d8a321eac741d387f1e2~tplv-obj.webp', cost: 1, tier: 'basic', id: 'cake_slice' },
    { name: 'Glow Stick', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8e1a5d66370c5586545e358e37c10d25~tplv-obj.webp', cost: 1, tier: 'basic', id: 'glow_stick' },
    { name: 'Love you', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/ab0a7b44bfc140923bb74164f6f880ab~tplv-obj.webp', cost: 1, tier: 'basic', id: 'love_you' },
    { name: 'Team Bracelet', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/54cb1eeca369e5bea1b97707ca05d189.png~tplv-obj.webp', cost: 2, tier: 'basic', id: 'team_bracelet' },
    { name: 'Finger Heart', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/a4c4dc437fd3a6632aba149769491f49.png~tplv-obj.webp', cost: 5, tier: 'basic', id: 'finger_heart' },
    { name: 'Popcorn', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/676d2d4c31a8979f1fd06cdf5ecd922f~tplv-obj.webp', cost: 5, tier: 'basic', id: 'popcorn' },
    { name: 'Cheer You Up', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/97e0529ab9e5cbb60d95fc9ff1133ea6~tplv-obj.webp', cost: 9, tier: 'basic', id: 'cheer_you_up' },
    { name: 'Rosa', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/eb77ead5c3abb6da6034d3cf6cfeb438~tplv-obj.webp', cost: 10, tier: 'basic', id: 'rosa' },
    
    // Premium Gifts (20-500 diamonds)
    { name: 'Perfume', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/20b8f61246c7b6032777bb81bf4ee055~tplv-obj.webp', cost: 20, tier: 'premium', id: 'perfume' },
    { name: 'Doughnut', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/4e7ad6bdf0a1d860c538f38026d4e812~tplv-obj.webp', cost: 30, tier: 'premium', id: 'doughnut' },
    { name: 'Paper Crane', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/0f158a08f7886189cdabf496e8a07c21~tplv-obj.webp', cost: 99, tier: 'premium', id: 'paper_crane' },
    { name: 'Little Crown', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/cf3db11b94a975417043b53401d0afe1~tplv-obj.webp', cost: 99, tier: 'premium', id: 'little_crown' },
    { name: 'Game Controller', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/20ec0eb50d82c2c445cb8391fd9fe6e2~tplv-obj.webp', cost: 100, tier: 'premium', id: 'game_controller' },
    { name: 'Confetti', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/cb4e11b3834e149f08e1cdcc93870b26~tplv-obj.webp', cost: 100, tier: 'premium', id: 'confetti' },
    { name: 'Heart Rain', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/be28619d8b8d1dc03f91c7c63e4e0260.png~tplv-obj.webp', cost: 149, tier: 'premium', id: 'heart_rain' },
    { name: 'Love You', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/134e51c00f46e01976399883ca4e4798~tplv-obj.webp', cost: 199, tier: 'premium', id: 'love_you_premium' },
    { name: 'Sunglasses', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/08af67ab13a8053269bf539fd27f3873.png~tplv-obj.webp', cost: 199, tier: 'premium', id: 'sunglasses' },
    { name: 'Sparklers', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/192a873e366e2410da4fa406aba0e0af.png~tplv-obj.webp', cost: 199, tier: 'premium', id: 'sparklers' },
    { name: 'Corgi', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/148eef0884fdb12058d1c6897d1e02b9~tplv-obj.webp', cost: 299, tier: 'premium', id: 'corgi' },
    { name: 'Boxing Gloves', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/9f8bd92363c400c284179f6719b6ba9c~tplv-obj.webp', cost: 299, tier: 'premium', id: 'boxing_gloves' },
    { name: 'Money Gun', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/e0589e95a2b41970f0f30f6202f5fce6~tplv-obj.webp', cost: 500, tier: 'premium', id: 'money_gun' },
    { name: 'VR Goggles', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/18c51791197b413bbd1b4f1b983bda36.png~tplv-obj.webp', cost: 500, tier: 'premium', id: 'vr_goggles' },
    
    // Luxury Gifts (700-5000 diamonds)
    { name: 'Swan', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/97a26919dbf6afe262c97e22a83f4bf1~tplv-obj.webp', cost: 699, tier: 'luxury', id: 'swan' },
    { name: 'Train', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/4227ed71f2c494b554f9cbe2147d4899~tplv-obj.webp', cost: 899, tier: 'luxury', id: 'train' },
    { name: 'Galaxy', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/79a02148079526539f7599150da9fd28.png~tplv-obj.webp', cost: 1000, tier: 'luxury', id: 'galaxy' },
    { name: 'Silver Sports Car', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/f9d784269da31a71e58b10de6fc34cde.png~tplv-obj.webp', cost: 1000, tier: 'luxury', id: 'silver_sports_car' },
    { name: 'Fireworks', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/9494c8a0bc5c03521ef65368e59cc2b8~tplv-obj.webp', cost: 1088, tier: 'luxury', id: 'fireworks' },
    { name: 'Chasing the Dream', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/1ea8dbb805466c4ced19f29e9590040f~tplv-obj.webp', cost: 1500, tier: 'luxury', id: 'chasing_dream' },
    { name: 'Gift Box', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/9cc22f7c8ac233e129dec7b981b91b76~tplv-obj.webp', cost: 1999, tier: 'luxury', id: 'gift_box' },
    { name: 'Baby Dragon', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/733030ca95fe6f757533aec40bf2af3a.png~tplv-obj.webp', cost: 2000, tier: 'luxury', id: 'baby_dragon' },
    { name: 'Motorcycle', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/6517b8f2f76dc75ff0f4f73107f8780e~tplv-obj.webp', cost: 2988, tier: 'luxury', id: 'motorcycle' },
    { name: 'Private Jet', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/921c6084acaa2339792052058cbd3fd3~tplv-obj.webp', cost: 4888, tier: 'luxury', id: 'private_jet' },
    
    // Exclusive Gifts (7000+ diamonds)
    { name: 'Sports Car', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/e7ce188da898772f18aaffe49a7bd7db~tplv-obj.webp', cost: 7000, tier: 'exclusive', id: 'sports_car' },
    { name: 'Luxury Yacht', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/resource/a97ef636c4e0494b2317c58c9edba0a8.png~tplv-obj.webp', cost: 10000, tier: 'exclusive', id: 'luxury_yacht' },
    { name: 'Interstellar', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8520d47b59c202a4534c1560a355ae06~tplv-obj.webp', cost: 10000, tier: 'exclusive', id: 'interstellar' },
    { name: 'Crystal Heart', icon: 'https://p16-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/08095e18ae3da6ad5dcf23ce68eb1483.png~tplv-obj.webp', cost: 14999, tier: 'exclusive', id: 'crystal_heart' },
    { name: 'TikTok Shuttle', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8ef48feba8dd293a75ae9d4376fb17c9~tplv-obj.webp', cost: 20000, tier: 'exclusive', id: 'tiktok_shuttle' },
    { name: 'Phoenix', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/ef248375c4167d70c1642731c732c982~tplv-obj.webp', cost: 25999, tier: 'exclusive', id: 'phoenix' },
    { name: 'Lion', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/4fb89af2082a290b37d704e20f4fe729~tplv-obj.webp', cost: 29999, tier: 'exclusive', id: 'lion' },
    { name: 'TikTok Universe', icon: 'https://p16-webcast.tiktokcdn.com/img/maliva/webcast-va/8f471afbcebfda3841a6cc515e381f58~tplv-obj.webp', cost: 44999, tier: 'exclusive', id: 'tiktok_universe' }
];

const SIMS_INTERACTIONS = [
    { value: 'none', label: 'No Interaction', icon: '🚫' },
    { value: 'create_sim', label: 'Create a Sim', icon: '🧑‍🎨' },
    { value: 'create_dog_sim', label: 'Create a Dog Sim', icon: '🐶' },
    { value: 'friendly_hug', label: 'Friendly Hug', icon: '🤗' },
    { value: 'romantic_hug', label: 'Romantic Hug', icon: '💕' },
    { value: 'romantic_kiss', label: 'Romantic Kiss', icon: '💋' },
    { value: 'flirty_compliment', label: 'Flirty Compliment', icon: '😘' },
    { value: 'friendly_compliment', label: 'Friendly Compliment', icon: '😊' },
    { value: 'tell_joke', label: 'Tell Joke', icon: '😂' },
    { value: 'playful_poke', label: 'Playful Poke', icon: '👉' },
    { value: 'excited_introduction', label: 'Excited Introduction', icon: '🤩' },
    { value: 'dance_together', label: 'Dance Together', icon: '💃' },
    { value: 'take_selfie', label: 'Take Selfie Together', icon: '📸' },
    { value: 'give_gift', label: 'Give Gift', icon: '🎁' },
    { value: 'blow_kiss', label: 'Blow Kiss', icon: '😘' },
    { value: 'wink', label: 'Wink Playfully', icon: '😉' },
    { value: 'high_five', label: 'High Five', icon: '🙌' },
    { value: 'show_off', label: 'Show Off', icon: '✨' },
    { value: 'confident_introduction', label: 'Confident Introduction', icon: '😎' },
    { value: 'passionate_kiss', label: 'Passionate Kiss', icon: '😍' },
    { value: 'woohoo', label: 'WooHoo', icon: '🔥' },
    { value: 'propose', label: 'Propose Marriage', icon: '💍' }
];

// Default gift mappings - Updated for new gift list
const DEFAULT_GIFT_MAPPINGS = {
    // Basic Gifts
    'rose': 'romantic_hug',
    'music_on_stage': 'dance_together',
    'gg': 'excited_introduction',
    'youre_awesome': 'friendly_compliment',
    'tiktok': 'dance_together',
    'love_you_so_much': 'flirty_compliment',
    'ice_cream_cone': 'give_gift',
    'heart_me': 'blow_kiss',
    'thumbs_up': 'friendly_compliment',
    'heart': 'blow_kiss',
    'cake_slice': 'give_gift',
    'glow_stick': 'show_off',
    'love_you': 'flirty_compliment',
    'team_bracelet': 'friendly_hug',
    'finger_heart': 'wink',
    'popcorn': 'tell_joke',
    'cheer_you_up': 'high_five',
    'rosa': 'romantic_hug',
    
    // Premium Gifts
    'perfume': 'flirty_compliment',
    'doughnut': 'give_gift',
    'paper_crane': 'take_selfie',
    'little_crown': 'confident_introduction',
    'game_controller': 'playful_poke',
    'confetti': 'dance_together',
    'heart_rain': 'romantic_kiss',
    'love_you_premium': 'passionate_kiss',
    'sunglasses': 'show_off',
    'sparklers': 'excited_introduction',
    'corgi': 'create_dog_sim',
    'boxing_gloves': 'confident_introduction',
    'money_gun': 'show_off',
    'vr_goggles': 'confident_introduction',
    
    // Luxury Gifts
    'swan': 'romantic_hug',
    'train': 'take_selfie',
    'galaxy': 'create_sim',
    'silver_sports_car': 'show_off',
    'fireworks': 'dance_together',
    'chasing_dream': 'excited_introduction',
    'gift_box': 'give_gift',
    'baby_dragon': 'playful_poke',
    'motorcycle': 'confident_introduction',
    'private_jet': 'woohoo',
    
    // Exclusive Gifts
    'sports_car': 'show_off',
    'luxury_yacht': 'woohoo',
    'interstellar': 'woohoo',
    'crystal_heart': 'propose',
    'tiktok_shuttle': 'woohoo',
    'phoenix': 'passionate_kiss',
    'lion': 'passionate_kiss',
    'tiktok_universe': 'propose'
};

// Gift configuration functionality
let currentGiftMappings = { ...DEFAULT_GIFT_MAPPINGS };

async function initializeGiftConfiguration() {
    await loadGiftConfiguration();
    renderGiftGrid();
    setupGiftConfigurationEvents();
}

function renderGiftGrid() {
    const giftGrid = document.getElementById('gift-grid');
    if (!giftGrid) return;

    giftGrid.innerHTML = '';

    TIKTOK_GIFTS.forEach(gift => {
        const giftItem = createGiftItem(gift);
        giftGrid.appendChild(giftItem);
    });
}

function createGiftItem(gift) {
    const giftItem = document.createElement('div');
    giftItem.className = 'gift-item';
    giftItem.innerHTML = `
        <div class="gift-header">
            <div class="gift-icon">
                <img src="${gift.icon}" alt="${gift.name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
                <span class="fallback-icon" style="display:none;">🎁</span>
            </div>
            <div class="gift-info">
                <h4 class="gift-name">${gift.name} <span class="gift-tier tier-${gift.tier}">${gift.tier}</span></h4>
                <div class="gift-cost">
                    <span class="diamond-icon">💎</span>
                    <span>${gift.cost} diamonds</span>
                </div>
            </div>
            <div class="gift-actions">
                <button class="btn btn-test btn-small" data-gift-id="${gift.id}" title="Test this gift">
                    🧪 Test
                </button>
            </div>
        </div>
        <div class="gift-mapping">
            <label for="mapping-${gift.id}">Sims 4 Interaction:</label>
            <select id="mapping-${gift.id}" data-gift-id="${gift.id}">
                ${SIMS_INTERACTIONS.map(interaction => 
                    `<option value="${interaction.value}" ${currentGiftMappings[gift.id] === interaction.value ? 'selected' : ''}>
                        ${interaction.icon} ${interaction.label}
                    </option>`
                ).join('')}
            </select>
        </div>
    `;

    // Add event listener for mapping changes
    const selectElement = giftItem.querySelector('select');
    selectElement.addEventListener('change', (e) => {
        const giftId = e.target.dataset.giftId;
        const selectedInteraction = e.target.value;
        currentGiftMappings[giftId] = selectedInteraction;
        
        // Log the change (but don't save yet)
        addLogEntry({
            type: 'info',
            message: `🎁 Gift mapping updated: ${gift.name} → ${SIMS_INTERACTIONS.find(i => i.value === selectedInteraction)?.icon || ''} ${SIMS_INTERACTIONS.find(i => i.value === selectedInteraction)?.label || 'Unknown'} (unsaved)`,
            timestamp: new Date().toISOString()
        });
        
        // Mark configuration as having unsaved changes
        markConfigurationAsUnsaved(giftId);
    });

    // Add event listener for test button
    const testButton = giftItem.querySelector('.btn-test');
    testButton.addEventListener('click', (e) => {
        e.preventDefault();
        const giftId = e.target.dataset.giftId;
        testGift(giftId);
    });

    return giftItem;
}

function setupGiftConfigurationEvents() {
    // Save configuration button
    const saveBtn = document.getElementById('save-config-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            if (!hasUnsavedChanges) {
                showInfo('No changes to save.');
                return;
            }
            
            await saveGiftConfiguration();
            showSuccess('Gift configuration saved successfully!');
        });
    }

    // Reset configuration button
    const resetBtn = document.getElementById('reset-config-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to reset all gift mappings to defaults? This cannot be undone.')) {
                resetGiftConfiguration();
                showSuccess('Gift configuration reset to defaults!');
            }
        });
    }
}

async function saveGiftConfiguration(silent = false) {
    try {
        // Save to backend service
        if (window.electronAPI && window.electronAPI.saveGiftMappings) {
            const result = await window.electronAPI.saveGiftMappings(currentGiftMappings);
            if (result && !result.success) {
                throw new Error(result.error || 'Bridge service failed to save gift mappings');
            }
        } else {
            // Fallback to localStorage if backend is not available
            localStorage.setItem('giftMappings', JSON.stringify(currentGiftMappings));
        }
        
        // Mark as saved and update UI
        markConfigurationAsSaved();
        
        // Only log if not silent
        if (!silent) {
            addLogEntry({
                type: 'info',
                message: '💾 Gift configuration saved',
                timestamp: new Date().toISOString()
            });
        }
    } catch (error) {
        console.error('Failed to save gift configuration:', error);
        showError(`Failed to save gift configuration: ${error.message}`);
    }
}

function markConfigurationAsUnsaved(giftId = null) {
    hasUnsavedChanges = true;
    if (giftId) {
        changedGifts.add(giftId);
    }
    updateUnsavedChangesDisplay();
}

function markConfigurationAsSaved() {
    hasUnsavedChanges = false;
    changedGifts.clear();
    updateUnsavedChangesDisplay();
}

function updateUnsavedChangesDisplay() {
    const unsavedLabel = document.getElementById('unsaved-changes-label');
    if (unsavedLabel) {
        const changeCount = changedGifts.size;
        if (hasUnsavedChanges && changeCount > 0) {
            unsavedLabel.textContent = `${changeCount} unsaved change${changeCount !== 1 ? 's' : ''}`;
            unsavedLabel.style.display = 'inline-block';
        } else {
            unsavedLabel.style.display = 'none';
        }
    }
}

async function loadGiftConfiguration() {
    try {
        // Try to load from backend service first
        if (window.electronAPI && window.electronAPI.loadGiftMappings) {
            const result = await window.electronAPI.loadGiftMappings();
            if (result && result.success && result.mappings) {
                currentGiftMappings = { ...DEFAULT_GIFT_MAPPINGS, ...result.mappings };
                addLogEntry({
                    type: 'info',
                    message: '📁 Gift configuration loaded from backend',
                    timestamp: new Date().toISOString()
                });
                
                // Mark as saved since we just loaded from backend
                markConfigurationAsSaved();
                return;
            }
        }
        
        // Fallback to localStorage if backend fails
        const saved = localStorage.getItem('giftMappings');
        if (saved) {
            currentGiftMappings = { ...DEFAULT_GIFT_MAPPINGS, ...JSON.parse(saved) };
            addLogEntry({
                type: 'info',
                message: '📁 Gift configuration loaded from localStorage',
                timestamp: new Date().toISOString()
            });
            
            // Migrate to backend storage
            if (window.electronAPI && window.electronAPI.saveGiftMappings) {
                await window.electronAPI.saveGiftMappings(currentGiftMappings);
                addLogEntry({
                    type: 'info',
                    message: '🔄 Gift configuration migrated to backend storage',
                    timestamp: new Date().toISOString()
                });
            }
        } else {
            currentGiftMappings = { ...DEFAULT_GIFT_MAPPINGS };
        }
        
        // Mark as saved since we just loaded from disk
        markConfigurationAsSaved();
    } catch (error) {
        console.error('Failed to load gift configuration:', error);
        currentGiftMappings = { ...DEFAULT_GIFT_MAPPINGS };
        markConfigurationAsSaved();
        
        addLogEntry({
            type: 'error',
            message: `❌ Failed to load gift configuration: ${error.message}`,
            timestamp: new Date().toISOString()
        });
    }
}

function resetGiftConfiguration() {
    currentGiftMappings = { ...DEFAULT_GIFT_MAPPINGS };
    // Mark all gifts as changed since we reset everything
    TIKTOK_GIFTS.forEach(gift => changedGifts.add(gift.id));
    markConfigurationAsUnsaved();
    renderGiftGrid();
    addLogEntry({
        type: 'info',
        message: '🔄 Gift configuration reset to defaults (unsaved)',
        timestamp: new Date().toISOString()
    });
}

// Export gift mappings for use by bridge service
function getGiftMappings() {
    return currentGiftMappings;
}

// Gift Testing Function
async function testGift(giftId) {
    // Find the gift data
    const gift = TIKTOK_GIFTS.find(g => g.id === giftId);
    if (!gift) {
        showError('Gift not found');
        return;
    }
    
    // Check if bridge is connected
    if (!isConnected) {
        showError('Bridge is not connected. Please start the bridge first.');
        return;
    }
    
    // Generate a test username
    const testUsername = `testuser_${Math.random().toString(36).substring(2, 8)}`;
    
    // Create the gift data in the same format as the manual gift system
    const giftData = {
        username: testUsername,
        giftName: gift.name,
        giftId: gift.id,
        diamondCount: gift.cost,
        giftDisplayName: gift.name,
        tier: gift.tier,
        icon: gift.icon
    };
    
    // Get the mapped Sims interaction for this gift
    const simsInteraction = currentGiftMappings[gift.id] || 'none';
    if (simsInteraction && simsInteraction !== 'none') {
        const interaction = SIMS_INTERACTIONS.find(i => i.value === simsInteraction);
        if (interaction) {
            giftData.simsInteraction = simsInteraction;
            giftData.simsInteractionLabel = interaction.label;
        }
    }
    
    try {
        const result = await window.electronAPI.sendManualGift(giftData);
        
        if (result.success) {
            const interactionText = giftData.simsInteractionLabel ? 
                ` → ${giftData.simsInteractionLabel}` : '';
            
            addLogEntry({
                type: 'success',
                message: `🧪 Test gift sent: ${testUsername} -> ${gift.name} (${gift.cost} 💎)${interactionText}`,
                timestamp: new Date().toISOString()
            });
            
            showSuccess(`Test gift sent: ${gift.name}`);
        } else {
            throw new Error(result.message || 'Failed to send test gift');
        }
    } catch (error) {
        addLogEntry({
            type: 'error',
            message: `Failed to send test gift: ${error.message}`,
            timestamp: new Date().toISOString(),
            stack: error.stack
        });
        
        showError(`Failed to send test gift: ${error.message}`);
    }
}

// Configuration state tracking
let hasUnsavedChanges = false;
let changedGifts = new Set();

// Theme Detection and Management
let currentTheme = 'system'; // 'system', 'light', or 'dark'

function initializeThemeDetection() {
    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme-preference') || 'system';
    currentTheme = savedTheme;
    
    // Apply the theme
    applyTheme(currentTheme);
    
    // Update toggle button
    updateThemeToggleIcon();
    
    // Check for system dark mode preference
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Listen for system theme changes (only relevant when in system mode)
    prefersDarkMode.addEventListener('change', (e) => {
        if (currentTheme === 'system') {
            updateThemeToggleIcon();
        }
    });
}

function toggleTheme() {
    // Cycle through: system -> light -> dark -> system
    switch (currentTheme) {
        case 'system':
            currentTheme = 'light';
            break;
        case 'light':
            currentTheme = 'dark';
            break;
        case 'dark':
            currentTheme = 'system';
            break;
    }
    
    // Apply the new theme
    applyTheme(currentTheme);
    updateThemeToggleIcon();
    
    // Save preference
    localStorage.setItem('theme-preference', currentTheme);
}

function applyTheme(theme) {
    const root = document.documentElement;
    
    if (theme === 'system') {
        // Remove data-theme attribute to let CSS media queries handle it
        root.removeAttribute('data-theme');
    } else {
        // Set explicit theme
        root.setAttribute('data-theme', theme);
    }
}

function getEffectiveTheme() {
    if (currentTheme === 'system') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return currentTheme;
}

function updateThemeToggleIcon() {
    if (!elements.themeToggle) return;
    
    const themeIcon = elements.themeToggle.querySelector('.theme-icon');
    if (!themeIcon) return;
    
    const effectiveTheme = getEffectiveTheme();
    
    // Update icon and tooltip based on current theme and mode
    if (currentTheme === 'system') {
        themeIcon.textContent = effectiveTheme === 'dark' ? '🌙' : '☀️';
        elements.themeToggle.title = `Theme: System (${effectiveTheme}) - Click to switch to Light mode`;
    } else if (currentTheme === 'light') {
        themeIcon.textContent = '☀️';
        elements.themeToggle.title = 'Theme: Light - Click to switch to Dark mode';
    } else {
        themeIcon.textContent = '🌙';
        elements.themeToggle.title = 'Theme: Dark - Click to switch to System mode';
    }
}

// GitHub link functionality
const githubLink = document.getElementById('github-link');
if (githubLink) {
    githubLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.electronAPI && window.electronAPI.openExternal) {
            window.electronAPI.openExternal('https://github.com/ConnorChristie/Sims4TikTokMod');
        }
    });
}

// Handle app close
window.addEventListener('beforeunload', () => {
    window.electronAPI.removeAllListeners('log-message');
});
