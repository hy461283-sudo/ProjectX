import psutil
from core.monitor_base import MonitorBase
from core.error_handling import safe_execute

class MacMonitor(MonitorBase):
    # Simulation Flags
    SIMULATE_BITS_CRASH = True
    SIMULATE_UPDATES_PENDING = False

    @safe_execute(default_return={})
    def get_system_metrics(self):
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Top Processes
        top_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                top_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        top_processes.sort(key=lambda x: (x.get('cpu_percent') or 0.0), reverse=True)
        top_processes = top_processes[:3]

        # Services Simulation
        services = [
            {'name': 'wuauserv', 'status': 'running', 'start_type': 'Auto'}
        ]
        
        if self.SIMULATE_BITS_CRASH:
             services.append({'name': 'BITS', 'status': 'stopped', 'start_type': 'Auto'})
        else:
             services.append({'name': 'BITS', 'status': 'running', 'start_type': 'Auto'})
        
        # Updates Simulation
        updates_pending = 6 if self.SIMULATE_UPDATES_PENDING else 0
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': mem_percent,
            'disk_percent': disk_percent,
            'top_processes': top_processes,
            'services': services,
            'updates_pending': updates_pending
        }
