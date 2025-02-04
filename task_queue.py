from queue import Queue
from threading import Lock, Event
from typing import Callable, Any, Dict, List
import time

class TaskQueue:
    def __init__(self, max_size=100):
        self.task_queue = Queue(maxsize=max_size)
        self.result_queue = Queue()
        self.processing_lock = Lock()
        self.stop_event = Event()
        self.error_handlers: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        self.last_task_time = 0
        self.min_task_interval = 1.0  # Minimum seconds between tasks
        
    def add_task(self, task: Dict[str, Any], priority: int = 1):
        """Add task to queue with priority and timestamp"""
        task.update({
            'timestamp': time.time(),
            'priority': priority,
            'status': 'pending',
            'retries': 0
        })
        self.task_queue.put(task)
    
    def get_next_task(self):
        """Get next task from queue with rate limiting"""
        if not self.task_queue.empty():
            current_time = time.time()
            if current_time - self.last_task_time >= self.min_task_interval:
                self.last_task_time = current_time
                return self.task_queue.get()
        return None
        
    def add_error_handler(self, handler: Callable):
        """Add error handler callback"""
        if handler not in self.error_handlers:
            self.error_handlers.append(handler)
        
    def add_completion_callback(self, callback: Callable):
        """Add completion callback"""
        if callback not in self.completion_callbacks:
            self.completion_callbacks.append(callback)
        
    def handle_error(self, task: Dict[str, Any], error: Exception):
        """Process task error through registered handlers"""
        for handler in self.error_handlers:
            try:
                handler(task, error)
            except Exception as e:
                print(f"Error in error handler: {e}")
            
    def notify_completion(self, task: Dict[str, Any], result: Any):
        """Notify completion callbacks of task completion"""
        for callback in self.completion_callbacks:
            try:
                callback(task, result)
            except Exception as e:
                print(f"Error in completion callback: {e}")
            
    def clear(self):
        """Clear all queues"""
        while not self.task_queue.empty():
            self.task_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()
            
    def stop(self):
        """Stop queue processing"""
        self.stop_event.set()
        self.clear()
