#!/usr/bin/env node
/**
 * Test script for Sim Character Creation Pipeline
 * NOTE: This test file uses legacy gift format and needs to be updated to use sims_action format
 * Sends test gift events to the bridge service to test the sim creation functionality
 */

const WebSocket = require('ws');

class SimCreationTester {
    constructor(host = '127.0.0.1', port = 8765) {
        this.host = host;
        this.port = port;
        this.url = `ws://${host}:${port}`;
        this.ws = null;
        this.isConnected = false;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            console.log(`🔗 Connecting to bridge service at ${this.url}...`);
            
            this.ws = new WebSocket(this.url);
            
            this.ws.on('open', () => {
                console.log('✅ Connected to bridge service!');
                this.isConnected = true;
                resolve();
            });
            
            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    console.log('📨 Received from bridge:', message);
                } catch (error) {
                    console.log('📨 Received raw message:', data.toString());
                }
            });
            
            this.ws.on('error', (error) => {
                console.error('❌ WebSocket error:', error.message);
                reject(error);
            });
            
            this.ws.on('close', () => {
                console.log('👋 Disconnected from bridge service');
                this.isConnected = false;
            });
        });
    }

    sendTestActionEvent(actionData) {
        if (!this.isConnected) {
            console.error('❌ Not connected to bridge service');
            return;
        }

        console.log(`📤 Sending test action event:`, actionData);
        this.ws.send(JSON.stringify(actionData));
    }

    async runTests() {
        try {
            await this.connect();
            
            console.log('\n🧪 Starting Sim Creation Tests...\n');
            
            // Test 1: User with small diamond gift action (should not trigger sim creation)
            console.log('Test 1: Small diamond gift action (should not trigger sim creation)');
            this.sendTestActionEvent({
                type: 'sims_action',
                user: 'test_user_1',
                action: 'give_money',
                count: 1,
                context: {
                    giftName: 'Diamond',
                    giftId: 12345,
                    diamondCount: 200,
                    profilePictureUrl: 'https://via.placeholder.com/150/FF6B6B/FFFFFF?text=User1',
                    isManual: false
                },
                timestamp: new Date().toISOString()
            });
            
            await this.sleep(2000);
            
            // Test 2: Same user with more diamonds (should trigger sim creation)
            console.log('\nTest 2: Large diamond gift (should trigger sim creation)');
            this.sendTestGiftEvent({
                type: 'gift',
                user: 'test_user_1',
                gift: 'diamond',
                giftDisplayName: 'Diamond',
                value: 1,
                giftId: 12346,
                diamondCount: 3, // Total: 2 + 3 = 5 >= 5 threshold
                description: 'A large diamond gift',
                profilePictureUrl: 'https://via.placeholder.com/150/4ECDC4/FFFFFF?text=User1',
                timestamp: new Date().toISOString()
            });
            
            await this.sleep(3000);
            
            // Test 3: Different user with single large gift
            console.log('\nTest 3: Different user with large gift (should trigger sim creation)');
            this.sendTestGiftEvent({
                type: 'gift',
                user: 'test_user_2',
                gift: 'diamond',
                giftDisplayName: 'Diamond',
                value: 1,
                giftId: 12347,
                diamondCount: 5, // Single gift >= 5 threshold
                description: 'A very large diamond gift',
                profilePictureUrl: 'https://via.placeholder.com/150/45B7D1/FFFFFF?text=User2',
                timestamp: new Date().toISOString()
            });
            
            await this.sleep(3000);
            
            // Test 4: Non-diamond gift (should not affect tracking)
            console.log('\nTest 4: Non-diamond gift (should not affect tracking)');
            this.sendTestGiftEvent({
                type: 'gift',
                user: 'test_user_3',
                gift: 'rose',
                giftDisplayName: 'Rose',
                value: 1,
                giftId: 12348,
                diamondCount: 0,
                description: 'A beautiful rose',
                profilePictureUrl: 'https://via.placeholder.com/150/FF9FF3/FFFFFF?text=User3',
                timestamp: new Date().toISOString()
            });
            
            await this.sleep(2000);
            
            console.log('\n✅ All tests completed!');
            console.log('📝 Check the bridge service logs and Sims 4 mod for results.');
            console.log('💡 Make sure the Sims 4 mod is running and connected to see sim creation.');
            
        } catch (error) {
            console.error('❌ Test failed:', error.message);
            console.log('\n🔍 Troubleshooting:');
            console.log('1. Make sure the bridge service is running: cd bridge_service && node bridge.js');
            console.log('2. Check that the WebSocket port (8765) is not blocked');
            console.log('3. Verify the bridge service is listening on the correct host/port');
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const hostIndex = args.indexOf('--host');
    const portIndex = args.indexOf('--port');
    
    const host = hostIndex !== -1 ? args[hostIndex + 1] : '127.0.0.1';
    const port = portIndex !== -1 ? parseInt(args[portIndex + 1]) : 8765;
    
    console.log('🚀 Sim Character Creation Test Script');
    console.log(`   Target: ${host}:${port}`);
    console.log('   Press Ctrl+C to stop\n');
    
    const tester = new SimCreationTester(host, port);
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Shutting down test script...');
        tester.disconnect();
        process.exit(0);
    });
    
    try {
        await tester.runTests();
        
        // Keep connection open for a bit to see any final messages
        console.log('\n⏳ Keeping connection open for 5 seconds to see final messages...');
        await tester.sleep(5000);
        
    } catch (error) {
        console.error('❌ Test execution failed:', error.message);
        process.exit(1);
    } finally {
        tester.disconnect();
    }
}

// Run the tests
if (require.main === module) {
    main().catch(error => {
        console.error('💥 Fatal error:', error.message);
        process.exit(1);
    });
}

module.exports = SimCreationTester;
