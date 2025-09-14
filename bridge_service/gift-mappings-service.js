import { writeFile, readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { app } from 'electron';
import { DEFAULT_GIFT_MAPPINGS } from './gift-mappings.js';

class GiftMappingsService {
    constructor() {
        // Use Electron's userData directory for storing gift mappings
        this.userDataPath = app.getPath('userData');
        this.settingsDir = join(this.userDataPath, 'settings');
        this.mappingsFile = join(this.settingsDir, 'gift-mappings.json');
        this.defaultMappings = DEFAULT_GIFT_MAPPINGS;
        this.mappings = { ...this.defaultMappings };
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
    
    async loadMappings() {
        try {
            await this.ensureSettingsDirectory();
            
            if (existsSync(this.mappingsFile)) {
                const data = await readFile(this.mappingsFile, 'utf8');
                const loadedMappings = JSON.parse(data);
                
                // Merge with defaults to handle new mappings
                this.mappings = { ...this.defaultMappings, ...loadedMappings };
                
                console.log('Gift mappings loaded successfully');
                console.log(`Loaded ${Object.keys(this.mappings).length} gift mappings`);
            } else {
                console.log('No existing gift mappings file found, using defaults');
                this.mappings = { ...this.defaultMappings };
                
                // Save defaults to file
                await this.saveMappings();
            }
        } catch (error) {
            console.error('Failed to load gift mappings:', error);
            // Fallback to defaults if loading fails
            this.mappings = { ...this.defaultMappings };
        }
        
        return this.mappings;
    }
    
    async saveMappings() {
        try {
            await this.ensureSettingsDirectory();
            
            const data = JSON.stringify(this.mappings, null, 2);
            await writeFile(this.mappingsFile, data, 'utf8');
            
            console.log('Gift mappings saved successfully');
        } catch (error) {
            console.error('Failed to save gift mappings:', error);
            throw error;
        }
    }
    
    // Get a specific mapping
    get(giftKey) {
        return this.mappings[giftKey];
    }
    
    // Set a specific mapping
    async set(giftKey, interaction) {
        this.mappings[giftKey] = interaction;
        await this.saveMappings();
    }
    
    // Update multiple mappings at once
    async updateMappings(newMappings) {
        this.mappings = { ...newMappings };
        await this.saveMappings();
        console.log(`Updated ${Object.keys(newMappings).length} gift mappings`);
    }
    
    // Get all mappings
    getAllMappings() {
        return { ...this.mappings };
    }
    
    // Reset mappings to defaults
    async resetToDefaults() {
        this.mappings = { ...this.defaultMappings };
        await this.saveMappings();
        console.log('Gift mappings reset to defaults');
        return this.mappings;
    }
    
    // Remove a specific mapping
    async remove(giftKey) {
        if (this.mappings.hasOwnProperty(giftKey)) {
            delete this.mappings[giftKey];
            await this.saveMappings();
            console.log(`Removed gift mapping for: ${giftKey}`);
        }
    }
    
    // Get mappings file path (for debugging)
    getMappingsPath() {
        return this.mappingsFile;
    }
    
    // Check if a gift has a mapping
    hasMapping(giftKey) {
        return this.mappings.hasOwnProperty(giftKey);
    }
    
    // Get mapping keys
    getMappingKeys() {
        return Object.keys(this.mappings);
    }
    
    // Get mapping count
    getMappingCount() {
        return Object.keys(this.mappings).length;
    }
}

export default GiftMappingsService;
