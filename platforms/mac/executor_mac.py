from core.executor_base import ExecutorBase
from typing import Tuple, Dict, Any
import re

SAFE_TO_KILL = ["chrome", "chromium", "firefox", "Code", "VS Code", "node", "python"]

class MacExecutor(ExecutorBase):
    def execute_action(self, action_type: str, issue_dict: dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Mock executor for macOS development.
        Logs what it would do without making system changes.
        """
        success = True
        output = ""
        extra = {}

        if action_type == 'action_kill_high_cpu_process':
            # Extract process name from description if available (e.g., "... (Top: chrome)")
            description = issue_dict.get('description', '')
            match = re.search(r"Top: ([^)]+)", description)
            target = match.group(1) if match else "unknown"
            
            extra['target_process'] = target
            
            if target in SAFE_TO_KILL:
                output = f"Would kill top CPU process: {target} (Allowed)."
            else:
                output = f"Would SKIP killing process: {target} (Not in Whitelist)."
                success = False # technically failed to act

        elif action_type == 'action_free_disk_space':
            output = "Would clean temporary files, caches, and Trash."
            extra['files_deleted'] = "temp, cache, trash"
        
        elif action_type == 'action_clear_memory_hog':
            output = "Would identify and terminate high memory consuming applications."
            extra['target_process'] = "largest_mem_process"
        
        elif action_type == 'action_restart_service':
            svc_name = "unknown"
            description = issue_dict.get('description', '')
            match = re.search(r"Service (\w+)", description)
            if match:
                svc_name = match.group(1)
            
            output = f"Would restart crashed service referenced in: {svc_name}"
            extra['target_service'] = svc_name
            
        elif action_type == 'action_handle_updates_pending':
            output = "Would restart Windows Update service (wuauserv) to finalize updates."
            extra['target_service'] = "wuauserv"
            
        else:
            success = False
            output = f"Unknown action type: {action_type}"

        return success, output, extra
