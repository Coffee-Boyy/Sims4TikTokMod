# Sim Character Creation Pipeline

This document describes the sim character creation pipeline that creates new sims when TikTok users gift more than 1000 diamonds (accumulated over time).

## Architecture Overview

The pipeline is split between two components:

### 1. Bridge Service (Node.js)
- **Location**: `bridge_service/bridge.js`
- **Responsibilities**:
  - Connects to TikTok Live streams
  - Receives gift events with profile pictures
  - Tracks diamond accumulation per user over time
  - Downloads and analyzes profile pictures using AI (OpenAI GPT-4 Vision)
  - Determines when diamond threshold is reached
  - Sends complete gift data with tracking and appearance analysis to the Sims 4 mod

### 2. Sims 4 Mod (Python)
- **Location**: `Scripts/sims_tik_tok_mod/sim_character_creator.py`
- **Responsibilities**:
  - Receives processed gift data from bridge service
  - Creates sims when bridge service indicates threshold is reached
  - Uses pre-analyzed appearance data from bridge service
  - Spawns sims in the game

## Configuration

### Bridge Service Configuration
Edit `bridge_service/config.json`:

```json
{
  "aiAnalysis": {
    "enabled": true,
    "openaiApiKey": "your-openai-api-key-here",
    "model": "gpt-4-vision-preview",
    "timeout": 30000
  }
}
```

Or set the environment variable:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### Bridge Service Diamond Tracking Configuration
Edit `bridge_service/config.json`:

```json
{
  "diamondTracking": {
    "threshold": 1000,
    "timeout": 3600
  }
}
```

## How It Works

1. **Gift Event**: User sends a gift with diamonds on TikTok Live
2. **Diamond Tracking**: Bridge service accumulates diamonds per user over time
3. **Profile Analysis**: Bridge service downloads profile picture and analyzes it with AI
4. **Threshold Check**: Bridge service determines when user reaches 1000+ diamonds
5. **Data Transmission**: Bridge sends complete gift data with tracking status and appearance analysis to Sims 4 mod
6. **Sim Creation**: Mod creates a new sim when bridge indicates threshold is reached
7. **Sim Spawning**: New sim is spawned in the game with the analyzed appearance

## AI Analysis

The bridge service uses OpenAI's GPT-4 Vision model to analyze profile pictures and extract:

- Hair color (blonde, brown, black, red, gray, white)
- Skin tone (light, medium, dark, very_light, very_dark)
- Eye color (blue, brown, green, hazel, gray)
- Gender (male, female)
- Age (young_adult, adult, elder)
- Hair style (short, medium, long, bald)
- Confidence score (0.0-1.0)

## Installation

### Bridge Service Dependencies
```bash
cd bridge_service
npm install
```

### Required Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## Usage

### Start Bridge Service
```bash
cd bridge_service
node bridge.js --username your_tiktok_username
```

### Start Sims 4 Mod
The mod will automatically connect to the bridge service when initialized.

## Testing

### Test Sim Creation Pipeline
Run the Node.js test script to verify the sim creation functionality:
```bash
cd bridge_service
npm run test-sim-creation
```

This will:
1. Connect to the bridge service
2. Send test gift events with different diamond amounts
3. Test diamond accumulation and threshold detection
4. Verify that sim creation is triggered when appropriate

### Test Bridge Service Connection
Test basic bridge service connectivity:
```bash
cd bridge_service
npm test
```

## Troubleshooting

### AI Analysis Not Working
- Check that `OPENAI_API_KEY` is set correctly
- Verify the API key has access to GPT-4 Vision
- Check bridge service logs for AI analysis errors

### Sims Not Being Created
- Verify diamond threshold is being reached (1000 diamonds)
- Check that appearance analysis is being received
- Look for errors in the Sims 4 mod logs

### Bridge Service Connection Issues
- Ensure the TikTok user is currently live streaming
- Check that the username is correct
- Verify network connectivity

## Customization

### Changing Diamond Threshold
Edit `bridge_service/config.json`:
```json
{
  "diamondTracking": {
    "threshold": 500,
    "timeout": 3600
  }
}
```

### Modifying AI Analysis
Edit the prompt in `bridge_service/bridge.js` in the `analyzeProfilePicture` method.

### Adding New Appearance Attributes
1. Update the AI prompt in the bridge service
2. Update the `AppearanceAttributes` dataclass in the mod
3. Update the sim creation logic to use new attributes
