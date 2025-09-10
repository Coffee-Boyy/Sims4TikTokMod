#!/usr/bin/env node
/**
 * TikTok Live Bridge Service for Sims 4 Mod (Node.js)
 * Connects to TikTok Live stream and forwards gift events to Sims 4 mod via WebSocket
 */

import { WebSocket, WebSocketServer } from 'ws';
import { TikTokLiveConnection } from 'tiktok-live-connector';
import config from './config.json' with { type: 'json' };
import axios from 'axios';
import readline from 'readline';
import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const Appearance = z.object({
    hair_color: z.enum(['blonde', 'brown', 'black', 'red', 'gray', 'white', 'dark_brown', 'light_brown', 'auburn', 'ginger', 'platinum']),
    skin_tone: z.string(),
    eye_color: z.enum(['blue', 'brown', 'green', 'hazel', 'gray']),
    gender: z.enum(['male', 'female']),
    age: z.enum(['young_adult', 'adult', 'elder']),
    hair_style: z.enum(['short', 'medium', 'long', 'bald']),
    confidence: z.number().min(0).max(1),
  });

class TikTokBridgeService {
    constructor(tiktokUsername, websocketPort = 8765, manualMode = false) {
        this.tiktokUsername = tiktokUsername;
        this.websocketPort = websocketPort;
        this.connectedClients = new Set();
        this.manualMode = manualMode;
        
        // Rate limiting
        this.lastSentTime = 0;
        this.minInterval = 2000; // 2 seconds in milliseconds
        this.maxEventsPerMinute = 10;
        this.eventsThisMinute = 0;
        this.minuteStartTime = Date.now();
        
        // AI Analysis configuration
        this.aiApiKey = config.aiAnalysis?.openaiApiKey;
        this.aiModel = config.aiAnalysis?.model || 'gpt-5-mini';
        this.aiTimeout = config.aiAnalysis?.timeout || 30000;
        this.aiEnabled = config.aiAnalysis?.enabled !== false && !!this.aiApiKey;
        
        if (this.aiEnabled) {
            this.openai = new OpenAI({
                apiKey: this.aiApiKey,
                timeout: this.aiTimeout
            });
        }
        
        // Diamond tracking configuration
        this.diamondThreshold = config.diamondTracking?.threshold || 5;
        this.diamondTimeout = config.diamondTracking?.timeout || 3600; // 1 hour
        this.diamondTrackers = new Map(); // Track diamond accumulation per user
        
        // Profile picture configuration
        this.profilePicturesEnabled = config.profilePictures?.enabled !== false;
        this.useWebScraping = config.profilePictures?.useWebScraping !== false;
        this.useTikTokLiveConnector = config.profilePictures?.useTikTokLiveConnector !== false;
        this.fallbackToGenerated = config.profilePictures?.fallbackToGenerated !== false;
        
        if (!manualMode) {
            // Initialize TikTok connection only in normal mode
            this.tiktokConnection = new TikTokLiveConnection(tiktokUsername, {
                enableExtendedGiftInfo: true,
                enableWebsocketUpgrade: true,
                requestPollingIntervalMs: 1000,
                sessionId: null,
                clientParams: {},
                requestHeaders: {},
                websocketHeaders: {},
                requestOptions: {},
                websocketOptions: {}
            });
            
            this.setupTikTokEvents();
        }
        
        // WebSocket server is set up separately in startWebSocketServer() for manual mode
        // or in setupWebSocketServer() for normal mode
        
        // Start cleanup interval for expired diamond trackers
        this.startDiamondTrackerCleanup();
    }
    
    setupTikTokEvents() {
        console.log(`🔗 Setting up TikTok Live connection for: @${this.tiktokUsername}`);
        
        // Connection events
        this.tiktokConnection.on('connected', (state) => {
            const roomId = state?.roomId || state?.roomInfo?.roomId || 'unknown';
            const viewerCount = state?.viewerCount || state?.roomInfo?.viewerCount || 'unknown';
            console.log(`✅ Connected to TikTok Live! Room ID: ${roomId}`);
            console.log(`👥 ${viewerCount} viewers watching`);
        });
        
        this.tiktokConnection.on('disconnected', () => {
            console.warn('⚠️  Disconnected from TikTok Live stream');
        });
        
        this.tiktokConnection.on('error', (err) => {
            // Check if this is just a fallback warning, not a fatal error
            const isWarning = err?.info && err.info.includes('falling back');
            
            if (isWarning) {
                console.warn('⚠️  TikTok connection warning:', err.info);
            } else {
                const errorMessage = err?.message || err?.toString?.() || JSON.stringify(err) || 'Unknown error';
                console.error('❌ TikTok connection error:', errorMessage);
                this.handleTikTokError(err);
            }
        });
        
        // Gift events - this is what we're interested in for the Sims 4 mod
        this.tiktokConnection.on('gift', (data) => {
            this.processGiftEvent(data);
        });
        
        // Optional: Log other events for debugging
        this.tiktokConnection.on('chat', (data) => {
            if (process.argv.includes('--verbose')) {
                const username = data.uniqueId || data.user?.uniqueId || 'unknown';
                const message = data.comment || data.message || 'no message';
                console.log(`💬 ${username}: ${message}`);
            }
        });
        
        this.tiktokConnection.on('like', (data) => {
            const username = data.uniqueId || data.user?.uniqueId || 'unknown';
            const count = data.likeCount || data.count || data.totalLikeCount || 'unknown';
            
            if (process.argv.includes('--verbose')) {
                console.log(`❤️  ${username} liked (${count} total)`);
            }
            
            // Forward like events to Sims 4 mod
            this.processLikeEvent(data);
        });
        
        this.tiktokConnection.on('follow', (data) => {
            if (process.argv.includes('--verbose')) {
                const username = data.uniqueId || data.user?.uniqueId || 'unknown';
                console.log(`➕ ${username} followed!`);
            }
        });
    }
    
    setupWebSocketServer() {
        console.log(`🌐 Setting up WebSocket server on port ${this.websocketPort}`);
        
        this.wss = new WebSocketServer({ 
            port: this.websocketPort,
            host: '127.0.0.1'  // Explicitly bind to IPv4 localhost
        });
        
        this.wss.on('connection', (ws, request) => {
            const clientInfo = `${request.socket.remoteAddress}:${request.socket.remotePort}`;
            console.log(`🎮 Sims 4 mod connected: ${clientInfo}`);
            
            this.connectedClients.add(ws);
            
            // Send welcome message
            ws.send(JSON.stringify({
                type: 'connection',
                message: `Connected to TikTok Live bridge for @${this.tiktokUsername}`,
                timestamp: new Date().toISOString()
            }));
            
            ws.on('message', (message) => {
                if (process.argv.includes('--verbose')) {
                    console.log(`📨 Received from ${clientInfo}: ${message}`);
                }
                // Handle any messages from Sims 4 mod if needed
            });
            
            ws.on('close', () => {
                console.log(`👋 Sims 4 mod disconnected: ${clientInfo}`);
                this.connectedClients.delete(ws);
            });
            
            ws.on('error', (error) => {
                console.error(`❌ WebSocket error for ${clientInfo}:`, error.message);
                this.connectedClients.delete(ws);
            });
        });
        
        this.wss.on('listening', () => {
            console.log(`✅ WebSocket server listening on localhost:${this.websocketPort}`);
        });
    }
    
    processGiftEvent(data) {
        // Debug: Log full gift event structure if --debug flag is used
        if (process.argv.includes('--debug')) {
            console.log('🔍 Full Gift Event Structure:', JSON.stringify(data, null, 2));
        }
        
        const currentTime = Date.now();
        
        // Reset minute counter if needed
        if (currentTime - this.minuteStartTime >= 60000) {
            this.eventsThisMinute = 0;
            this.minuteStartTime = currentTime;
        }
        
        // Check rate limits
        const username = data.user?.uniqueId || data.uniqueId || 'unknown';
        if (currentTime - this.lastSentTime < this.minInterval || 
            this.eventsThisMinute >= this.maxEventsPerMinute) {
            console.log(`⏱️  Rate limited: Skipping gift from ${username}`);
            return;
        }
        
        // Update rate limiting counters
        this.lastSentTime = currentTime;
        this.eventsThisMinute++;
        
        // Create event payload for Sims 4 mod - using actual API structure
        const giftName = data.giftDetails?.giftName || data.extendedGiftInfo?.name || data.giftName || 'unknown';
        const repeatCount = data.repeatCount || data.comboCount || data.groupCount || 1;
        const giftId = data.giftId || data.giftDetails?.id || data.extendedGiftInfo?.id || 0;
        const diamondCount = data.giftDetails?.diamondCount || data.extendedGiftInfo?.diamond_count || 0;
        
        // Extract profile picture URL from user data
        const profilePictureUrl = data.user?.avatarThumb?.urlList?.[0] || 
                                 data.user?.avatarMedium?.urlList?.[0] || 
                                 data.user?.avatarLarger?.urlList?.[0] || 
                                 null;

        const payload = {
            type: 'gift',
            user: username,
            gift: giftName.toLowerCase(),
            giftDisplayName: giftName, // Keep original case for display
            value: repeatCount,
            giftId: giftId,
            diamondCount: diamondCount,
            description: data.giftDetails?.describe || data.extendedGiftInfo?.describe || '',
            profilePictureUrl: profilePictureUrl,
            timestamp: new Date().toISOString()
        };
        
        // Process diamond tracking
        if (diamondCount > 0) {
            this.processDiamondTracking(username, diamondCount, profilePictureUrl)
                .then(result => {
                    if (result) {
                        payload.diamondTracking = result;
                        console.log(`💎 Diamond tracking for ${username}:`, result);
                    }
                    
                    // If this gift has diamonds and a profile picture, analyze the appearance
                    if (profilePictureUrl && this.aiEnabled) {
                        return this.analyzeUserAppearance(username);
                    }
                    return null;
                })
                .then(appearanceData => {
                    if (appearanceData) {
                        payload.appearanceAnalysis = appearanceData;
                        console.log(`🎨 Analyzed appearance for ${username}:`, appearanceData);
                    }
                    // Send the payload with all data
                    this.broadcastToClients(payload);
                })
                .catch(error => {
                    console.error(`❌ Error processing gift for ${username}:`, error.message);
                    // Send payload without additional data
                    this.broadcastToClients(payload);
                });
        } else {
            // Send payload immediately if no diamonds
            this.broadcastToClients(payload);
        }
        
        console.log(`🎁 Processing gift: ${payload.user} sent "${payload.giftDisplayName}" (x${payload.value}) [${payload.diamondCount} 💎]`);
        
        // Debug logging in verbose mode
        if (process.argv.includes('--verbose')) {
            console.log(`   📊 Gift Details:`, {
                id: payload.giftId,
                diamonds: payload.diamondCount,
                description: payload.description
            });
        }
    }
    
    async processDiamondTracking(username, diamondCount, profilePictureUrl) {
        try {
            const currentTime = Date.now() / 1000; // Convert to seconds
            
            // Initialize or update tracker for this user
            if (!this.diamondTrackers.has(username)) {
                this.diamondTrackers.set(username, {
                    totalDiamonds: 0,
                    firstGiftTime: currentTime,
                    lastGiftTime: currentTime,
                    profilePictureUrl: profilePictureUrl,
                    simCreated: false
                });
            }
            
            const tracker = this.diamondTrackers.get(username);
            tracker.totalDiamonds += diamondCount;
            tracker.lastGiftTime = currentTime;
            
            // Update profile picture URL if provided
            if (profilePictureUrl) {
                tracker.profilePictureUrl = profilePictureUrl;
            }
            
            console.log(`💎 User ${username} now has ${tracker.totalDiamonds} accumulated diamonds`);
            
            // Check if threshold reached
            if (tracker.totalDiamonds >= this.diamondThreshold && !tracker.simCreated) {
                tracker.simCreated = true;
                console.log(`🎉 Diamond threshold reached for ${username}! Triggering sim creation...`);
                
                return {
                    totalDiamonds: tracker.totalDiamonds,
                    thresholdReached: true,
                    shouldCreateSim: true,
                    timeRemaining: this.diamondTimeout - (currentTime - tracker.firstGiftTime)
                };
            }
            
            // Return current status
            return {
                totalDiamonds: tracker.totalDiamonds,
                thresholdReached: false,
                shouldCreateSim: false,
                timeRemaining: this.diamondTimeout - (currentTime - tracker.firstGiftTime)
            };
            
        } catch (error) {
            console.error(`❌ Error processing diamond tracking for ${username}:`, error.message);
            return null;
        }
    }
    
    getProfilePictureUrl(username) {
        // return "https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/d94b9222ec1d97f4245acc9b860b417e~tplv-tiktokx-cropcenter:1080:1080.jpeg?dr=9640&refresh_token=19c901a3&x-expires=1757372400&x-signature=HdmRsI286XGuH8vgk%2FdJBJsRFjY%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5";
        return "https://p19-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/96342a004e5b15067605aeb18c70faf1~tplv-tiktokx-cropcenter:1080:1080.jpeg?dr=9640&refresh_token=6f355dd4&x-expires=1757368800&x-signature=EdaetmYBWIdwSWQiZRx9SKYY43I%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5";
    }
    
    async analyzeUserAppearance(username) {
        try {
            console.log(`🎨 Starting appearance analysis for ${username}...`);
            
            // Get profile picture URL
            const profilePictureUrl = this.getProfilePictureUrl(username);
            if (!profilePictureUrl) {
                console.warn(`⚠️ No profile picture available for ${username}, using defaults`);
                return this.getDefaultAppearance();
            }
            
            // Analyze the profile picture
            const appearanceData = await this.analyzeProfilePicture(profilePictureUrl, username);
            if (!appearanceData) {
                console.warn(`⚠️ AI analysis failed for ${username}, using defaults`);
                return this.getDefaultAppearance();
            }
            
            return appearanceData;
            
        } catch (error) {
            console.error(`❌ Error in appearance analysis for ${username}:`, error.message);
            return this.getDefaultAppearance();
        }
    }
    
    getDefaultAppearance() {
        return {
            hair_color: 'brown',
            skin_tone: 'medium',
            eye_color: 'brown',
            gender: 'male',
            age: 'adult',
            hair_style: 'short',
            confidence: 0.0
        };
    }

    async analyzeProfilePicture(profilePictureUrl, username) {
        try {
            console.log(`🔍 Analyzing profile picture for ${username}...`);
            
            if (!this.openai) {
                console.warn(`⚠️ OpenAI client not initialized for ${username}`);
                return null;
            }
            
            // Download the profile picture
            const imageResponse = await axios.get(profilePictureUrl, {
                responseType: 'arraybuffer',
                timeout: 10000
            });
            
            // Convert to base64
            const imageBase64 = Buffer.from(imageResponse.data).toString('base64');
            
            // Prepare the AI prompt
            const prompt = `Analyze this profile picture and determine the person's appearance attributes for creating a Sims 4 character.

Please respond with a JSON object containing the following attributes:
{
    "hair_color": "blonde|brown|light_brown|dark_brown|black|red|auburn|ginger|platinum|gray|white",
    "skin_tone": "very_light|light|fair|medium|tan|olive|brown|dark|very_dark", 
    "eye_color": "blue|brown|green|hazel|gray",
    "gender": "male|female",
    "age": "young_adult|adult|elder",
    "hair_style": "short|medium|long|bald",
    "confidence": 0.0-1.0
}

If you cannot determine an attribute, use reasonable defaults.`;
            
            // Call OpenAI API using the new Responses API
            const response = await this.openai.responses.parse({
                model: this.aiModel,
                input: [
                    {
                        role: 'user',
                        content: [
                            { type: 'input_text', text: prompt },
                            {
                                type: 'input_image',
                                image_url: `data:image/jpeg;base64,${imageBase64}`
                            }
                        ]
                    }
                ],
                text: {
                    format: zodTextFormat(Appearance, "appearance"),
                },
            });
            const content = response.output_parsed;
            return content;
        } catch (error) {
            console.error(`❌ Error analyzing profile picture for ${username}:`, error.message);
            return null;
        }
    }
    
    processLikeEvent(data) {
        const currentTime = Date.now();
        
        // Reset minute counter if needed
        if (currentTime - this.minuteStartTime >= 60000) {
            this.eventsThisMinute = 0;
            this.minuteStartTime = currentTime;
        }
        
        // Extract username from data
        const username = data.user?.uniqueId || data.uniqueId || 'unknown';
        
        // No rate limiting for likes - let Sims 4 mod handle accumulation
        
        // Create event payload for Sims 4 mod
        const likeCount = data.likeCount || data.count || data.totalLikeCount || 1;
        
        const payload = {
            type: 'like',
            user: username,
            likeCount: likeCount,
            timestamp: new Date().toISOString()
        };
        
        console.log(`❤️  Processing like: ${payload.user} liked (${payload.likeCount} total)`);
        
        // Send to all connected Sims 4 mod clients
        this.broadcastToClients(payload);
    }
    
    broadcastToClients(payload) {
        if (this.connectedClients.size === 0) {
            console.warn('⚠️  No Sims 4 mod clients connected');
            return;
        }
        
        const message = JSON.stringify(payload);
        const disconnectedClients = new Set();
        
        this.connectedClients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                try {
                    client.send(message);
                    if (process.argv.includes('--verbose')) {
                        console.log(`📤 Sent to client: ${message}`);
                    }
                } catch (error) {
                    console.error('❌ Error sending to client:', error.message);
                    disconnectedClients.add(client);
                }
            } else {
                disconnectedClients.add(client);
            }
        });
        
        // Remove disconnected clients
        disconnectedClients.forEach(client => {
            this.connectedClients.delete(client);
        });
    }
    
    handleTikTokError(error) {
        console.error('🔍 DEBUGGING TIPS:');
        
        // Safely get error message
        const errorMessage = error?.message || error?.toString?.() || JSON.stringify(error) || 'Unknown error';
        const errorMessageLower = errorMessage.toLowerCase();
        
        if (errorMessageLower.includes('live has ended') || errorMessageLower.includes('not found') || errorMessageLower.includes('room not exist')) {
            console.error(`   1. Check if @${this.tiktokUsername} is currently LIVE streaming`);
            console.error(`   2. Verify the username '${this.tiktokUsername}' exists on TikTok`);
            console.error('   3. The user must be actively live streaming (not just having an account)');
            console.error('   4. Try a different username that you know is currently live');
        } else if (errorMessageLower.includes('rate limit') || errorMessageLower.includes('429')) {
            console.error('   🔍 Rate limit detected - TikTok may be blocking requests');
            console.error('   Try again in a few minutes');
        } else if (errorMessageLower.includes('network') || errorMessageLower.includes('enotfound') || errorMessageLower.includes('connection')) {
            console.error('   🔍 Network connection issue detected');
            console.error('   Check your internet connection and firewall settings');
        } else if (errorMessageLower.includes('undefined') || !errorMessage || errorMessage === 'Unknown error') {
            console.error('   🔍 Connection failed - likely causes:');
            console.error(`   1. @${this.tiktokUsername} is NOT currently live streaming`);
            console.error('   2. Username does not exist on TikTok');
            console.error('   3. TikTok may be blocking the connection');
            console.error('   4. Try a different username that you know is currently live');
        } else {
            console.error(`   🔍 Unexpected error: ${errorMessage}`);
            console.error(`   1. @${this.tiktokUsername} may not be live streaming`);
            console.error('   2. Try a different username');
        }
        
        console.error('⚠️  Note: This service only works when the TikTok user is actively live streaming!');
    }
    
    async start() {
        console.log('🚀 Starting TikTok Bridge Service...');
        console.log(`   TikTok Username: ${this.tiktokUsername}`);
        console.log(`   WebSocket Port: ${this.websocketPort}`);
        console.log(`   AI Analysis: ${this.aiEnabled ? '✅ Enabled' : '❌ Disabled'}`);
        if (this.aiEnabled) {
            console.log(`   AI Model: ${this.aiModel}`);
        }
        console.log(`   Diamond Tracking: ✅ Enabled (threshold: ${this.diamondThreshold}, timeout: ${this.diamondTimeout}s)`);
        console.log('   Press Ctrl+C to stop');
        console.log('--------------------------------------------------');
        
        try {
            console.log('🔗 Attempting to connect to TikTok Live...');
            
            // Connect to TikTok Live
            const state = await this.tiktokConnection.connect();
            console.log(`🎉 Successfully connected! Room ID: ${state?.roomId || 'unknown'}`);
            console.log(`👥 Viewer count: ${state?.viewerCount || 'unknown'}`);
            
        } catch (error) {
            console.error('❌ Failed to connect to TikTok Live:', error);
            console.error('❌ Error type:', typeof error);
            console.error('❌ Error keys:', error ? Object.keys(error) : 'no keys');
            this.handleTikTokError(error);
            process.exit(1);
        }
    }
    
    startWebSocketServer() {
        console.log('🌐 Starting WebSocket server for manual mode...');
        this.setupWebSocketServer();
        console.log(`✅ WebSocket server running on port ${this.websocketPort}`);
        console.log('🎮 Ready to receive connections from Sims 4 mod!');
    }

    startManualCommandInterface() {
        console.log('\n🎮 Manual Command Interface Activated!');
        console.log('Available commands:');
        console.log('  spawn <username>     - Manually trigger sim creation for a user');
        console.log('  gift <username> <gift> <diamonds> - Send a test gift event');
        console.log('  help                - Show this help message');
        console.log('  exit                - Exit the program');
        console.log('\nType a command and press Enter:');
        
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            prompt: '> '
        });
        
        rl.prompt();
        
        rl.on('line', (input) => {
            const command = input.trim().toLowerCase();
            const parts = input.trim().split(' ');
            
            switch (parts[0].toLowerCase()) {
                case 'spawn':
                    if (parts.length < 2) {
                        console.log('❌ Usage: spawn <username>');
                    } else {
                        this.handleManualSpawnCommand(parts[1]).catch(error => {
                            console.error(`❌ Error in spawn command: ${error.message}`);
                        });
                    }
                    break;
                    
                case 'gift':
                    if (parts.length < 4) {
                        console.log('❌ Usage: gift <username> <gift_name> <diamond_count>');
                    } else {
                        this.handleManualGiftCommand(parts[1], parts[2], parseInt(parts[3]));
                    }
                    break;
                    
                case 'help':
                    this.showManualCommandHelp();
                    break;
                    
                case 'exit':
                    console.log('👋 Goodbye!');
                    rl.close();
                    process.exit(0);
                    break;
                    
                default:
                    if (command) {
                        console.log('❌ Unknown command. Type "help" for available commands.');
                    }
                    break;
            }
            
            rl.prompt();
        });
        
        rl.on('close', () => {
            console.log('👋 Manual command interface closed.');
            process.exit(0);
        });
    }
    
    async handleManualSpawnCommand(username) {
        console.log(`🎮 Manually triggering sim creation for: ${username}`);
        
        try {
            // Create a fake diamond tracking result that triggers sim creation
            const fakeDiamondTracking = {
                totalDiamonds: this.diamondThreshold,
                thresholdReached: true,
                shouldCreateSim: true,
                timeRemaining: 3600
            };
            
            // Get real profile picture and analyze appearance with AI
            let appearanceAnalysis;
            let profilePictureUrl;
            
            if (this.aiEnabled) {
                console.log(`🤖 AI enabled - analyzing appearance for ${username}...`);
                appearanceAnalysis = await this.analyzeUserAppearance(username);
                profilePictureUrl = this.getProfilePictureUrl(username);
            } else {
                console.log(`⚠️ AI disabled - using default appearance for ${username}`);
                appearanceAnalysis = this.getDefaultAppearance();
                profilePictureUrl = 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=Test';
            }
            
            // Create the gift data structure
            const giftData = {
                type: 'gift',
                user: `${username}_${Math.random().toString(36).substring(2, 15)}`,
                gift: 'diamond',
                giftDisplayName: 'Diamond',
                value: 1,
                giftId: 99999,
                diamondCount: this.diamondThreshold,
                description: 'Manual test gift',
                timestamp: new Date().toISOString(),
                diamondTracking: fakeDiamondTracking,
                appearanceAnalysis: appearanceAnalysis
            };
            
            // Send the event to connected clients (same format as real gifts)
            console.log(`📤 Sending sim creation event:`, JSON.stringify(giftData, null, 2));
            this.broadcastToClients(giftData);
            
            console.log(`✅ Sim creation event sent for ${username}`);
            
        } catch (error) {
            console.error(`❌ Error in manual spawn command for ${username}:`, error.message);
            
            // Fallback: send with default appearance
            const fallbackData = {
                type: 'gift',
                user: username,
                gift: 'diamond',
                giftDisplayName: 'Diamond',
                value: 1,
                giftId: 99999,
                diamondCount: this.diamondThreshold,
                description: 'Manual test gift (fallback)',
                profilePictureUrl: 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=Test',
                timestamp: new Date().toISOString(),
                diamondTracking: {
                    totalDiamonds: this.diamondThreshold,
                    thresholdReached: true,
                    shouldCreateSim: true,
                    timeRemaining: 3600
                },
                appearanceAnalysis: this.getDefaultAppearance()
            };
            
            this.broadcastToClients(fallbackData);
            console.log(`✅ Fallback sim creation event sent for ${username}`);
        }
    }
    
    handleManualGiftCommand(username, giftName, diamondCount) {
        console.log(`🎮 Sending test gift: ${username} sent ${giftName} (${diamondCount} diamonds)`);
        
        const giftData = {
            type: 'gift',
            user: username,
            gift: giftName.toLowerCase(),
            giftDisplayName: giftName,
            value: 1,
            giftId: Math.floor(Math.random() * 100000),
            diamondCount: diamondCount,
            description: `Manual test ${giftName} gift`,
            profilePictureUrl: 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=Test',
            timestamp: new Date().toISOString()
        };
        
        // Send the event to connected clients (same format as real gifts)
        console.log(`📤 Sending test gift event:`, JSON.stringify(giftData, null, 2));
        this.broadcastToClients(giftData);
        
        console.log(`✅ Test gift event sent: ${username} -> ${giftName} (${diamondCount} diamonds)`);
    }
    
    showManualCommandHelp() {
        console.log('\n📖 Manual Command Help:');
        console.log('  spawn <username>     - Manually trigger sim creation for a user');
        console.log('                       Example: spawn testuser123');
        console.log('');
        console.log('  gift <username> <gift> <diamonds> - Send a test gift event');
        console.log('                       Example: gift testuser123 rose 5');
        console.log('');
        console.log('  help                - Show this help message');
        console.log('  exit                - Exit the program');
        console.log('');
    }

    startDiamondTrackerCleanup() {
        // Clean up expired diamond trackers every 5 minutes
        setInterval(() => {
            this.cleanupExpiredDiamondTrackers();
        }, 5 * 60 * 1000); // 5 minutes
    }
    
    cleanupExpiredDiamondTrackers() {
        try {
            const currentTime = Date.now() / 1000;
            const expiredUsers = [];
            
            for (const [username, tracker] of this.diamondTrackers.entries()) {
                const timeSinceFirst = currentTime - tracker.firstGiftTime;
                if (timeSinceFirst >= this.diamondTimeout && !tracker.simCreated) {
                    expiredUsers.push(username);
                }
            }
            
            // Remove expired trackers
            for (const username of expiredUsers) {
                this.diamondTrackers.delete(username);
            }
            
            if (expiredUsers.length > 0) {
                console.log(`🧹 Cleaned up ${expiredUsers.length} expired diamond trackers`);
            }
            
        } catch (error) {
            console.error('❌ Error cleaning up expired diamond trackers:', error.message);
        }
    }
    
    stop() {
        console.log('🛑 Stopping TikTok Bridge Service...');
        
        if (this.tiktokConnection) {
            this.tiktokConnection.disconnect();
        }
        
        if (this.wss) {
            this.wss.close();
        }
        
        console.log('👋 Bridge service stopped');
    }
}

// Main execution
if (import.meta.url === `file://${process.argv[1]}`) {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const usernameIndex = args.indexOf('--username');
    const portIndex = args.indexOf('--port');
    
    const username = usernameIndex !== -1 ? args[usernameIndex + 1] : config.tiktokUsername;
    const port = portIndex !== -1 ? parseInt(args[portIndex + 1]) : config.websocketPort;
    const verbose = args.includes('--verbose');
    const manualMode = args.includes('--manual');
    
    if (!username) {
        console.error('❌ Error: TikTok username is required');
        console.log('Usage: node bridge.js --username <tiktok_username> [--port <port>] [--verbose] [--manual]');
        console.log('   or configure username in config.json');
        process.exit(1);
    }
    
    // Create and start bridge service
    const bridge = new TikTokBridgeService(username, port, manualMode);
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Received shutdown signal...');
        bridge.stop();
        process.exit(0);
    });
    
    process.on('SIGTERM', () => {
        console.log('\n🛑 Received termination signal...');
        bridge.stop();
        process.exit(0);
    });
    
    if (manualMode) {
        // Manual mode: Only start WebSocket server and command interface
        console.log('🎮 Starting in MANUAL MODE - No TikTok connection required');
        bridge.startWebSocketServer();
        bridge.startManualCommandInterface();
    } else {
        // Normal mode: Start full TikTok connection
        bridge.setupWebSocketServer(); // Set up WebSocket server for normal mode
        bridge.start().catch(error => {
            console.error('💥 Fatal error:', error.message);
            process.exit(1);
        });
    }
}

export default TikTokBridgeService;
