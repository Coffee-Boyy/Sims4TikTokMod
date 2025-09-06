#!/usr/bin/env node
/**
 * TikTok Live Bridge Service for Sims 4 Mod (Node.js)
 * Connects to TikTok Live stream and forwards gift events to Sims 4 mod via WebSocket
 */

const { WebSocket, WebSocketServer } = require('ws');
const { TikTokLiveConnection } = require('tiktok-live-connector');
const config = require('./config.json');

class TikTokBridgeService {
    constructor(tiktokUsername, websocketPort = 8765) {
        this.tiktokUsername = tiktokUsername;
        this.websocketPort = websocketPort;
        this.connectedClients = new Set();
        
        // Rate limiting
        this.lastSentTime = 0;
        this.minInterval = 2000; // 2 seconds in milliseconds
        this.maxEventsPerMinute = 10;
        this.eventsThisMinute = 0;
        this.minuteStartTime = Date.now();
        
        // Initialize TikTok connection
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
        this.setupWebSocketServer();
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
            const errorMessage = err?.message || err?.toString() || '';
            const isWarning = err?.info && err.info.includes('falling back');
            
            if (isWarning) {
                console.warn('⚠️  TikTok connection warning:', err.info);
            } else {
                console.error('❌ TikTok connection error:', err);
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
            if (process.argv.includes('--verbose')) {
                const username = data.uniqueId || data.user?.uniqueId || 'unknown';
                const count = data.likeCount || data.count || data.totalLikeCount || 'unknown';
                console.log(`❤️  ${username} liked (${count} total)`);
            }
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
        
        const payload = {
            type: 'gift',
            user: username,
            gift: giftName.toLowerCase(),
            giftDisplayName: giftName, // Keep original case for display
            value: repeatCount,
            giftId: giftId,
            diamondCount: diamondCount,
            description: data.giftDetails?.describe || data.extendedGiftInfo?.describe || '',
            timestamp: new Date().toISOString()
        };
        
        console.log(`🎁 Processing gift: ${payload.user} sent "${payload.giftDisplayName}" (x${payload.value}) [${payload.diamondCount} 💎]`);
        
        // Debug logging in verbose mode
        if (process.argv.includes('--verbose')) {
            console.log(`   📊 Gift Details:`, {
                id: payload.giftId,
                diamonds: payload.diamondCount,
                description: payload.description
            });
        }
        
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
        const errorMessage = error?.message || error?.toString() || 'Unknown error';
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
if (require.main === module) {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const usernameIndex = args.indexOf('--username');
    const portIndex = args.indexOf('--port');
    
    const username = usernameIndex !== -1 ? args[usernameIndex + 1] : config.tiktokUsername;
    const port = portIndex !== -1 ? parseInt(args[portIndex + 1]) : config.websocketPort;
    const verbose = args.includes('--verbose');
    
    if (!username) {
        console.error('❌ Error: TikTok username is required');
        console.log('Usage: node bridge.js --username <tiktok_username> [--port <port>] [--verbose]');
        console.log('   or configure username in config.json');
        process.exit(1);
    }
    
    // Create and start bridge service
    const bridge = new TikTokBridgeService(username, port);
    
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
    
    // Start the service
    bridge.start().catch(error => {
        console.error('💥 Fatal error:', error.message);
        process.exit(1);
    });
}

module.exports = TikTokBridgeService;
