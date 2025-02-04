import pyautogui
import ast
from typing import List, Dict
from task_queue import TaskQueue
from state_manager import StateManager, AutomationState

class CommandProcessor:
    def __init__(self, state_manager: StateManager, task_queue: TaskQueue):
        self.state_manager = state_manager
        self.task_queue = task_queue
        self.valid_commands = ['press', 'typewrite', 'click', 'doubleClick', 
                             'rightClick', 'moveTo', 'hotkey', 'scroll', 'dragTo']
        
    def process_command_queue(self):
        """Process commands from the task queue"""
        while not self.task_queue.stop_event.is_set():
            task = self.task_queue.get_next_task()
            if not task:
                continue
                
            try:
                result = self.execute_command(task['command'])
                if result:
                    self.state_manager.update_data(
                        last_command_result=True,
                        last_action=task['command']
                    )
                    self.task_queue.notify_completion(task, result)
                else:
                    raise Exception("Command execution failed")
                    
            except Exception as e:
                self.state_manager.update_data(
                    last_command_result=False,
                    error_count=self.state_manager.data.error_count + 1
                )
                self.task_queue.handle_error(task, e)
                
    def execute_command(self, command: str) -> bool:
        """Execute a single PyAutoGUI command"""
        try:
            cmd_parts = command.split('(', 1)
            func_name = cmd_parts[0].strip()
            
            if func_name not in self.valid_commands:
                raise ValueError(f"Invalid command: {func_name}")
                
            args_str = '(' + cmd_parts[1]
            args = ast.literal_eval(args_str)
            
            func = getattr(pyautogui, func_name)
            
            if isinstance(args, tuple):
                func(*args)
            else:
                func(args)
            return True
            
        except Exception as e:
            print(f"Command execution error: {e}")
            return False
