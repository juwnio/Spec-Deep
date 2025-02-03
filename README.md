# Spec-Drive: AI-Powered Task Automation System 🤖

## Overview
Spec-Drive is an advanced automation system that combines computer vision and language models to perform automated tasks on Windows. It uses Groq's powerful AI models to analyze screen content and execute precise actions.

## Features

### Core Capabilities
- 🔄 Fully automated task execution
- 👁️ Real-time screen analysis
- ⌨️ Smart keyboard/mouse automation
- 🛡️ Multiple safety mechanisms
- 🎯 Precise action verification
- 🔄 Automatic error recovery

### Smart Features
- 📱 Multi-model support (DeepSeek, LLaMA variants)
- 🔑 Secure API key management
- ⚡ Rate limit handling with model switching
- 🔄 Automatic state recovery
- 📊 Real-time status updates
- ⚙️ Easy settings management

## Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

Required packages:
- customtkinter
- pyautogui
- requests
- pywin32
- Pillow
- python-dotenv
- typing-extensions

### First-Time Setup
1. Launch the application
2. Get your API key from [Groq Console](https://console.groq.com/keys)
3. Enter your API key in the welcome screen
4. Select your preferred model

### Basic Usage
1. Enter your task description
2. Click "Execute Task"
3. Monitor progress in status panels
4. Use corner triggers for emergency stop

## Safety Features

### Automatic Safeguards
- Corner trigger failsafe
- Command verification
- Rate limiting protection
- Maximum execution time limits
- Minimum action intervals

### Error Handling
- Automatic retry mechanism
- Model switching on rate limits
- API key validation
- Command verification
- State recovery

## Interface Components

### Main Window
- Task input field
- Model selector
- Status panels
- Settings access
- Progress indicators

### Settings Panel
- API key management
- Model selection
- Configuration options

### Status Panels
- Current action reason
- Executed command
- Progress indicators
- Error messages

## Development Information

### File Structure
```
spec-drive/
├── spec.py              # Main application
├── api_manager.py       # API key handling
├── model_selector.py    # Model selection
├── response_handler.py  # Response processing
├── settings_dialog.py   # Settings UI
├── completion_dialog.py # Task completion
└── rate_limit_dialog.py # Rate limit handling
```

### Configuration
- API keys stored in: `~/.spec-drive/config.json`
- Context files:
  - `context.txt`: Vision analysis instructions
  - `context2.txt`: Automation rules

### Models Available
- DeepSeek (default)
- LLaMA Spec
- LLaMA Versatile

## Troubleshooting

### Common Issues
1. **API Key Invalid**
   - Check key in settings
   - Regenerate from Groq console

2. **Rate Limit Reached**
   - Switch to different model
   - Wait for cooldown
   - Check usage limits

3. **Task Execution Failed**
   - Check task description
   - Verify screen state
   - Monitor error messages

### Emergency Stops
- Move cursor to screen corner
- Close application
- Use task manager if needed

## Security Notes
- API keys stored locally encrypted
- No data sent to third parties
- Screen captures temporary only
- Secure credential handling

## Updates and Maintenance
- Check for updates regularly
- Keep dependencies updated
- Monitor API key validity
- Review automation logs

## Support
For issues and suggestions:
- Check error messages
- Review documentation
- Monitor system resources
- Use safe mode if needed