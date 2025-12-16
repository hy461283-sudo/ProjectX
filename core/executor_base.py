import platform
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class ExecutorBase(ABC):
    @abstractmethod
    def execute_action(self, action_type: str, issue_dict: dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Execute a remediation action.
        
        Args:
            action_type (str): The specific type of action to perform.
            issue_dict (dict): Details about the issue triggering this action.
            
        Returns:
            (success: bool, output: str, extra: dict)
        """
        pass

def get_executor() -> 'ExecutorBase':
    system = platform.system()
    if system == 'Darwin' or system == 'Linux':
        from platforms.mac.executor_mac import MacExecutor
        return MacExecutor()
    elif system == 'Windows':
        from platforms.windows.executor_windows import WindowsExecutor
        return WindowsExecutor()
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")
