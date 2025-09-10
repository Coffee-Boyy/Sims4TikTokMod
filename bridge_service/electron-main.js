import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import TikTokBridgeService from './bridge-service.js';
import UserSettings from './user-settings.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

let mainWindow;
let bridgeService;
let isConnected = false;
let userSettings;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: join(__dirname, 'preload.js'),
            enableRemoteModule: false,
            webSecurity: true
        },
        icon: join(__dirname, 'assets', 'icon.png'),
        title: 'Sims 4 TikTok Bridge',
        show: false
    });

    mainWindow.loadFile('renderer.html');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Add debugging for preload script
    mainWindow.webContents.once('did-finish-load', () => {
        console.log('Renderer process loaded');
        
        // Check if preload script worked
        mainWindow.webContents.executeJavaScript('typeof window.electronAPI')
            .then(result => {
                console.log('electronAPI type in renderer:', result);
                if (result === 'undefined') {
                    console.error('electronAPI not found in renderer - preload script may have failed');
                }
            })
            .catch(err => console.error('Error checking electronAPI:', err));
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    mainWindow.on('closed', () => {
        if (bridgeService) {
            console.log('Main window closed, stopping bridge service...');
            bridgeService.stop();
            bridgeService = null;
        }
        mainWindow = null;
    });

    // Handle window close event before it closes
    mainWindow.on('close', (event) => {
        if (bridgeService) {
            console.log('Main window closing, stopping bridge service...');
            bridgeService.stop();
            bridgeService = null;
        }
    });
}

app.whenReady().then(async () => {
    // Initialize user settings
    userSettings = new UserSettings();
    await userSettings.loadSettings();
    
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (bridgeService) {
        console.log('All windows closed, stopping bridge service...');
        bridgeService.stop();
        bridgeService = null;
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    if (bridgeService) {
        console.log('App quitting, stopping bridge service...');
        bridgeService.stop();
        bridgeService = null;
    }
});

// Handle process termination signals
process.on('SIGINT', () => {
    console.log('Received SIGINT, stopping bridge service...');
    if (bridgeService) {
        bridgeService.stop();
        bridgeService = null;
    }
    app.quit();
});

process.on('SIGTERM', () => {
    console.log('Received SIGTERM, stopping bridge service...');
    if (bridgeService) {
        bridgeService.stop();
        bridgeService = null;
    }
    app.quit();
});

// IPC Handlers
ipcMain.handle('start-bridge', async (event, config) => {
    try {
        if (bridgeService) {
            bridgeService.stop();
        }

        bridgeService = new TikTokBridgeService(
            config.username,
            config.port,
            config.manualMode,
            (logMessage) => {
                // Send log messages to renderer
                mainWindow?.webContents.send('log-message', logMessage);
            }
        );

        if (config.manualMode) {
            bridgeService.startWebSocketServer();
            isConnected = true;
            
            // Save username when bridge starts successfully
            if (config.username && userSettings) {
                await userSettings.saveLastTikTokUsername(config.username);
            }
            
            return { success: true, message: 'Manual mode started successfully' };
        } else {
            bridgeService.setupWebSocketServer();
            await bridgeService.start();
            isConnected = true;
            
            // Save username when bridge starts successfully
            if (config.username && userSettings) {
                await userSettings.saveLastTikTokUsername(config.username);
            }
            
            return { success: true, message: 'Bridge connected successfully' };
        }
    } catch (error) {
        isConnected = false;
        return { success: false, message: error.message };
    }
});

ipcMain.handle('stop-bridge', async () => {
    try {
        if (bridgeService) {
            bridgeService.stop();
            bridgeService = null;
        }
        isConnected = false;
        return { success: true, message: 'Bridge stopped successfully' };
    } catch (error) {
        return { success: false, message: error.message };
    }
});

ipcMain.handle('get-bridge-status', () => {
    return {
        connected: isConnected,
        hasClients: bridgeService ? bridgeService.connectedClients.size > 0 : false,
        clientCount: bridgeService ? bridgeService.connectedClients.size : 0
    };
});

ipcMain.handle('spawn-sim', async (event, username) => {
    try {
        if (!bridgeService) {
            return { success: false, message: 'Bridge service not running' };
        }
        
        await bridgeService.handleManualSpawnCommand(username);
        return { success: true, message: 'Sim spawn triggered successfully' };
    } catch (error) {
        return { success: false, message: error.message };
    }
});


ipcMain.handle('show-info-dialog', async (event, options) => {
    const result = await dialog.showMessageBox(mainWindow, {
        type: options.type || 'info',
        title: options.title || 'Information',
        message: options.message,
        detail: options.detail,
        buttons: options.buttons || ['OK']
    });
    return result;
});

ipcMain.handle('show-error-dialog', async (event, options) => {
    const result = await dialog.showErrorBox(
        options.title || 'Error',
        options.message
    );
    return result;
});

ipcMain.handle('open-external', async (event, url) => {
    try {
        await shell.openExternal(url);
        return { success: true };
    } catch (error) {
        console.error('Failed to open external URL:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('save-gift-mappings', async (event, mappings) => {
    try {
        if (bridgeService) {
            bridgeService.updateGiftMappings(mappings);
        }
        return { success: true };
    } catch (error) {
        console.error('Failed to save gift mappings:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('load-gift-mappings', async (event) => {
    try {
        if (bridgeService) {
            const mappings = bridgeService.getGiftMappings();
            return { success: true, mappings };
        }
        return { success: true, mappings: {} };
    } catch (error) {
        console.error('Failed to load gift mappings:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('send-manual-gift', async (event, giftData) => {
    try {
        if (bridgeService) {
            bridgeService.handleManualGiftCommand(giftData);
            return { success: true, message: `Manual gift sent: ${giftData.giftName}` };
        } else {
            return { success: false, message: 'Bridge service not running' };
        }
    } catch (error) {
        console.error('Failed to send manual gift:', error);
        return { success: false, message: error.message };
    }
});

// User Settings IPC Handlers
ipcMain.handle('get-user-settings', async () => {
    try {
        if (userSettings) {
            return { success: true, settings: userSettings.getAllSettings() };
        } else {
            return { success: false, error: 'User settings not initialized' };
        }
    } catch (error) {
        console.error('Failed to get user settings:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('get-last-tiktok-username', async () => {
    try {
        if (userSettings) {
            const username = userSettings.getLastTikTokUsername();
            return { success: true, username: username };
        } else {
            return { success: false, error: 'User settings not initialized' };
        }
    } catch (error) {
        console.error('Failed to get last TikTok username:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('save-user-setting', async (event, key, value) => {
    try {
        if (userSettings) {
            await userSettings.set(key, value);
            return { success: true };
        } else {
            return { success: false, error: 'User settings not initialized' };
        }
    } catch (error) {
        console.error('Failed to save user setting:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('reset-user-settings', async () => {
    try {
        if (userSettings) {
            await userSettings.resetToDefaults();
            return { success: true };
        } else {
            return { success: false, error: 'User settings not initialized' };
        }
    } catch (error) {
        console.error('Failed to reset user settings:', error);
        return { success: false, error: error.message };
    }
});
