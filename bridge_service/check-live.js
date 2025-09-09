#!/usr/bin/env node
/**
 * Simple utility to check if a TikTok user is currently live streaming
 */

import https from 'https';
import http from 'http';
import zlib from 'zlib';

function checkTikTokLiveStatus(username) {
    return new Promise((resolve, reject) => {
        console.log(`🔍 Checking if @${username} is currently live...`);
        
        const options = {
            hostname: 'www.tiktok.com',
            port: 443,
            path: `/@${username}/live`,
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        };
        
        const req = https.request(options, (res) => {
            let data = Buffer.alloc(0);
            
            res.on('data', (chunk) => {
                data = Buffer.concat([data, chunk]);
            });
            
            res.on('end', () => {
                if (res.statusCode === 404) {
                    console.log(`❌ User @${username} not found on TikTok`);
                    resolve(false);
                } else if (res.statusCode !== 200) {
                    console.log(`⚠️  Could not verify live status (HTTP ${res.statusCode})`);
                    resolve(false);
                } else {
                    // Handle compressed responses
                    let htmlContent = '';
                    const encoding = res.headers['content-encoding'];
                    
                    try {
                        if (encoding === 'gzip') {
                            htmlContent = zlib.gunzipSync(data).toString('utf8');
                        } else if (encoding === 'deflate') {
                            htmlContent = zlib.inflateSync(data).toString('utf8');
                        } else if (encoding === 'br') {
                            htmlContent = zlib.brotliDecompressSync(data).toString('utf8');
                        } else {
                            htmlContent = data.toString('utf8');
                        }
                        
                        console.log(`📦 Content encoding: ${encoding || 'none'}`);
                        
                        // More sophisticated live detection
                        const isLive = detectLiveStatus(htmlContent, username);
                        if (isLive) {
                            console.log(`✅ @${username} appears to be live!`);
                            resolve(true);
                        } else {
                            console.log(`❌ @${username} does not appear to be live streaming`);
                            resolve(false);
                        }
                    } catch (decompressError) {
                        console.error(`❌ Error decompressing content: ${decompressError.message}`);
                        // Try as plain text fallback
                        htmlContent = data.toString('utf8');
                        const isLive = detectLiveStatus(htmlContent, username);
                        resolve(isLive);
                    }
                }
            });
        });
        
        req.on('error', (error) => {
            console.error(`❌ Network error: ${error.message}`);
            resolve(false);
        });
        
        req.setTimeout(15000, () => {
            console.error('❌ Request timeout');
            req.destroy();
            resolve(false);
        });
        
        req.end();
    });
}

function detectLiveStatus(htmlContent, username) {
    try {
        console.log(`🔍 Analyzing HTML content for ${username} (${htmlContent.length} characters)`);
        
        // Convert to lowercase for case-insensitive matching
        const content = htmlContent.toLowerCase();
        
        // Debug: Check what we're getting
        if (content.includes('<!doctype html')) {
            console.log('✅ Received full HTML page');
        } else {
            console.log('⚠️ Content may be incomplete or redirected');
        }
        
        // Check for specific live indicators in TikTok's HTML structure
        const liveIndicators = [
            // Look for live room data structures
            '"live_status":1',
            '"live_status": 1',
            '"roomstatus":2',
            '"room_status":2',
            '"isliving":true',
            '"is_living":true',
            '"livestatus":1',
            // Live stream specific elements
            'live-room-player',
            'live-stream-container',
            'live-viewer-count',
            'live-room-info',
            'live-room-header',
            // Meta tags for live streams
            'property="og:type" content="tiktok:live"',
            'name="twitter:card" content="player"',
            // TikTok specific live indicators
            'data-e2e="live-room"',
            'data-e2e="live-player"',
            'class="live-room',
            // URL patterns that indicate live
            '/live/',
            'live?',
            // Live status in scripts
            'roominfo',
            'liveroom',
            'live_room'
        ];
        
        // Check for live indicators with debugging
        const foundIndicators = [];
        liveIndicators.forEach(indicator => {
            if (content.includes(indicator.toLowerCase())) {
                foundIndicators.push(indicator);
            }
        });
        
        if (foundIndicators.length > 0) {
            console.log(`✅ Found ${foundIndicators.length} live indicators:`, foundIndicators);
            return true;
        } else {
            console.log('❌ No live indicators found');
        }
        
        // Check for redirect patterns
        const redirectPatterns = [
            'window.location.replace',
            'window.location.href',
            'location.href',
            'redirect'
        ];
        
        const foundRedirects = [];
        redirectPatterns.forEach(pattern => {
            if (content.includes(pattern.toLowerCase())) {
                foundRedirects.push(pattern);
            }
        });
        
        if (foundRedirects.length > 0) {
            console.log(`⚠️ Found redirect patterns:`, foundRedirects);
        }
        
        // Look for JSON data in script tags
        const scriptRegex = /<script[^>]*>(.*?)<\/script>/gi;
        let scriptMatch;
        let foundLiveData = false;
        
        while ((scriptMatch = scriptRegex.exec(htmlContent)) !== null) {
            const scriptContent = scriptMatch[1].toLowerCase();
            
            // Look for live-related data in scripts
            if (scriptContent.includes('live') && (
                scriptContent.includes('room') || 
                scriptContent.includes('status') ||
                scriptContent.includes('viewer') ||
                scriptContent.includes('stream')
            )) {
                console.log('🔍 Found potential live data in script tag');
                
                // Look for specific patterns
                if (scriptContent.includes('"live"') || 
                    scriptContent.includes('islive') || 
                    scriptContent.includes('live_status') ||
                    scriptContent.includes('roomstatus')) {
                    console.log('✅ Found live status data in script');
                    foundLiveData = true;
                }
            }
        }
        
        // Simple fallback - if we're on a live URL and have live-related content
        if (content.includes('live') && content.includes('viewer')) {
            console.log('✅ Found live + viewer combination');
            return true;
        }
        
        // Another fallback - look for common live page elements
        const livePageElements = [
            'live room',
            'live stream',
            'viewer count',
            'live chat',
            'now live',
            'going live',
            'live video'
        ];
        
        const foundElements = [];
        livePageElements.forEach(element => {
            if (content.includes(element)) {
                foundElements.push(element);
            }
        });
        
        if (foundElements.length > 0) {
            console.log(`✅ Found ${foundElements.length} live page elements:`, foundElements);
            return true;
        }
        
        // Debug: Show a sample of the content
        console.log('📄 Content sample (first 500 chars):');
        console.log(htmlContent.substring(0, 500));
        
        return foundLiveData;
        
    } catch (error) {
        console.error(`Error parsing live status for ${username}:`, error);
        return false;
    }
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

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export { checkTikTokLiveStatus };
