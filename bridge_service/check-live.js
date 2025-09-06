#!/usr/bin/env node
/**
 * Simple utility to check if a TikTok user is currently live streaming
 */

const https = require('https');
const http = require('http');

function checkTikTokLiveStatus(username) {
    return new Promise((resolve, reject) => {
        console.log(`🔍 Checking if @${username} is currently live...`);
        
        const options = {
            hostname: 'www.tiktok.com',
            port: 443,
            path: `/@${username}/live`,
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                if (res.statusCode === 404) {
                    console.log(`❌ User @${username} not found on TikTok`);
                    resolve(false);
                } else if (res.statusCode !== 200) {
                    console.log(`⚠️  Could not verify live status (HTTP ${res.statusCode})`);
                    resolve(false);
                } else {
                    // Check if "LIVE" appears in the response
                    if (data.includes('LIVE') || data.includes('live')) {
                        console.log(`✅ @${username} appears to be live!`);
                        resolve(true);
                    } else {
                        console.log(`❌ @${username} does not appear to be live streaming`);
                        resolve(false);
                    }
                }
            });
        });
        
        req.on('error', (error) => {
            console.error(`❌ Network error: ${error.message}`);
            resolve(false);
        });
        
        req.setTimeout(10000, () => {
            console.error('❌ Request timeout');
            req.destroy();
            resolve(false);
        });
        
        req.end();
    });
}

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.error('❌ Error: TikTok username is required');
        console.log('Usage: node check-live.js <tiktok_username>');
        console.log('Example: node check-live.js peanut_the_squirrel12');
        process.exit(1);
    }
    
    const username = args[0];
    
    try {
        const isLive = await checkTikTokLiveStatus(username);
        
        if (isLive) {
            console.log('\n✅ This user should work with the TikTok bridge!');
            process.exit(0);
        } else {
            console.log('\n❌ This user is not live - the bridge will not work');
            console.log('💡 Try finding a user who is currently live streaming');
            process.exit(1);
        }
    } catch (error) {
        console.error('💥 Error:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { checkTikTokLiveStatus };
