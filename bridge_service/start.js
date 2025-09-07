#!/usr/bin/env node
/**
 * Startup script for TikTok Bridge Service
 * Provides a nice interface for starting the bridge
 */

const TikTokBridgeService = require('./bridge.js');
const config = require('./config.json');

function showBanner() {
    console.log('╔═══════════════════════════════════════════════════════════════╗');
    console.log('║                  🎮 SIMS 4 TIKTOK BRIDGE 🎮                  ║');
    console.log('║                        Node.js Edition                        ║');
    console.log('╚═══════════════════════════════════════════════════════════════╝');
    console.log('');
}

function showUsage() {
    console.log('Usage:');
    console.log('  node start.js [--username <tiktok_username>] [--port <port>] [--verbose] [--debug] [--manual]');
    console.log('');
    console.log('Options:');
    console.log('  --username    TikTok username to connect to (without @)');
    console.log('  --port        WebSocket port (default: 8765)');
    console.log('  --verbose     Enable verbose logging (shows chat, likes, follows)');
    console.log('  --debug       Enable debug mode (shows full event structures)');
    console.log('  --manual      Enable manual command interface (no TikTok connection required)');
    console.log('  --help        Show this help message');
    console.log('');
    console.log('Examples:');
    console.log('  node start.js --username shirleycoelloc');
    console.log('  node start.js --username popular_streamer --port 9000 --verbose');
    console.log('  node start.js --username streamer --debug');
    console.log('  node start.js --username testuser --manual');
    console.log('');
    console.log('Note: The TikTok user must be currently live streaming (unless using --manual)!');
}

function main() {
    showBanner();
    
    const args = process.argv.slice(2);
    
    // Check for help flag
    if (args.includes('--help') || args.includes('-h')) {
        showUsage();
        return;
    }
    
    // Parse arguments
    const usernameIndex = args.indexOf('--username');
    const portIndex = args.indexOf('--port');
    
    const username = usernameIndex !== -1 ? args[usernameIndex + 1] : config.tiktokUsername;
    const port = portIndex !== -1 ? parseInt(args[portIndex + 1]) : config.websocketPort;
    const verbose = args.includes('--verbose');
    const debug = args.includes('--debug');
    const manualMode = args.includes('--manual');
    
    if (!username) {
        console.error('❌ Error: TikTok username is required!');
        console.log('');
        showUsage();
        process.exit(1);
    }
    
    // Show startup info
    console.log('🚀 Starting TikTok Bridge Service...');
    console.log(`   TikTok Username: @${username}`);
    console.log(`   WebSocket Port: ${port}`);
    console.log(`   Verbose Mode: ${verbose ? 'ON' : 'OFF'}`);
    console.log(`   Debug Mode: ${debug ? 'ON' : 'OFF'}`);
    console.log(`   Manual Mode: ${manualMode ? 'ON' : 'OFF'}`);
    console.log('   Press Ctrl+C to stop');
    console.log('--------------------------------------------------');
    
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
    
    // Start the service
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

if (require.main === module) {
    main();
}
