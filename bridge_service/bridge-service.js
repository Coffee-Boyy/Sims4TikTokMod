import { WebSocket, WebSocketServer } from 'ws';
import { TikTokLiveConnection } from 'tiktok-live-connector';
import config from './config.json' with { type: 'json' };
import axios from 'axios';
import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";
import GiftMappings from './gift-mappings.js';

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
    constructor(tiktokUsername, websocketPort = 8765, manualMode = false, logCallback = null) {
        this.tiktokUsername = tiktokUsername;
        this.websocketPort = websocketPort;
        this.connectedClients = new Set();
        this.manualMode = manualMode;
        this.logCallback = logCallback || console.log;
        
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
        
        // Gift mappings for interactions - will be loaded from file
        this.giftMappingsManager = new GiftMappings();
        this.giftMappings = {};
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
        
        // Like tracking configuration
        this.likesThreshold = config.likeTracking?.threshold || 100; // Number of likes needed to trigger simoleon reward
        this.likesTimeout = config.likeTracking?.timeout || 60; // Time in seconds before accumulated likes expire
        this.likeTrackers = new Map(); // Track like accumulation per user
        
        // Profile picture configuration
        this.profilePicturesEnabled = config.profilePictures?.enabled !== false;
        this.useWebScraping = config.profilePictures?.useWebScraping !== false;
        this.useTikTokLiveConnector = config.profilePictures?.useTikTokLiveConnector !== false;
        this.fallbackToGenerated = config.profilePictures?.fallbackToGenerated !== false;
        
        if (!manualMode) {
            // Initialize TikTok connection only in normal mode
            this.tiktokConnection = new TikTokLiveConnection(tiktokUsername, {
                processInitialData: false,
                fetchRoomInfoOnConnect: true,
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
        
        // Start cleanup interval for expired diamond trackers and like trackers
        this.startDiamondTrackerCleanup();
        this.startLikeTrackerCleanup();
    }
    
    log(message, type = 'info') {
        const logMessage = {
            timestamp: new Date().toISOString(),
            type: type,
            message: message
        };
        
        if (this.logCallback) {
            this.logCallback(logMessage);
        }
        
        // Also log to console for debugging
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
    
    formatError(error) {
        if (!error) return 'Unknown error';
        
        // Handle different types of errors
        if (typeof error === 'string') {
            return error;
        }
        
        try {
            const exc = error.exception?.stack;
            return JSON.stringify(error) + '\n' + exc;
        } catch (e) {
            // Fallback if JSON.stringify fails
            return error.toString();
        }
    }
    
    setupTikTokEvents() {
        this.log(`🔗 Setting up TikTok Live connection for: @${this.tiktokUsername}`);
        
        // Remove any existing event listeners to prevent duplicates
        if (this.tiktokConnection) {
            this.tiktokConnection.removeAllListeners('connected');
            this.tiktokConnection.removeAllListeners('disconnected');
            this.tiktokConnection.removeAllListeners('error');
            this.tiktokConnection.removeAllListeners('gift');
            this.tiktokConnection.removeAllListeners('chat');
            this.tiktokConnection.removeAllListeners('like');
            this.tiktokConnection.removeAllListeners('follow');
        }
        
        // Connection events
        this.tiktokConnection.on('connected', (state) => {
            const roomId = state?.roomId || state?.roomInfo?.roomId || 'unknown';
            const viewerCount = state?.roomInfo?.data?.user_count || 'unknown';
            this.log(`✅ Connected to TikTok Live! Room ID: ${roomId}`, 'success');
            this.log(`👥 ${viewerCount} viewers watching`, 'info');
        });
        
        this.tiktokConnection.on('disconnected', () => {
            this.log('⚠️  Disconnected from TikTok Live stream', 'warning');
        });
        
        this.tiktokConnection.on('error', (err) => {
            // Check if this is just a fallback warning, not a fatal error
            const isWarning = err?.info && err.info.includes('falling back');
            
            if (isWarning) {
                this.log(`⚠️  TikTok connection warning: ${err.info}`, 'warning');
            } else {
                const errorMessage = this.formatError(err);
                this.log(`❌ TikTok connection error: ${errorMessage}`, 'error');
                this.handleTikTokError(err);
            }
        });
        
        // Gift events - this is what we're interested in for the Sims 4 mod
        this.tiktokConnection.on('gift', (data) => {
            this.processGiftEvent(data);
        });
        
        // Optional: Log other events for debugging
        this.tiktokConnection.on('chat', (data) => {
            const username = data.uniqueId || data.user?.uniqueId || 'unknown';
            const message = data.comment || data.message || 'no message';
            this.log(`💬 ${username}: ${message}`, 'chat');
        });
        
        this.tiktokConnection.on('like', (data) => {
            const username = data.uniqueId || data.user?.uniqueId || 'unknown';
            const count = data.likeCount || data.count || data.totalLikeCount || 'unknown';
            
            this.log(`❤️  ${username} liked (${count} total)`, 'like');
            
            // Forward like events to Sims 4 mod
            this.processLikeEvent(data);
        });
        
        this.tiktokConnection.on('follow', (data) => {
            const username = data.uniqueId || data.user?.uniqueId || 'unknown';
            this.log(`➕ ${username} followed!`, 'follow');
        });
    }
    
    setupWebSocketServer() {
        this.log(`🌐 Setting up WebSocket server on port ${this.websocketPort}`);
        
        this.wss = new WebSocketServer({ 
            port: this.websocketPort,
            host: '127.0.0.1'  // Explicitly bind to IPv4 localhost
        });
        
        this.wss.on('connection', (ws, request) => {
            const clientInfo = `${request.socket.remoteAddress}:${request.socket.remotePort}`;
            this.log(`🎮 Sims 4 mod connected: ${clientInfo}`, 'connection');
            
            this.connectedClients.add(ws);
            
            // Send welcome message
            ws.send(JSON.stringify({
                type: 'connection',
                message: `Connected to TikTok Live bridge for @${this.tiktokUsername}`,
                timestamp: new Date().toISOString()
            }));
            
            ws.on('message', (message) => {
                this.log(`📨 Received from ${clientInfo}: ${message}`, 'websocket');
                // Handle any messages from Sims 4 mod if needed
            });
            
            ws.on('close', () => {
                this.log(`👋 Sims 4 mod disconnected: ${clientInfo}`, 'connection');
                this.connectedClients.delete(ws);
            });
            
            ws.on('error', (error) => {
                this.log(`❌ WebSocket error for ${clientInfo}: ${error.message}`, 'error');
                this.connectedClients.delete(ws);
            });
        });
        
        this.wss.on('listening', () => {
            this.log(`✅ WebSocket server listening on localhost:${this.websocketPort}`, 'success');
        });
    }
    
    processGiftEvent(data) {
        const currentTime = Date.now();
        
        // Reset minute counter if needed
        if (currentTime - this.minuteStartTime >= 60000) {
            this.eventsThisMinute = 0;
            this.minuteStartTime = currentTime;
        }
        
        // Check rate limits
        const username = data.user?.uniqueId || 'unknown';
        if (currentTime - this.lastSentTime < this.minInterval || 
            this.eventsThisMinute >= this.maxEventsPerMinute) {
            this.log(`⏱️  Rate limited: Skipping gift from ${username}`, 'warning');
            return;
        }
        
        // Update rate limiting counters
        this.lastSentTime = currentTime;
        this.eventsThisMinute++;
        
        // Extract gift information from TikTok API
        const giftName = data.giftDetails?.giftName || data.extendedGiftInfo?.name || data.giftName || 'unknown';
        const repeatCount = data.repeatCount || data.comboCount || data.groupCount || 1;
        const giftId = data.giftId || data.giftDetails?.id || data.extendedGiftInfo?.id || 0;
        const diamondCount = data.giftDetails?.diamondCount || data.extendedGiftInfo?.diamond_count || 0;
        
        // Extract profile picture URL from user data
        const profilePictureUrl = data.user?.profilePicture?.url?.[0];

        // Look up the mapped Sims interaction for this gift
        const giftKey = giftName.toLowerCase().trim().replace(/ /g, '_');
        const simsInteraction = this.giftMappings[giftKey] || this.giftMappings[giftId] || 'none';
        
        // Only send to mod if there's a mapped interaction
        if (simsInteraction === 'none') {
            this.log(`⚠️  No Sims interaction mapped for gift: ${giftName} (ID: ${giftId})`, 'warning');
            return;
        }

        // Create simplified payload for Sims 4 mod - only contains action information
        const payload = {
            type: 'sims_action',
            user: username,
            action: simsInteraction,
            count: repeatCount,
            // Optional: keep some gift context for logging/debugging
            context: {
                giftName: giftName,
                giftId: giftId,
                diamondCount: diamondCount,
                profilePictureUrl: profilePictureUrl
            },
            timestamp: new Date().toISOString()
        };
        
        // Process diamond tracking and sim creation
        if (diamondCount > 0) {
            this.processDiamondTracking(username, diamondCount, profilePictureUrl)
                .then(result => {
                    let shouldCreateSim = false;
                    if (result) {
                        shouldCreateSim = result.shouldCreateSim || false;
                        this.log(`💎 Diamond tracking for ${username}: ${JSON.stringify(result)}`, 'diamond');
                    }
                    
                    // If this gift has diamonds and a profile picture, analyze the appearance
                    if (shouldCreateSim && profilePictureUrl && this.aiEnabled) {
                        return this.analyzeUserAppearance(username, profilePictureUrl).then(appearanceData => {
                            return { shouldCreateSim, diamondTracking: result, appearanceAnalysis: appearanceData };
                        });
                    }
                    return { shouldCreateSim, diamondTracking: result, appearanceAnalysis: null };
                })
                .then(processedData => {
                    // Send sim creation action if needed
                    if (processedData.shouldCreateSim) {
                        const simCreationPayload = {
                            type: 'sims_action',
                            user: username,
                            action: 'create_sim',
                            count: 1,
                            context: {
                                giftName: giftName,
                                giftId: giftId,
                                diamondCount: diamondCount,
                                profilePictureUrl: profilePictureUrl,
                                diamondTracking: processedData.diamondTracking,
                                appearanceAnalysis: processedData.appearanceAnalysis
                            },
                            timestamp: new Date().toISOString()
                        };
                        this.broadcastToClients(simCreationPayload);
                        this.log(`📤 Sim creation action sent: ${username} -> create_sim`, 'gift');
                    } else {
                        // Send the gift action
                        this.broadcastToClients(payload);
                        this.log(`📤 Sims action sent: ${username} -> ${simsInteraction} (from ${giftName}, ${diamondCount} 💎)`, 'gift');
                    }
                })
                .catch(error => {
                    this.log(`❌ Error processing gift for ${username}: ${this.formatError(error)}`, 'error');
                    // Still send the gift action even if diamond tracking fails
                    this.broadcastToClients(payload);
                    this.log(`📤 Sims action sent: ${username} -> ${simsInteraction} (from ${giftName}, ${diamondCount} 💎)`, 'gift');
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
            
            this.log(`💎 User ${username} now has ${tracker.totalDiamonds} accumulated diamonds`, 'diamond');
            
            // Check if threshold reached
            if (tracker.totalDiamonds >= this.diamondThreshold && !tracker.simCreated) {
                tracker.simCreated = true;
                this.log(`🎉 Diamond threshold reached for ${username}! Triggering sim creation...`, 'success');
                
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
            this.log(`❌ Error processing diamond tracking for ${username}: ${this.formatError(error)}`, 'error');
            return null;
        }
    }
    
    getProfilePictureUrl(username) {
        return "https://p19-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/96342a004e5b15067605aeb18c70faf1~tplv-tiktokx-cropcenter:1080:1080.jpeg?dr=9640&refresh_token=6f355dd4&x-expires=1757368800&x-signature=EdaetmYBWIdwSWQiZRx9SKYY43I%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5";
    }
    
    async analyzeUserAppearance(username, profilePictureUrl) {
        try {
            this.log(`🎨 Starting appearance analysis for ${username}...`, 'ai');
            
            // Get profile picture URL
            if (!profilePictureUrl) {
                this.log(`⚠️ No profile picture available for ${username}, using defaults`, 'warning');
                return this.getDefaultAppearance();
            }
            
            // Analyze the profile picture
            const appearanceData = await this.analyzeProfilePicture(profilePictureUrl, username);
            if (!appearanceData) {
                this.log(`⚠️ AI analysis failed for ${username}, using defaults`, 'warning');
                return this.getDefaultAppearance();
            }
            
            return appearanceData;
            
        } catch (error) {
            this.log(`❌ Error in appearance analysis for ${username}: ${this.formatError(error)}`, 'error');
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
            this.log(`🔍 Analyzing profile picture for ${username}...`, 'ai');
            
            if (!this.openai) {
                this.log(`⚠️ OpenAI client not initialized for ${username}`, 'warning');
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
            this.log(`❌ Error analyzing profile picture for ${username}: ${this.formatError(error)}`, 'error');
            return null;
        }
    }
    
    processLikeEvent(data) {
        try {
            const currentTime = Date.now();
            
            // Reset minute counter if needed
            if (currentTime - this.minuteStartTime >= 60000) {
                this.eventsThisMinute = 0;
                this.minuteStartTime = currentTime;
            }
            
            // Extract username from data
            const username = data.user?.uniqueId || data.uniqueId || 'unknown';
            const likeCount = data.likeCount || data.count || data.totalLikeCount || 1;
            
            this.log(`❤️  Processing like: ${username} liked (${likeCount} total)`, 'like');
            
            // Clean up expired likes first
            this.cleanupExpiredLikeTrackers();
            
            // Accumulate likes for this user
            this.accumulateLikes(username, likeCount);
            
        } catch (error) {
            this.log(`❌ Error processing like event: ${this.formatError(error)}`, 'error');
        }
    }
    
    accumulateLikes(username, likeCount) {
        try {
            const currentTime = Date.now() / 1000; // Convert to seconds
            
            // Initialize or update tracker for this user
            if (!this.likeTrackers.has(username)) {
                this.likeTrackers.set(username, {
                    totalLikes: 0,
                    firstLikeTime: currentTime,
                    lastLikeTime: currentTime
                });
            }
            
            const tracker = this.likeTrackers.get(username);
            tracker.totalLikes += likeCount;
            tracker.lastLikeTime = currentTime;
            
            this.log(`💖 User ${username} now has ${tracker.totalLikes} accumulated likes`, 'like');
            
            // Check if we should trigger a reward
            this.checkAndTriggerLikeReward(username, tracker);
            
        } catch (error) {
            this.log(`❌ Error accumulating likes for ${username}: ${this.formatError(error)}`, 'error');
        }
    }
    
    checkAndTriggerLikeReward(username, tracker) {
        try {
            const currentTime = Date.now() / 1000;
            const timeSinceFirst = currentTime - tracker.firstLikeTime;
            
            // Check if threshold reached or timeout elapsed
            const shouldTrigger = (tracker.totalLikes >= this.likesThreshold || 
                                 timeSinceFirst >= this.likesTimeout);
            
            if (shouldTrigger) {
                // Trigger reward
                this.triggerLikeReward(username, tracker.totalLikes);
                
                // Remove tracker since reward was triggered
                this.likeTrackers.delete(username);
            }
            
        } catch (error) {
            this.log(`❌ Error checking like reward trigger for ${username}: ${this.formatError(error)}`, 'error');
        }
    }
    
    triggerLikeReward(username, totalLikes) {
        try {
            this.log(`🎉 Like threshold reached for ${username}! Triggering simoleon reward for ${totalLikes} likes...`, 'success');
            
            // Create a simoleon reward action for the Sims 4 mod
            const rewardPayload = {
                type: 'sims_action',
                user: username,
                action: 'like_reward',
                count: totalLikes, // Amount of simoleons to add
                context: {
                    totalLikes: totalLikes,
                    rewardType: 'like_milestone',
                    description: `${username} reached ${totalLikes} likes!`
                },
                timestamp: new Date().toISOString()
            };
            
            // Send the reward action to connected clients
            this.broadcastToClients(rewardPayload);
            this.log(`📤 Like reward sent: ${username} -> ${totalLikes} simoleons for ${totalLikes} likes`, 'like');
            
        } catch (error) {
            this.log(`❌ Error triggering like reward for ${username}: ${this.formatError(error)}`, 'error');
        }
    }
    
    broadcastToClients(payload) {
        if (this.connectedClients.size === 0) {
            this.log('⚠️  No Sims 4 mod clients connected', 'warning');
            return;
        }
        
        const message = JSON.stringify(payload);
        const disconnectedClients = new Set();
        
        this.connectedClients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                try {
                    client.send(message);
                    this.log(`📤 Sent to client: ${payload.type} event for ${payload.user}`, 'websocket');
                } catch (error) {
                    this.log(`❌ Error sending to client: ${this.formatError(error)}`, 'error');
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
        // Use the improved error formatting
        const errorMessage = this.formatError(error);
        const errorMessageLower = errorMessage.toLowerCase();
        
        if (errorMessageLower.includes('live has ended') || errorMessageLower.includes('not found') || errorMessageLower.includes('room not exist')) {
            this.log(`   1. Check if @${this.tiktokUsername} is currently LIVE streaming`, 'error');
            this.log(`   2. Verify the username '${this.tiktokUsername}' exists on TikTok`, 'error');
            this.log('   3. The user must be actively live streaming (not just having an account)', 'error');
            this.log('   4. Try a different username that you know is currently live', 'error');
        } else if (errorMessageLower.includes('rate limit') || errorMessageLower.includes('429')) {
            this.log('   🔍 Rate limit detected - TikTok may be blocking requests', 'error');
            this.log('   Try again in a few minutes', 'error');
        } else if (errorMessageLower.includes('undefined') || !errorMessage || errorMessage === 'Unknown error') {
            this.log('   🔍 Connection failed - likely causes:', 'error');
            this.log(`   1. @${this.tiktokUsername} is NOT currently live streaming`, 'error');
            this.log('   2. Username does not exist on TikTok', 'error');
            this.log('   3. TikTok may be blocking the connection', 'error');
            this.log('   4. Try a different username that you know is currently live', 'error');
        }
    }
    
    async start() {
        this.log('🚀 Starting TikTok Bridge Service...', 'info');
        this.log(`   TikTok Username: ${this.tiktokUsername}`, 'info');
        this.log(`   WebSocket Port: ${this.websocketPort}`, 'info');
        this.log(`   AI Analysis: ${this.aiEnabled ? '✅ Enabled' : '❌ Disabled'}`, 'info');
        if (this.aiEnabled) {
            this.log(`   AI Model: ${this.aiModel}`, 'info');
        }
        this.log(`   Diamond Tracking: ✅ Enabled (threshold: ${this.diamondThreshold}, timeout: ${this.diamondTimeout}s)`, 'info');
        this.log(`   Like Tracking: ✅ Enabled (threshold: ${this.likesThreshold}, timeout: ${this.likesTimeout}s)`, 'info');
        
        try {
            this.log('🔗 Attempting to connect to TikTok Live...', 'info');
            
            // Connect to TikTok Live
            const state = await this.tiktokConnection.connect();
            // Connection success is already logged by the 'connected' event handler
            
        } catch (error) {
            const errorMessage = this.formatError(error);
            this.log(`❌ Failed to connect to TikTok Live: ${errorMessage}`, 'error');
            this.handleTikTokError(error);
            throw error;
        }
    }
    
    startWebSocketServer() {
        this.log('🌐 Starting WebSocket server for manual mode...', 'info');
        this.setupWebSocketServer();
        this.log(`✅ WebSocket server running on port ${this.websocketPort}`, 'success');
        this.log('🎮 Ready to receive connections from Sims 4 mod!', 'info');
    }

    async handleManualSpawnCommand(username) {
        this.log(`🎮 Manually triggering sim creation for: ${username}`, 'manual');
        
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
                this.log(`🤖 AI enabled - analyzing appearance for ${username}...`, 'ai');
                profilePictureUrl = this.getProfilePictureUrl(username);
                appearanceAnalysis = await this.analyzeUserAppearance(username, profilePictureUrl);
            } else {
                this.log(`⚠️ AI disabled - using default appearance for ${username}`, 'warning');
                profilePictureUrl = 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=Test';
                appearanceAnalysis = this.getDefaultAppearance();
            }
            
            // Create the sim creation action data structure
            const simCreationData = {
                type: 'sims_action',
                user: `${username}_${Math.random().toString(36).substring(2, 15)}`,
                action: 'create_sim',
                count: 1,
                context: {
                    giftName: 'Diamond',
                    giftId: 99999,
                    diamondCount: this.diamondThreshold,
                    profilePictureUrl: profilePictureUrl,
                    diamondTracking: fakeDiamondTracking,
                    appearanceAnalysis: appearanceAnalysis,
                    isManual: true
                },
                timestamp: new Date().toISOString()
            };
            
            // Send the event to connected clients
            this.log(`📤 Sending sim creation action for ${username}`, 'manual');
            this.broadcastToClients(simCreationData);
            
            this.log(`✅ Sim creation event sent for ${username}`, 'success');
            
        } catch (error) {
            this.log(`❌ Error in manual spawn command for ${username}: ${this.formatError(error)}`, 'error');
            
            // Fallback: send with default appearance
            const fallbackData = {
                type: 'sims_action',
                user: username,
                action: 'create_sim',
                count: 1,
                context: {
                    giftName: 'Diamond',
                    giftId: 99999,
                    diamondCount: this.diamondThreshold,
                    profilePictureUrl: 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=Test',
                    diamondTracking: {
                        totalDiamonds: this.diamondThreshold,
                        thresholdReached: true,
                        shouldCreateSim: true,
                        timeRemaining: 3600
                    },
                    appearanceAnalysis: this.getDefaultAppearance(),
                    isManual: true
                },
                timestamp: new Date().toISOString()
            };
            
            this.broadcastToClients(fallbackData);
            this.log(`✅ Fallback sim creation action sent for ${username}`, 'success');
        }
    }
    
    handleManualGiftCommand(giftData) {
        const { username, giftName, diamondCount, giftId, tier, icon, simsInteraction, simsInteractionLabel } = giftData;
        
        this.log(`🎮 Sending manual gift: ${username} sent ${giftName} (${diamondCount} diamonds)`, 'manual');
        
        // Look up the mapped Sims interaction for this gift
        const giftKey = giftName.toLowerCase();
        const mappedInteraction = simsInteraction || this.giftMappings[giftKey] || this.giftMappings[giftId] || 'none';
        
        // Only send to mod if there's a mapped interaction
        if (mappedInteraction === 'none') {
            this.log(`⚠️  No Sims interaction mapped for manual gift: ${giftName} (ID: ${giftId})`, 'warning');
            return;
        }

        // Create simplified payload for Sims 4 mod - only contains action information
        const payload = {
            type: 'sims_action',
            user: username,
            action: mappedInteraction,
            count: 1,
            // Optional: keep some gift context for logging/debugging
            context: {
                giftName: giftName,
                giftId: giftId || Math.floor(Math.random() * 100000),
                diamondCount: diamondCount,
                profilePictureUrl: 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=Manual',
                tier: tier,
                icon: icon,
                isManual: true
            },
            timestamp: new Date().toISOString()
        };
        
        // Send the event to connected clients
        this.log(`📤 Sending manual Sims action: ${username} -> ${mappedInteraction} (from ${giftName}, ${diamondCount} 💎)`, 'manual');
        this.broadcastToClients(payload);
        
        this.log(`✅ Manual Sims action sent: ${username} -> ${mappedInteraction} (from ${giftName}, ${diamondCount} 💎)`, 'success');
    }

    async updateGiftMappings(mappings) {
        this.giftMappings = { ...mappings };
        await this.giftMappingsManager.updateMappings(mappings);
        this.log(`🔧 Gift mappings updated: ${Object.keys(mappings).length} gifts configured`, 'info');
    }

    getGiftMappings() {
        return { ...this.giftMappings };
    }

    async loadGiftMappings() {
        try {
            this.giftMappings = await this.giftMappingsManager.loadMappings();
            this.log(`📁 Gift mappings loaded: ${Object.keys(this.giftMappings).length} gifts configured`, 'info');
            return this.giftMappings;
        } catch (error) {
            this.log(`❌ Failed to load gift mappings: ${this.formatError(error)}`, 'error');
            // Use defaults if loading fails
            this.giftMappings = this.giftMappingsManager.getAllMappings();
            return this.giftMappings;
        }
    }

    startDiamondTrackerCleanup() {
        // Clean up expired diamond trackers every 5 minutes
        setInterval(() => {
            this.cleanupExpiredDiamondTrackers();
        }, 5 * 60 * 1000); // 5 minutes
    }
    
    startLikeTrackerCleanup() {
        // Clean up expired like trackers every minute
        setInterval(() => {
            this.cleanupExpiredLikeTrackers();
        }, 60 * 1000); // 1 minute
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
                this.log(`🧹 Cleaned up ${expiredUsers.length} expired diamond trackers`, 'info');
            }
            
        } catch (error) {
            this.log(`❌ Error cleaning up expired diamond trackers: ${this.formatError(error)}`, 'error');
        }
    }
    
    cleanupExpiredLikeTrackers() {
        try {
            const currentTime = Date.now() / 1000;
            const expiredUsers = [];
            
            for (const [username, tracker] of this.likeTrackers.entries()) {
                const timeSinceFirst = currentTime - tracker.firstLikeTime;
                if (timeSinceFirst >= this.likesTimeout) {
                    expiredUsers.push(username);
                }
            }
            
            // Trigger rewards for expired users and remove trackers
            for (const username of expiredUsers) {
                const tracker = this.likeTrackers.get(username);
                if (tracker && tracker.totalLikes > 0) {
                    this.triggerLikeReward(username, tracker.totalLikes);
                }
                this.likeTrackers.delete(username);
            }
            
            if (expiredUsers.length > 0) {
                this.log(`🧹 Cleaned up ${expiredUsers.length} expired like trackers`, 'info');
            }
            
        } catch (error) {
            this.log(`❌ Error cleaning up expired like trackers: ${this.formatError(error)}`, 'error');
        }
    }
    
    stop() {
        this.log('🛑 Stopping TikTok Bridge Service...', 'info');
        
        try {
            // Close all WebSocket connections
            if (this.connectedClients.size > 0) {
                this.connectedClients.forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.close(1000, 'Bridge service shutting down');
                    }
                });
                this.connectedClients.clear();
            }
            
            // Disconnect from TikTok and clean up event listeners
            if (this.tiktokConnection) {
                // Remove all event listeners before disconnecting to prevent memory leaks
                this.tiktokConnection.removeAllListeners('connected');
                this.tiktokConnection.removeAllListeners('disconnected');
                this.tiktokConnection.removeAllListeners('error');
                this.tiktokConnection.removeAllListeners('gift');
                this.tiktokConnection.removeAllListeners('chat');
                this.tiktokConnection.removeAllListeners('like');
                this.tiktokConnection.removeAllListeners('follow');
                
                this.tiktokConnection.disconnect();
                this.tiktokConnection = null;
                this.log('🔌 Disconnected from TikTok Live and cleaned up event listeners', 'info');
            }
            
            // Close WebSocket server
            if (this.wss) {
                this.wss.close(() => {
                    this.log('✅ WebSocket server closed', 'info');
                });
                this.wss = null;
            }
            
            this.log('👋 Bridge service stopped successfully', 'success');
        } catch (error) {
            this.log(`❌ Error stopping bridge service: ${this.formatError(error)}`, 'error');
        }
    }
}

export default TikTokBridgeService;
