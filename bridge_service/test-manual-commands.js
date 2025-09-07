#!/usr/bin/env node
/**
 * Test script for manual command interface
 * This script demonstrates how to use the manual command feature
 */

console.log('🎮 Manual Command Interface Test');
console.log('================================');
console.log('');
console.log('To test the manual command interface:');
console.log('');
console.log('1. Start the bridge service with --manual flag:');
console.log('   node bridge.js --username your_tiktok_username --manual');
console.log('');
console.log('   ✅ NO TikTok connection required!');
console.log('   ✅ NO live stream needed!');
console.log('   ✅ Works completely offline!');
console.log('');
console.log('2. Available commands:');
console.log('   spawn testuser123        - Trigger sim creation for testuser123');
console.log('   gift testuser123 rose 5  - Send a test rose gift (5 diamonds)');
console.log('   gift testuser123 diamond 1 - Send a test diamond gift (1 diamond)');
console.log('   help                     - Show help');
console.log('   exit                     - Exit');
console.log('');
console.log('3. Example session:');
console.log('   > spawn alice123');
console.log('   > gift bob456 heart 3');
console.log('   > gift charlie789 diamond 1');
console.log('   > exit');
console.log('');
console.log('Note: Make sure your Sims 4 mod is running and connected to the bridge service!');
console.log('The bridge will start a WebSocket server on port 8765 for your mod to connect to.');
console.log('');
