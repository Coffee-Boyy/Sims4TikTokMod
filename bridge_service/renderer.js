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
let simsInteractions = null;
let tiktokGifts = null;

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

    window.electronAPI.getInteractions().then(interactions => {
        simsInteractions = interactions;
    });
    window.electronAPI.getGifts().then(gifts => {
        tiktokGifts = gifts;
    });
    
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

// Gift configuration functionality
let currentGiftMappings = {};

async function initializeGiftConfiguration() {
    await loadGiftConfiguration();
    renderGiftGrid();
    setupGiftConfigurationEvents();
}

function renderGiftGrid() {
    const giftGrid = document.getElementById('gift-grid');
    if (!giftGrid) return;

    giftGrid.innerHTML = '';

    tiktokGifts.forEach(gift => {
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
                ${simsInteractions.map(interaction => 
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
            message: `🎁 Gift mapping updated: ${gift.name} → ${simsInteractions.find(i => i.value === selectedInteraction)?.icon || ''} ${simsInteractions.find(i => i.value === selectedInteraction)?.label || 'Unknown'} (unsaved)`,
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
        resetBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to reset all gift mappings to defaults? This cannot be undone.')) {
                await resetGiftConfiguration();
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
                currentGiftMappings = result.mappings;
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

        // Mark as saved since we just loaded from disk
        markConfigurationAsSaved();
    } catch (error) {
        console.error('Failed to load gift configuration:', error);
        currentGiftMappings = {};
        markConfigurationAsSaved();
        
        addLogEntry({
            type: 'error',
            message: `❌ Failed to load gift configuration: ${error.message}`,
            timestamp: new Date().toISOString()
        });
    }
}

async function resetGiftConfiguration() {
    const result = await window.electronAPI.resetGiftMappings();
    currentGiftMappings = result;
    // Mark all gifts as changed since we reset everything
    tiktokGifts.forEach(gift => changedGifts.add(gift.id));
    markConfigurationAsUnsaved();
    renderGiftGrid();
    addLogEntry({
        type: 'info',
        message: '🔄 Gift configuration reset to defaults (unsaved)',
        timestamp: new Date().toISOString()
    });
}

// Gift Testing Function
async function testGift(giftId) {
    // Find the gift data
    const gift = tiktokGifts.find(g => g.id === giftId);
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
        const interaction = simsInteractions.find(i => i.value === simsInteraction);
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
