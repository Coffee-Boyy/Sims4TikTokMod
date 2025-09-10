import { writeFile, readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { app } from 'electron';

class UserSettings {
    constructor() {
        // Use Electron's userData directory for storing user settings
        this.userDataPath = app.getPath('userData');
        this.settingsDir = join(this.userDataPath, 'settings');
        this.settingsFile = join(this.settingsDir, 'user-settings.json');
        
        // Default settings
        this.defaultSettings = {
            lastTikTokUsername: '',
            windowBounds: null,
            theme: 'system',
            autoScroll: true,
            lastUsed: null
        };
        
        this.settings = { ...this.defaultSettings };
    }
    
    async ensureSettingsDirectory() {
        try {
            if (!existsSync(this.settingsDir)) {
                await mkdir(this.settingsDir, { recursive: true });
                console.log(`Created settings directory: ${this.settingsDir}`);
            }
        } catch (error) {
            console.error('Failed to create settings directory:', error);
            throw error;
        }
    }
    
    async loadSettings() {
        try {
            await this.ensureSettingsDirectory();
            
            if (existsSync(this.settingsFile)) {
                const data = await readFile(this.settingsFile, 'utf8');
                const loadedSettings = JSON.parse(data);
                
                // Merge with defaults to handle new settings
                this.settings = { ...this.defaultSettings, ...loadedSettings };
                
                console.log('User settings loaded successfully');
                console.log('Last TikTok username:', this.settings.lastTikTokUsername || 'None');
            } else {
                console.log('No existing settings file found, using defaults');
                this.settings = { ...this.defaultSettings };
            }
        } catch (error) {
            console.error('Failed to load user settings:', error);
            // Fallback to defaults if loading fails
            this.settings = { ...this.defaultSettings };
        }
        
        return this.settings;
    }
    
    async saveSettings() {
        try {
            await this.ensureSettingsDirectory();
            
            // Add timestamp for last update
            this.settings.lastUsed = new Date().toISOString();
            
            const data = JSON.stringify(this.settings, null, 2);
            await writeFile(this.settingsFile, data, 'utf8');
            
            console.log('User settings saved successfully');
        } catch (error) {
            console.error('Failed to save user settings:', error);
            throw error;
        }
    }
    
    // Get a specific setting
    get(key) {
        return this.settings[key];
    }
    
    // Set a specific setting
    async set(key, value) {
        this.settings[key] = value;
        await this.saveSettings();
    }
    
    // Get the last used TikTok username
    getLastTikTokUsername() {
        return this.settings.lastTikTokUsername || '';
    }
    
    // Save the last used TikTok username
    async saveLastTikTokUsername(username) {
        if (username && username.trim()) {
            this.settings.lastTikTokUsername = username.trim();
            await this.saveSettings();
            console.log(`Saved last TikTok username: ${username}`);
        }
    }
    
    // Get all settings
    getAllSettings() {
        return { ...this.settings };
    }
    
    // Reset settings to defaults
    async resetToDefaults() {
        this.settings = { ...this.defaultSettings };
        await this.saveSettings();
        console.log('User settings reset to defaults');
    }
    
    // Get settings file path (for debugging)
    getSettingsPath() {
        return this.settingsFile;
    }
}

export default UserSettings;
