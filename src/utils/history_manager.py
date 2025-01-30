from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CommandHistory:
    timestamp: str
    reason: str
    action: str
    success: bool

class HistoryManager:
    def __init__(self):
        self.command_history: List[CommandHistory] = []
        self.objective: str = ""
    
    def set_objective(self, objective: str) -> None:
        self.objective = objective
    
    def add_command(self, reason: str, action: str, success: bool) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.command_history.append(
            CommandHistory(timestamp, reason, action, success)
        )
    
    def format_history(self) -> str:
        if not self.command_history:
            return "No actions executed yet."
            
        history = f"Original Objective: {self.objective}\n\nCommand History:\n"
        for cmd in self.command_history:
            status = "✓" if cmd.success else "✗"
            history += f"[{cmd.timestamp}] {status} {cmd.reason} -> {cmd.action}\n"
        return history
    
    def clear(self) -> None:
        self.command_history.clear()
        self.objective = ""
