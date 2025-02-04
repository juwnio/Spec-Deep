from enum import Enum
from threading import Lock
from typing import Dict, Any, List, Callable
from dataclasses import dataclass

class AutomationState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class StateData:
    current_task: str = None
    last_action: str = None
    error_count: int = 0
    last_vision_data: str = None
    last_command_result: bool = None
    task_completed: bool = False

class StateObserver:
    def on_state_change(self, state: AutomationState, data: StateData):
        pass

class StateManager:
    def __init__(self):
        self._state = AutomationState.IDLE
        self._state_lock = Lock()
        self._data = StateData()
        self._data_lock = Lock()
        self._observers: List[StateObserver] = []
        
    def add_observer(self, observer: StateObserver):
        if observer not in self._observers:
            self._observers.append(observer)
        
    def remove_observer(self, observer: StateObserver):
        if observer in self._observers:
            self._observers.remove(observer)
        
    def notify_observers(self):
        for observer in self._observers:
            observer.on_state_change(self._state, self._data)
            
    def set_state(self, new_state: AutomationState):
        with self._state_lock:
            if self._state != new_state:
                self._state = new_state
                self.notify_observers()
            
    def update_data(self, **kwargs):
        with self._data_lock:
            for key, value in kwargs.items():
                if hasattr(self._data, key):
                    setattr(self._data, key, value)
        self.notify_observers()
        
    @property
    def state(self) -> AutomationState:
        with self._state_lock:
            return self._state
            
    @property
    def data(self) -> StateData:
        with self._data_lock:
            return self._data
