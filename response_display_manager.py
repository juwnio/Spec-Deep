import tkinter as tk

class ResponseDisplayManager:
    def __init__(self, interface):
        self.interface = interface
        self.current_reason = ""
        self.current_action = ""
    
    def update_displays(self, reason=None, action=None):
        """Update display panels with new content"""
        if reason is not None:
            self.current_reason = reason
            self._update_reason_panel(reason)
        
        if action is not None:
            self.current_action = action
            self._update_action_panel(action)
    
    def _update_reason_panel(self, reason):
        """Update reason panel with new content"""
        def _update():
            self.interface.reason_text.configure(state="normal")
            self.interface.reason_text.delete("1.0", tk.END)
            self.interface.reason_text.insert(tk.END, reason)
            self.interface.reason_text.configure(state="disabled")
        self.interface.root.after(0, _update)
    
    def _update_action_panel(self, action):
        """Update action panel with new content"""
        def _update():
            self.interface.action_text.configure(state="normal")
            self.interface.action_text.delete("1.0", tk.END)
            self.interface.action_text.insert(tk.END, action)
            self.interface.action_text.configure(state="disabled")
        self.interface.root.after(0, _update)
