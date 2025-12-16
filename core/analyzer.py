from typing import List, Optional
from .models import Event
import datetime

class Analyzer:
    def __init__(self, db_manager):
        self.db = db_manager

    def analyze(self, metrics: dict) -> List[Event]:
        settings = self.db.get_settings()
        events = []
        timestamp = datetime.datetime.now().isoformat()

        # 1. Check CPU
        cpu_threshold = float(settings.get('cpu_threshold', 80.0))
        if metrics['cpu_percent'] > cpu_threshold:
            # Try to identify culprit for description
            top_process = "unknown"
            if metrics.get('top_processes'):
                # Assumes top_processes is sorted desc
                top_process = metrics['top_processes'][0].get('name', 'unknown')
            
            events.append(Event(
                timestamp=timestamp,
                type='cpu_high',
                severity='warning' if metrics['cpu_percent'] < 95 else 'critical',
                description=f"CPU usage is at {metrics['cpu_percent']}% (Top: {top_process})",
                metric_value=metrics['cpu_percent'],
                threshold=cpu_threshold
            ))

        # 2. Check Memory
        mem_threshold = float(settings.get('memory_threshold', 85.0))
        if metrics['memory_percent'] > mem_threshold:
            events.append(Event(
                timestamp=timestamp,
                type='memory_high',
                severity='warning',
                description=f"Memory usage is at {metrics['memory_percent']}%",
                metric_value=metrics['memory_percent'],
                threshold=mem_threshold
            ))

        # 3. Check Disk
        disk_threshold = float(settings.get('disk_threshold', 90.0))
        if metrics['disk_percent'] > disk_threshold:
            events.append(Event(
                timestamp=timestamp,
                type='disk_low',
                severity='critical',
                description=f"Disk usage is at {metrics['disk_percent']}%",
                metric_value=metrics['disk_percent'],
                threshold=disk_threshold
            ))

        # 4. Check Services (Platform specific logic handles what services are checked)
        if 'services' in metrics:
            for service in metrics['services']:
                # Logic: Service down + StartType=Automatic -> service_crashed
                if service['status'] != 'running' and service.get('start_type') == 'Auto': # 'Auto' might need mapping
                    events.append(Event(
                        timestamp=timestamp,
                        type='service_crashed',
                        severity='critical',
                        description=f"Service {service['name']} is stopped but set to Auto start.",
                        metric_value=0, # Binary state
                        threshold=1
                    ))

        # 5. Check Updates
        updates_threshold = int(settings.get('updates_pending_threshold', 5))
        if metrics.get('updates_pending', 0) > updates_threshold:
            events.append(Event(
                timestamp=timestamp,
                type='updates_pending',
                severity='warning',
                description=f"{metrics['updates_pending']} Windows updates are pending.",
                metric_value=metrics['updates_pending'],
                threshold=updates_threshold
            ))

        return events
