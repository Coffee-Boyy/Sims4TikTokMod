#!/usr/bin/env node
/**
 * Test client for TikTok Bridge Service
 * Simulates a Sims 4 mod connecting to the WebSocket server
 */

const WebSocket = require('ws');
const config = require('./config.json');

class TestClient {
    constructor(port = 8765) {
        this.port = port;
        this.ws = null;
    }
    
    connect() {
        console.log(`🔗 Connecting to TikTok Bridge on ws://localhost:${this.port}`);
        
        this.ws = new WebSocket(`ws://localhost:${this.port}`);
        
        this.ws.on('open', () => {
            console.log('✅ Connected to TikTok Bridge Service!');
            console.log('🎧 Listening for TikTok gift events...');
            console.log('   Press Ctrl+C to disconnect');
            console.log('--------------------------------------------------');
        });
        
        this.ws.on('message', (data) => {
            try {
                const event = JSON.parse(data.toString());
                this.handleEvent(event);
            } catch (error) {
                console.error('❌ Error parsing message:', error.message);
                console.log('Raw message:', data.toString());
            }
        });
        
        this.ws.on('close', () => {
            console.log('👋 Disconnected from TikTok Bridge Service');
        });
        
        this.ws.on('error', (error) => {
            console.error('❌ WebSocket error:', error.message);
        });
    }
    
    handleEvent(event) {
        switch (event.type) {
            case 'connection':
                console.log(`📡 ${event.message}`);
                break;
                
            case 'sims_action':
                console.log('🎮 SIMS ACTION RECEIVED:');
                console.log(`   👤 User: ${event.user}`);
                console.log(`   🎯 Action: ${event.action}`);
                console.log(`   🔢 Count: ${event.count}`);
                console.log(`   📝 Context: ${JSON.stringify(event.context, null, 2)}`);
                console.log(`   ⏰ Time: ${event.timestamp}`);
                
                // Simulate Sims 4 mod response
                this.simulateSimsResponse(event);
                break;
                
                
            default:
                console.log(`📨 Unknown event type: ${event.type}`, event);
        }
    }
    
    simulateSimsResponse(actionEvent) {
        // Simulate what the Sims 4 mod might do with this action
        const action = actionEvent.action;
        const context = actionEvent.context || {};
        const giftName = context.giftName || 'Unknown';
        
        console.log(`   🎮 Sims 4 Processing: ${action}`);
        console.log(`   📄 From Gift: ${giftName}`);
        console.log('--------------------------------------------------');
        
        // Send a response back to the bridge (optional)
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const response = {
                type: 'response',
                actionProcessed: action,
                user: actionEvent.user,
                context: context,
                timestamp: new Date().toISOString()
            };
            
            this.ws.send(JSON.stringify(response));
        }
    }
    
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Main execution
if (require.main === module) {
    const args = process.argv.slice(2);
    const portIndex = args.indexOf('--port');
    const port = portIndex !== -1 ? parseInt(args[portIndex + 1]) : config.websocketPort;
    
    const client = new TestClient(port);
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Shutting down test client...');
        client.disconnect();
        process.exit(0);
    });
    
    // Connect to bridge service
    client.connect();
}

module.exports = TestClient;
