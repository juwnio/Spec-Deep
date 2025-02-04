import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import requests
import json
import re
import pyautogui
import base64
import os
import time
import ast
import win32gui
import win32con
import threading
import itertools
import math
from response_handler import ModelResponseHandler
from response_display_manager import ResponseDisplayManager
from completion_dialog import CompletionDialog
from model_selector import ModelSelector
from rate_limit_dialog import RateLimitDialog
from greeting_dialog import GreetingDialog
from api_manager import APIManager
from api_error_notification import APIErrorNotification
from settings_dialog import SettingsDialog
from state_manager import StateManager, AutomationState, StateObserver
from task_queue import TaskQueue

# Configure PyAutoGUI failsafe
pyautogui.FAILSAFE = True  # Enables failsafe corner trigger
pyautogui.FAILSAFE_POINTS = [(0, 0), (0, pyautogui.size()[1]-1),
                            (pyautogui.size()[0]-1, 0), 
                            (pyautogui.size()[0]-1, pyautogui.size()[1]-1)]

class WindowFocusManager:
    def __init__(self):
        self.last_active_window = None
    
    def store_current_focus(self):
        self.last_active_window = win32gui.GetForegroundWindow()
    
    def restore_focus(self):
        if self.last_active_window:
            # Activate the last active window
            win32gui.ShowWindow(self.last_active_window, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(self.last_active_window)

class VisionProcessor:
    def __init__(self, api_key, base_url, root_window, focus_manager):
        self.api_key = api_key
        self.base_url = base_url
        self.root_window = root_window
        self.focus_manager = focus_manager

    def capture_and_encode_screenshot(self):
        # Take screenshot directly without window manipulation
        screenshot = pyautogui.screenshot()
            
        # Save, encode, and cleanup
        screenshot.save("temp_screenshot.png")
        with open("temp_screenshot.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        os.remove("temp_screenshot.png")
        return encoded_string

    def analyze_image(self, base64_image):
        with open("context.txt", "r") as f:
            vision_context = f.read()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.2-90b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_context},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

class AutomationState:
    def __init__(self):
        self.command_history = []
        self.last_vision_response = None
        self.last_command_executed = None
        self.task_completed = False
        self.error_count = 0
        self.max_retries = 3
        self.current_task = None
        self.last_action_time = 0
        self.min_action_interval = 2.0  # Minimum seconds between actions
        self.verification_retries = 3
        self.verification_delay = 1.0  # Seconds to wait before verifying

    def add_command_to_history(self, command):
        self.command_history.append({
            'command': command,
            'timestamp': time.strftime('%H:%M:%S')
        })

    def can_execute_next_action(self):
        """Check if enough time has passed since last action"""
        current_time = time.time()
        if current_time - self.last_action_time >= self.min_action_interval:
            self.last_action_time = current_time
            return True
        return False

# Update the CommandProcessor class
class CommandProcessor:
    def __init__(self, state_manager=None, task_queue=None):
        self.state_manager = state_manager
        self.task_queue = task_queue
        self.valid_commands = ['press', 'typewrite', 'click', 'doubleClick', 'rightClick', 
                             'moveTo', 'hotkey', 'scroll', 'dragTo']
    
    def extract_commands(self, response_text):
        commands = []
        pattern = r'action:\s*pyautogui\.([^(\n]*\([^)]*\))'
        matches = re.finditer(pattern, response_text)
        
        for match in matches:
            cmd = match.group(1)
            if any(valid_cmd in cmd for valid_cmd in self.valid_commands):
                commands.append(cmd)
        return commands
    
    def execute_command(self, command):
        try:
            cmd_parts = command.split('(', 1)
            func_name = cmd_parts[0].strip()
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

class LoadingAnimation:
    def __init__(self, label):
        self.label = label
        self.running = False
        self.chars = itertools.cycle(['|', '/', '-', '\\'])
        
    def start(self):
        self.running = True
        self.animate()
        
    def stop(self):
        self.running = False
        self.label.configure(text="")
        
    def animate(self):
        if self.running:
            self.label.configure(text=next(self.chars))
            self.label.after(100, self.animate)

class UpdateQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
    
    def add_update(self, reason, action):
        with self.lock:
            self.queue.append((reason, action))
    
    def process_updates(self, interface):
        with self.lock:
            if self.queue:
                reason, action = self.queue[-1]  # Get most recent update
                self.queue.clear()
                interface.update_status(reason, action)

class ResponseParser:
    @staticmethod
    def parse_response(response_text):
        # Strip any extra whitespace and normalize newlines
        response_text = response_text.strip().replace('\r\n', '\n')
        
        # Look for patterns after any potential <think> tag
        think_split = response_text.split('</think>')
        text_to_parse = think_split[-1] if len(think_split) > 1 else response_text
        
        # Extract reason and action using more precise patterns
        reason_match = re.search(r'reason_for_action:\s*(.*?)(?=\naction:|$)', text_to_parse, re.DOTALL)
        action_match = re.search(r'action:\s*(.*?)(?=\nreason_for_action:|$)', text_to_parse, re.DOTALL)
        
        # Extract and clean the matches
        reason = reason_match.group(1).strip() if reason_match else ""
        action = action_match.group(1).strip() if action_match else ""
        
        return reason, action

class GroqInterface(StateObserver):
    def __init__(self, root):
        self.root = root
        self.root.title("Spec-Drive")
        
        # Initialize core components
        self.state_manager = StateManager()
        self.task_queue = TaskQueue()
        self.api_manager = APIManager()
        
        # Set up state observation
        self.state_manager.add_observer(self)
        
        # Initialize command processor with state and queue
        self.command_processor = CommandProcessor(self.state_manager, self.task_queue)
        
        # Add error handlers
        self.task_queue.add_error_handler(self.handle_error)
        self.task_queue.add_completion_callback(self.handle_completion)
        
        if self.api_manager.is_first_run():
            self.show_greeting()
        else:
            self.initialize_interface()
            
    def on_state_change(self, state, data):
        """Handle state changes"""
        self.update_queue.add_update(
            reason=f"State changed to: {state.value}",
            action=f"Last action: {data.last_action}"
        )
        
        if state == AutomationState.ERROR:
            self.handle_error_state()
        elif state == AutomationState.COMPLETED:
            self.show_completion_dialog()
            
    def process_workflow(self):
        if self.state_manager.state != AutomationState.IDLE:
            return
            
        self.state_manager.set_state(AutomationState.PROCESSING)
        self.loading_animation.start()
        
        threading.Thread(
            target=self._process_workflow_thread,
            daemon=True
        ).start()

    def show_greeting(self):
        """Show greeting dialog for first-time users"""
        greeting = GreetingDialog(self.root)
        self.root.wait_window(greeting.dialog)
        self.initialize_interface()
    
    def initialize_interface(self):
        """Initialize the main interface"""
        # Load API key
        self.api_key = self.api_manager.load_api_key()
        if not self.api_key:
            print("No API key found")
            self.root.quit()
            return
            
        # Set CustomTkinter theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create widgets before other components
        self.create_widgets()
        
        # Initialize components
        self.focus_manager = WindowFocusManager()
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.vision_processor = VisionProcessor(self.api_key, self.base_url, self.root, self.focus_manager)
        self.command_processor = CommandProcessor()
        self.automation_state = AutomationState()
        self.update_queue = UpdateQueue()
        self.response_parser = ResponseParser()
        self.processing = False
        self.display_manager = ResponseDisplayManager(self)
        self.response_handler = ModelResponseHandler(self)
        self.safety_monitor = None
        self.safety_check_interval = 100  # ms
        self.start_safety_monitoring()
        self.completion_dialog = None
        
        # Add periodic update checker
        self.schedule_updates()
        
        # Add API key reload capability
        self.api_manager.on_api_key_change = self.update_api_key

    def start_safety_monitoring(self):
        """Start monitoring for safety trigger conditions"""
        def check_safety():
            try:
                x, y = pyautogui.position()
                screen_width, screen_height = pyautogui.size()
                corner_threshold = 5  # pixels from corner
                
                # Check if cursor is near any corner
                if ((x <= corner_threshold and y <= corner_threshold) or  # Top-left
                    (x >= screen_width - corner_threshold and y <= corner_threshold) or  # Top-right
                    (x <= corner_threshold and y >= screen_height - corner_threshold) or  # Bottom-left
                    (x >= screen_width - corner_threshold and y >= screen_height - corner_threshold)):  # Bottom-right
                    self.emergency_stop("Safety trigger activated: Cursor in corner")
                
                # Schedule next check if not stopped
                if self.processing:
                    self.safety_monitor = self.root.after(self.safety_check_interval, check_safety)
            except Exception as e:
                print(f"Safety monitor error: {e}")

        self.safety_monitor = self.root.after(self.safety_check_interval, check_safety)

    def emergency_stop(self, reason):
        """Handle emergency stop procedure"""
        print(f"Emergency Stop: {reason}")
        self.processing = False
        self.automation_state.task_completed = True
        self.log_error(f"Emergency Stop: {reason}")
        self.loading_animation.stop()
        if self.safety_monitor:
            self.root.after_cancel(self.safety_monitor)

    def schedule_updates(self):
        """Schedule periodic UI updates"""
        if not self.processing:
            self.update_queue.process_updates(self)
        self.root.after(100, self.schedule_updates)

    def create_widgets(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Add settings button at the top right
        settings_btn = ctk.CTkButton(
            main_frame,
            text="⚙️",  # Gear emoji
            width=40,
            height=40,
            command=self.show_settings,
            font=("Segoe UI", 16)
        )
        settings_btn.pack(side="top", anchor="e", padx=5, pady=5)
        
        # Add model selector at the top
        self.model_selector = ModelSelector(main_frame)
        
        # Task input section
        task_frame = ctk.CTkFrame(main_frame)
        task_frame.pack(fill=tk.X, pady=(0, 25))
        
        task_label = ctk.CTkLabel(
            task_frame,
            text="Task:",
            font=("Segoe UI", 14, "bold")
        )
        task_label.pack(anchor='w', pady=(15, 5), padx=15)
        
        self.input_text = ctk.CTkTextbox(
            task_frame,
            height=80,
            font=("Segoe UI", 12)
        )
        self.input_text.pack(fill=tk.X, padx=15)
        
        button_frame = ctk.CTkFrame(task_frame)
        button_frame.pack(fill=tk.X, pady=(15, 15), padx=15)
        
        # Execute button
        submit_btn = ctk.CTkButton(
            button_frame,
            text="Execute Task",
            command=self.process_workflow,
            font=("Segoe UI", 12, "bold")
        )
        submit_btn.pack(side=tk.LEFT)
        
        # Loading animation
        self.loading_label = ctk.CTkLabel(button_frame, text="", width=30)
        self.loading_label.pack(side=tk.LEFT, padx=15)
        self.loading_animation = LoadingAnimation(self.loading_label)
        
        # Status section
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Reason panel
        reason_label = ctk.CTkLabel(
            status_frame,
            text="Reason for Action:",
            font=("Segoe UI", 12, "bold")
        )
        reason_label.pack(anchor='w', pady=(15, 5), padx=15)
        
        self.reason_text = ctk.CTkTextbox(
            status_frame,
            height=80,
            font=("Segoe UI", 12)
        )
        self.reason_text.pack(fill=tk.X, padx=15)
        
        # Action panel
        action_label = ctk.CTkLabel(
            status_frame,
            text="Action:",
            font=("Segoe UI", 12, "bold")
        )
        action_label.pack(anchor='w', pady=(15, 5), padx=15)
        
        self.action_text = ctk.CTkTextbox(
            status_frame,
            height=80,
            font=("Segoe UI", 12)
        )
        self.action_text.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Make text widgets read-only
        self.reason_text.configure(state="disabled")
        self.action_text.configure(state="disabled")

    def show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self.root, self.api_manager, self.api_key)

    def process_workflow(self):
        if self.processing:
            return  # Prevent multiple simultaneous runs
        self.processing = True
        self.loading_animation.start()
        self.start_safety_monitoring()  # Restart safety monitoring
        threading.Thread(target=self._process_workflow_thread, daemon=True).start()

    def _process_workflow_thread(self):
        try:
            user_prompt = self.input_text.get("1.0", tk.END).strip()
            self.automation_state = AutomationState()
            self.execute_automation_loop(user_prompt)
        except Exception as e:
            self.log_error(f"Workflow error: {str(e)}")
        finally:
            self.processing = False
            if self.safety_monitor:
                self.root.after_cancel(self.safety_monitor)
            self.root.after(0, self.loading_animation.stop)

    def update_status(self, reason, action):
        """Update the status displays thread-safely"""
        self.root.after(0, lambda: self.display_manager.update_displays(reason=reason, action=action))

    def execute_automation_loop(self, user_prompt):
        self.automation_state.current_task = user_prompt
        
        try:
            # Add timeout protection
            start_time = time.time()
            max_execution_time = 300  # 5 minutes timeout
            
            while not self.automation_state.task_completed:
                if time.time() - start_time > max_execution_time:
                    self.emergency_stop("Maximum execution time exceeded")
                    break

                # Rate limiting check
                if not self.automation_state.can_execute_next_action():
                    time.sleep(0.5)  # Short sleep if we need to wait
                    continue

                # Get vision analysis
                vision_response = self.get_vision_analysis()
                if not vision_response:
                    self.automation_state.error_count += 1
                    continue

                # Get DeepSeek response
                deepseek_response = self.get_deepseek_response(vision_response, user_prompt)
                if not deepseek_response:
                    self.automation_state.error_count += 1
                    continue

                # Extract commands
                commands = self.command_processor.extract_commands(deepseek_response)
                if not commands:
                    self.automation_state.error_count += 1
                    continue

                # Execute command with verification
                cmd = commands[0]
                if self.execute_and_verify_command(cmd, vision_response):
                    self.automation_state.add_command_to_history(cmd)
                    self.automation_state.error_count = 0  # Reset error count on success
                else:
                    self.automation_state.error_count += 1
                    if self.automation_state.error_count >= self.automation_state.max_retries:
                        self.log_error("Max retries reached. Stopping automation.")
                        break

                # Check for completion
                if self.check_task_completion(deepseek_response):
                    # Verify completion state
                    time.sleep(self.automation_state.verification_delay)
                    final_vision = self.get_vision_analysis()
                    if self.verify_completion(final_vision):
                        break
                    else:
                        continue

                # Ensure minimum delay between iterations
                time.sleep(self.automation_state.verification_delay)
                self.root.update()

        except Exception as e:
            self.log_error(f"Loop iteration error: {str(e)}")
            self.emergency_stop(f"Critical error: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources and state"""
        self.processing = False
        if self.safety_monitor:
            self.root.after_cancel(self.safety_monitor)
        self.loading_animation.stop()
        self.automation_state.task_completed = True

    def execute_and_verify_command(self, command, previous_vision):
        """Execute command and verify its effect"""
        try:
            if not self.command_processor.execute_command(command):
                return False

            # Wait for action to take effect
            time.sleep(self.automation_state.verification_delay)
            
            # Get new vision analysis
            new_vision = self.get_vision_analysis()
            if new_vision == previous_vision:
                # No change detected, might need retry
                return False

            self.automation_state.last_command_executed = command
            return True

        except Exception as e:
            self.log_error(f"Command execution/verification error: {str(e)}")
            return False

    def verify_completion(self, vision_response):
        """Verify that the task is actually completed"""
        try:
            # Add specific completion verification logic based on the task
            if "error" in vision_response.lower() or "fail" in vision_response.lower():
                return False
                
            # Basic verification passed
            return True
        except Exception as e:
            self.log_error(f"Completion verification error: {str(e)}")
            return False

    def get_vision_analysis(self):
        try:
            base64_image = self.vision_processor.capture_and_encode_screenshot()
            vision_response = self.vision_processor.analyze_image(base64_image)
            self.automation_state.last_vision_response = vision_response
            return vision_response
        except Exception as e:
            error_msg = str(e)
            if "429 Client Error: Too Many Requests" in error_msg:
                self.show_rate_limit_dialog()
                return None
            elif "401 Client Error: Unauthorized" in error_msg:
                self.show_api_error()
                return None
            self.log_error(f"Vision analysis error: {error_msg}")
            return None
    
    def show_api_error(self):
        """Show API error notification"""
        self.emergency_stop("Invalid API key")
        self.root.after(0, lambda: APIErrorNotification(self.root))

    def show_rate_limit_dialog(self):
        """Show rate limit exceeded dialog"""
        self.emergency_stop("Rate limit exceeded")
        self.root.after(0, lambda: RateLimitDialog(self.root))

    def get_deepseek_response(self, vision_response, user_prompt):
        try:
            with open("context2.txt", "r") as f:
                final_context = f.read()
            
            history_text = "\n".join([
                f"Previously executed: {h['command']} at {h['timestamp']}"
                for h in self.automation_state.command_history
            ])
            
            combined_prompt = (
                f"{final_context}\n\n"
                f"COMMAND HISTORY:\n{history_text}\n\n"
                f"UPDATE OF SCREEN:\n{vision_response}\n\n"
                f"ORIGINAL TASK: {self.automation_state.current_task}\n\n"
                f"CURRENT PROMPT: {user_prompt}"
            )
            
            return self.send_to_deepseek(combined_prompt)
        except Exception as e:
            self.log_error(f"DeepSeek response error: {str(e)}")
            return None

    def check_task_completion(self, response):
        if ("reason_for_action: Task successfully completed" in response and 
            "action: done" in response):
            self.automation_state.task_completed = True
            # Stop processing
            self.processing = False
            # Stop loading animation
            self.loading_animation.stop()
            # Cancel safety monitor
            if self.safety_monitor:
                self.root.after_cancel(self.safety_monitor)
            # Show completion dialog
            self.show_completion_dialog()
            return True
        return False

    def show_completion_dialog(self):
        """Show task completion dialog"""
        self.root.after(0, lambda: CompletionDialog(self.root))

    def execute_single_command(self, command):
        try:
            success = self.command_processor.execute_command(command)
            if success:
                self.automation_state.last_command_executed = command
            return success
        except Exception as e:
            self.log_error(f"Command execution error: {str(e)}")
            return False

    def log_status(self, status_message):
        print(f"Status: {status_message}")
        self.update_status("Status Update", status_message)  # Changed to separate reason and action
        self.root.update()

    def execute_commands(self, response):
        try:
            commands = self.command_processor.extract_commands(response)
            if not commands:
                return False
                
            for cmd in commands:
                success = self.command_processor.execute_command(cmd)
                if not success:
                    return False
                self.automation_state.last_command_executed = cmd
                self.root.update()  # Update GUI
                time.sleep(3)  # Wait between commands
            return True
        except Exception as e:
            self.log_error(f"Command execution error: {str(e)}")
            return False

    def log_error(self, error_message):
        print(f"Error: {error_message}")
        self.update_status("Error occurred", error_message)  # Separated error reason from message
        self.root.update()

    def send_to_deepseek(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_selector.get_selected_model(),
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
            # Process response through handler
            reason, action = self.response_handler.process_response(response_text)
            
            return response_text
            
        except Exception as e:
            error_msg = str(e)
            if "401 Client Error: Unauthorized" in error_msg:
                self.show_api_error()
            self.display_manager.update_displays(
                reason="Error occurred",
                action=str(e)
            )
            return ""

    def update_api_key(self, new_key):
        """Update API key and reinitialize components that use it"""
        self.api_key = new_key
        if hasattr(self, 'vision_processor'):
            self.vision_processor.api_key = new_key

    def handle_error(self, task, error):
        """Handle task queue errors"""
        self.log_error(f"Task error: {error}")
        self.state_manager.set_state(AutomationState.ERROR)
        
    def handle_completion(self, task, result):
        """Handle task completion"""
        self.log_status(f"Task completed: {result}")
        if not self.task_queue.task_queue.empty():
            self.state_manager.set_state(AutomationState.PROCESSING)
        else:
            self.state_manager.set_state(AutomationState.COMPLETED)

if __name__ == "__main__":
    root = ctk.CTk()
    app = GroqInterface(root)
    root.geometry("600x500")
    root.mainloop()
