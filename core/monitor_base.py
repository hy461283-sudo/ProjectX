from abc import ABC, abstractmethod
from typing import Dict, Any

class MonitorBase(ABC):
    @abstractmethod
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Collect and return system metrics.
        Expected format:
        {
            'cpu_percent': float,
            'memory_percent': float,
            'disk_percent': float,
            'top_processes': [{'name': str, 'pid': int, 'cpu': float}],
            'services': [{'name': str, 'status': str, 'start_type': str}],
            'updates_pending': int
        }
        """
        pass
