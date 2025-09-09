const { contextBridge, ipcRenderer } = require('electron');

console.log('Preload script starting...');

try {
    contextBridge.exposeInMainWorld('electronAPI', {
        // Bridge control
        startBridge: (config) => ipcRenderer.invoke('start-bridge', config),
        stopBridge: () => ipcRenderer.invoke('stop-bridge'),
        getBridgeStatus: () => ipcRenderer.invoke('get-bridge-status'),
        
        // Manual commands
        sendManualGift: (giftData) => ipcRenderer.invoke('send-manual-gift', giftData),
        spawnSim: (username) => ipcRenderer.invoke('spawn-sim', username),
        
        
        // Dialog functions
        showInfoDialog: (options) => ipcRenderer.invoke('show-info-dialog', options),
        showErrorDialog: (options) => ipcRenderer.invoke('show-error-dialog', options),
        
        // Event listeners
        onLogMessage: (callback) => {
            ipcRenderer.on('log-message', (event, message) => callback(message));
        },
        
        removeAllListeners: (channel) => {
            ipcRenderer.removeAllListeners(channel);
        }
    });
    
    console.log('Preload script completed successfully - electronAPI exposed to main world');
} catch (error) {
    console.error('Error in preload script:', error);
}
