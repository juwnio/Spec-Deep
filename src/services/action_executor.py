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
            # Validate action format
            if not action or action.lower() == 'done':
                return False
                
            # Parse command and parameters
            parts = action.replace('pyautogui.', '').split('(')
            if len(parts) != 2:
                raise ValueError("Invalid command format")
                
            command = parts[0].strip()
            params = parts[1].rstrip(')').split(',')
            
            # Validate command exists in pyautogui
            if not hasattr(pyautogui, command):
                raise ValueError(f"Invalid command: {command}")
            
            # Parse parameters safely
            parsed_params = []
            for p in params:
                p = p.strip()
                try:
                    # Handle string literals
                    if p.startswith('"') or p.startswith("'"):
                        parsed_params.append(p.strip("'\""))
                    # Handle numeric values
                    else:
                        parsed_params.append(float(p) if '.' in p else int(p))
                except ValueError:
                    raise ValueError(f"Invalid parameter value: {p}")
            
            # Execute command with safety delay
            pyautogui.PAUSE = 1.0  # Add safety delay between commands
            func = getattr(pyautogui, command)
            func(*parsed_params)
            return True
            
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
