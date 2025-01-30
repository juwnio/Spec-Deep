import pyautogui
import yaml
import time
import asyncio
from typing import Dict, Any, Optional, Tuple

class ActionExecutor:
    @staticmethod
    def parse_yaml_response(response: str) -> Tuple[str, str]:
        """Parse YAML response into reason and action."""
        try:
            # Remove any non-YAML content
            yaml_content = response.split('```yaml')[-1].split('```')[0] if '```' in response else response
            data = yaml.safe_load(yaml_content)
            return data.get('reason_for_action', ''), data.get('action', '')
        except Exception as e:
            raise ValueError(f"Failed to parse YAML response: {str(e)}")
    
    @staticmethod
    def execute_command(action: str) -> bool:
        """Execute PyAutoGUI command safely."""
        try:
            if not action or action.lower() == 'done':
                return False
                
            # Remove any python formatting
            action = action.replace('python', '').replace('```', '').strip()
            
            # Validate command starts with pyautogui
            if not action.startswith('pyautogui.'):
                raise ValueError(f"Invalid command format: {action}")
            
            # Execute the command
            exec(action)
            return True
            
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
