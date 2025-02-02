# AI-Powered Task Automation System 💻  (⊙_⊙;)

## Overview
This program is an AI-powered automation system that combines computer vision and language models to perform automated tasks on Windows. It uses screenshots for visual analysis and converts high-level user instructions into PyAutoGUI commands.

## Core Components

### 1. Visual Analysis System
- Uses LLaVA vision model for screenshot analysis
- Captures and processes screen content
- Provides structured analysis of UI elements and content
- Handles window management during captures

### 2. Command Generation
- Uses Groq's language model for decision making
- Converts visual analysis into concrete actions
- Follows strict single-command protocol
- Prioritizes keyboard shortcuts over mouse actions

### 3. Execution System
- Executes PyAutoGUI commands safely
- Verifies command execution success
- Maintains command history
- Implements safety measures and failsafes

# Key Features

- **Safety First**: 
  - Corner trigger failsafe
  - Command verification
  - Error recovery
  - Rate limiting

- **Smart Navigation**: 
  - Prefers keyboard shortcuts
  - Uses Windows search for navigation
  - Maintains context awareness
  - Adapts to screen changes

- **Robust Error Handling**:
  - Command verification
  - Retry mechanisms
  - Error logging
  - Graceful failure recovery

## How It Works

1. **Task Input**
   - User enters task description
   - Interface initializes safety monitoring
   - Automation state is prepared

2. **Automation Loop**
   ```
   1. Capture screenshot
   2. Analyze visual content
   3. Generate next action
   4. Execute command
   5. Verify result
   6. Repeat until complete
   ```

3. **Command Processing**
   - Single command execution
   - Minimum delay between actions
   - Success verification
   - History tracking

4. **Status Updates**
   - Real-time feedback in UI
   - Reason for each action
   - Command execution status
   - Error reporting

# Setup Requirements

```bash
pip install -r requirements.txt
```

## Required packages:
- customtkinter
- pyautogui
- Pillow
- requests
- pywin32
- python-dotenv
- typing-extensions

Configuration Files

1. **context.txt**: Vision model instructions
   - UI element detection
   - Screen content analysis
   - Visual hierarchy understanding

2. **context2.txt**: Automation instructions
   - Command rules
   - Safety measures
   - Response format
   - Operation priorities

# Usage

1. Start the program:
   ```bash
   python groq_interface.py
   ```

2. Enter your task in the input field
3. Click "Execute Task"
4. Monitor progress in the status panels
5. Move cursor to corner to stop execution

# Safety Notes

- Move cursor to screen corner for emergency stop
- Program enforces minimum delays between actions
- All commands are verified before continuing
- Automatic error recovery with retry limits

# Error Handling

- Maximum retry limit for failed commands
- Automatic error logging
- Visual verification of actions
- Graceful shutdown on critical errors

# Development

The system is modular with these key classes:
- `GroqInterface`: Main UI and control flow
- `VisionProcessor`: Screenshot and analysis
- `CommandProcessor`: Command handling
- `AutomationState`: State management
- `ModelResponseHandler`: AI response processing
