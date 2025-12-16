from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class Event:
    timestamp: str
    type: str  # e.g., 'cpu_high', 'disk_low'
    severity: str  # 'warning', 'critical'
    description: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    id: Optional[int] = None

@dataclass
class Action:
    timestamp: str
    type: str  # e.g., 'kill_process', 'clear_temp'
    status: str  # 'success', 'failed', 'pending'
    output: str
    duration_ms: int
    event_id: Optional[int] = None
    id: Optional[int] = None

@dataclass
class AuditEntry:
    timestamp: str
    action_id: int
    affected_resources: str
    status: str
    id: Optional[int] = None
