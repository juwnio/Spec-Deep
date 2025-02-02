import re

class ModelResponseHandler:
    def __init__(self, interface):
        self.interface = interface
        
    def process_response(self, response_text):
        """Process the full model response and update UI"""
        # Split on think tag if present
        parts = response_text.split('</think>')
        content = parts[-1].strip() if len(parts) > 1 else response_text.strip()
        
        # Extract reason and action
        reason = self._extract_field(content, 'reason_for_action')
        action = self._extract_field(content, 'action')
        
        # Update interface
        if reason or action:
            self.interface.update_status(reason, action)
            
        return reason, action
        
    def _extract_field(self, text, field_name):
        """Extract specific field from response text"""
        pattern = rf'{field_name}:\s*(.*?)(?=\n(?:reason_for_action|action):|$)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
