import re

class ModelResponseHandler:
    def __init__(self, interface):
        self.interface = interface
        
    def process_response(self, response_text):
        """Process the full model response and update UI"""
        parts = response_text.split('</think>')
        content = parts[-1].strip() if len(parts) > 1 else response_text.strip()
        
        # Extract fields with clear separation
        reason = self._extract_reason(content)
        action = self._extract_action(content)
        
        # Update displays through the display manager
        self.interface.display_manager.update_displays(reason=reason, action=action)
        
        return reason, action
    
    def _extract_reason(self, text):
        """Extract and clean reason field"""
        pattern = r'reason_for_action:\s*(.*?)(?=\n*action:|$)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_action(self, text):
        """Extract and clean action field"""
        pattern = r'action:\s*(.*?)(?=\n*reason_for_action:|$)'
        match = re.search(pattern, text, re.DOTALL)
        action = match.group(1).strip() if match else ""
        return action.replace('action:', '').strip()
