// DOM Elements
const elements = {
    // Form inputs
    username: document.getElementById('username'),
    manualMode: document.getElementById('manual-mode'),
    
    // Buttons
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    spawnSimBtn: document.getElementById('spawn-sim-btn'),
    sendGiftBtn: document.getElementById('send-gift-btn'),
    clearLogBtn: document.getElementById('clear-log-btn'),
    
    // Status
    connectionStatus: document.getElementById('connection-status'),
    clientCount: document.getElementById('client-count'),
    currentUser: document.getElementById('current-user'),
    
    // Manual commands
    manualCommandsPanel: document.getElementById('manual-commands-panel'),
    spawnUsername: document.getElementById('spawn-username'),
    giftUsername: document.getElementById('gift-username'),
    giftName: document.getElementById('gift-name'),
    diamondCount: document.getElementById('diamond-count'),
    
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
    setupEventListeners();
    updateStatus();
    startStatusPolling();
});

function setupEventListeners() {
    // Bridge controls
    elements.startBtn.addEventListener('click', startBridge);
    elements.stopBtn.addEventListener('click', stopBridge);
    
    // Manual commands
    elements.spawnSimBtn.addEventListener('click', spawnSim);
    elements.sendGiftBtn.addEventListener('click', sendGift);
    
    // Log controls
    elements.clearLogBtn.addEventListener('click', clearLog);
    
    // Manual mode toggle
    elements.manualMode.addEventListener('change', (e) => {
        elements.manualCommandsPanel.style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Listen for log messages from main process
    window.electronAPI.onLogMessage((logMessage) => {
        addLogEntry(logMessage);
    });
}

async function startBridge() {
    const username = elements.username.value.trim();
    const port = 8765; // Default port, configurable via config.json
    const manualMode = elements.manualMode.checked;
    
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
            elements.stopBtn.style.display = 'inline-block';
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
            elements.startBtn.style.display = 'inline-block';
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


async function spawnSim() {
    const username = elements.spawnUsername.value.trim();
    
    if (!username) {
        showError('Please enter a username for sim spawning');
        return;
    }
    
    if (!isConnected) {
        showError('Bridge is not connected');
        return;
    }
    
    elements.spawnSimBtn.disabled = true;
    elements.spawnSimBtn.innerHTML = 'Spawning... <span class="loading"></span>';
    
    try {
        const result = await window.electronAPI.spawnSim(username);
        
        if (result.success) {
            addLogEntry({
                type: 'success',
                message: `🎮 Sim spawn triggered for: ${username}`,
                timestamp: new Date().toISOString()
            });
            
            showSuccess(`Sim spawn triggered for ${username}`);
            elements.spawnUsername.value = '';
        } else {
            throw new Error(result.message || 'Failed to spawn sim');
        }
    } catch (error) {
        addLogEntry({
            type: 'error',
            message: `Failed to spawn sim: ${error.message}`,
            timestamp: new Date().toISOString(),
            stack: error.stack
        });
        
        showError(`Failed to spawn sim: ${error.message}`);
    } finally {
        elements.spawnSimBtn.disabled = false;
        elements.spawnSimBtn.innerHTML = 'Spawn Sim';
    }
}

async function sendGift() {
    const username = elements.giftUsername.value.trim();
    const giftName = elements.giftName.value;
    const diamondCount = parseInt(elements.diamondCount.value) || 0;
    
    if (!username) {
        showError('Please enter a username for gift sending');
        return;
    }
    
    if (!isConnected) {
        showError('Bridge is not connected');
        return;
    }
    
    elements.sendGiftBtn.disabled = true;
    elements.sendGiftBtn.innerHTML = 'Sending... <span class="loading"></span>';
    
    try {
        const result = await window.electronAPI.sendManualGift({
            username,
            giftName,
            diamondCount
        });
        
        if (result.success) {
            addLogEntry({
                type: 'success',
                message: `🎁 Test gift sent: ${username} -> ${giftName} (${diamondCount} diamonds)`,
                timestamp: new Date().toISOString()
            });
            
            showSuccess(`Test gift sent: ${giftName} from ${username}`);
            elements.giftUsername.value = '';
        } else {
            throw new Error(result.message || 'Failed to send gift');
        }
    } catch (error) {
        addLogEntry({
            type: 'error',
            message: `Failed to send gift: ${error.message}`,
            timestamp: new Date().toISOString(),
            stack: error.stack
        });
        
        showError(`Failed to send gift: ${error.message}`);
    } finally {
        elements.sendGiftBtn.disabled = false;
        elements.sendGiftBtn.innerHTML = 'Send Gift';
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
    timestamp.textContent = `[${new Date(logMessage.timestamp).toLocaleTimeString()}]`;
    
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
        } else {
            elements.connectionStatus.textContent = 'Stopped';
            elements.connectionStatus.className = 'status-value status-stopped';
        }
        
        // Update client count
        elements.clientCount.textContent = status.clientCount;
        
        isConnected = status.connected;
    } catch (error) {
        console.error('Failed to update status:', error);
        // Show error status if we can't get status
        elements.connectionStatus.textContent = 'Error';
        elements.connectionStatus.className = 'status-value status-error';
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

// Handle app close
window.addEventListener('beforeunload', () => {
    window.electronAPI.removeAllListeners('log-message');
});
