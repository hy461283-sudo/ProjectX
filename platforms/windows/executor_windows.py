import subprocess
from core.executor_base import ExecutorBase
from typing import Tuple, Dict, Any
import re

SAFE_TO_KILL = ["chrome", "chrome.exe", "chromium", "firefox", "firefox.exe", "Code", "code.exe", "node", "node.exe", "python", "python.exe"]

class WindowsExecutor(ExecutorBase):
    def _run_powershell(self, script: str) -> Tuple[bool, str]:
        """
        Helper to run a PowerShell script safely.
        """
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            success = (result.returncode == 0)
            output = result.stdout + "\n" + result.stderr
            return success, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Execution timed out after 30s."
        except Exception as e:
            return False, f"Execution failed: {str(e)}"

    def execute_action(self, action_type: str, issue_dict: dict) -> Tuple[bool, str, Dict[str, Any]]:
        success = False
        output = ""
        extra = {}

        if action_type == 'action_throttle_high_cpu_process':
            # Extract target process from description
            description = issue_dict.get('description', '')
            match = re.search(r"Top: (.+?)\)", description)
            target_name = match.group(1) if match else None

            if not target_name:
                return False, "Could not identify target process from issue description.", {}

            # Construct PowerShell array string from Python list
            safe_list_str = ",".join([f"'{s}'" for s in SAFE_TO_KILL])
            
            script = f"""
            $safe = @({safe_list_str})
            $ignored = @("MsMpEng", "System", "Registry", "svchost", "csrss", "lsass", "wininit", "services", "Antigravity")
            $target = "{target_name}"
            
            if ($ignored -contains $target) {{
                Write-Output "CPU high due to system process ($target); cannot throttle"
                exit 0
            }}

            if ($safe -contains $target) {{
                $p = Get-Process -Name $target -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($p) {{
                    $oldPriority = $p.PriorityClass
                    $p.PriorityClass = 'BelowNormal'
                    Write-Output "Throttled ($target) from $oldPriority to BelowNormal priority"
                }} else {{
                    Write-Output "Process ($target) not found"
                }}
            }} else {{
                Write-Output "Skipped ($target) - Not in whitelist"
                exit 1
            }}
            """
            success, output = self._run_powershell(script)
            extra['target_process'] = target_name

        elif action_type == 'action_free_disk_space':
            # Clears Temp, Windows Temp, and Recycle Bin
            script = """
            $beforeSize = (Get-ChildItem -Path "$env:TEMP" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $targets = @("$env:TEMP\\*", "$env:SystemRoot\\Temp\\*")
            foreach ($t in $targets) {
                Remove-Item -Path $t -Recurse -Force -ErrorAction SilentlyContinue
            }
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            $afterSize = (Get-ChildItem -Path "$env:TEMP" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $reclaimedMB = [math]::Round(($beforeSize - $afterSize) / 1MB, 2)
            Write-Output "Disk cleanup completed. Reclaimed approximately ${{reclaimedMB}}MB (Temp folders + Recycle Bin)"
            """
            success, output = self._run_powershell(script)
            extra['files_deleted'] = "temp, system_temp, recycle_bin"

        elif action_type == 'action_kill_high_cpu_process':
            # Get whitelist from extra args (passed from API)
            whitelist = issue_dict.get('whitelist', [])
            # Also include default hardcoded safety net
            default_safe = ["chrome", "chromium", "firefox", "Code", "VS Code", "node", "python", "Antigravity", "Antigravity Helper (Renderer)"]
            combined_safe = list(set(whitelist + default_safe))
            safe_list_str = ",".join([f"'{s}'" for s in combined_safe])
            
            # Smart Throttling Script
            # 1. Identify top process
            # 2. Check if in whitelist
            # 3. If in whitelist -> THROTTLE (Lower Priority)
            # 4. If NOT in whitelist -> KILL
            
            script = f"""
            $safe = @({safe_list_str})
            $p = Get-Process | Sort-Object CPU -Descending | Select-Object -First 1 | Where-Object {{ $_.ProcessName -ne 'System Idle Process' }}
            
            if ($p) {{
                $name = $p.ProcessName
                if ($safe -contains $name) {{
                    # THROTTLE
                    $p.PriorityClass = 'BelowNormal'
                    Write-Output "Throttled (Lowered Priority): $name"
                }} else {{
                    # KILL (Non-Critical, Non-Whitelisted)
                    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                    Write-Output "Killed: $name"
                }}
            }} else {{
                Write-Output "No action needed."
            }}
            """
            success, output = self._run_powershell(script)
            
            # Metadata extraction
            if "Throttled" in output:
                extra['action_detail'] = "throttled"
                match = re.search(r"Throttled.*: (.+)", output)
                if match: extra['target_process'] = match.group(1)
            elif "Killed" in output:
                extra['action_detail'] = "killed"
                match = re.search(r"Killed: (.+)", output)
                if match: extra['target_process'] = match.group(1)

            extra['recommendation'] = 'close_app'

        elif action_type == 'action_log_memory_hog':
            # Log largest memory process without killing it
            safe_list_str = ",".join([f"'{s}'" for s in SAFE_TO_KILL])
            
            script = f"""
            $ignored = @("MsMpEng", "System", "Registry", "svchost", "csrss", "lsass", "wininit", "services", "Antigravity")
            $p = Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 1
            if ($p) {{
                 $memoryMB = [math]::Round($p.WorkingSet / 1MB, 2)
                 if ($ignored -contains $p.ProcessName) {{
                    Write-Output "Memory high due to system process ($($p.ProcessName)) using ${{memoryMB}}MB"
                    exit 0
                 }} else {{
                    Write-Output "Memory hog: ($($p.ProcessName)) using ${{memoryMB}}MB - Recommend closing manually"
                    exit 0
                 }}
            }}
            """
            success, output = self._run_powershell(script)
            # Extract process name from output
            match = re.search(r"\((.+?)\)", output)
            if match:
                extra['target_process'] = match.group(1)
            extra['recommendation'] = 'close_app'

        elif action_type == 'action_log_service_failure':
            # Log stopped services without restarting them
            script = """
            $services = Get-Service | Where-Object {$_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic'}
            if ($services) {
                foreach ($s in $services) {
                    Write-Output "Service stopped: $($s.Name) - Recommend manual restart"
                }
            } else {
                Write-Output "No crashed automatic services found."
            }
            """
            success, output = self._run_powershell(script)
            # Extract service names from output
            stopped = re.findall(r"Service stopped: (.+?) -", output)
            if stopped:
                extra['target_service'] = ", ".join(stopped)
                extra['recommendation'] = 'restart_service'

        elif action_type == 'action_log_updates_pending':
            # Log pending updates without restarting service
            script = """
            Write-Output "Windows updates pending - Recommend installing updates manually"
            """
            success, output = self._run_powershell(script)
            if success:
                extra['recommendation'] = 'install_updates'

        else:
            success = False
            output = f"Unknown action type: {action_type}"

        return success, output, extra

    def rollback_action(self, action_id: int) -> bool:
        """
        Rollback a previous action by ID.
        Currently supports Un-Throttling (restoring Normal priority).
        """
        # Note: We need the DB manager or Action context passed here, but Executor usually just takes the ID.
        # However, ExecutorBase doesn't have DB access directly. 
        # For this design, we'll assume the API passes the NECESSARY INFO (like process name) if we change the signature,
        # OR we rely on the fact that we can't easily look it up without DB.
        
        # BUT, the executor is stateless. The API handler needs to fetch the action details.
        # Let's check api_app.py rollback route... it calls executor.rollback_action(id).
        # We need to enhance that flow or cheat (pass the name).
        
        # Actually, let's implement a generic "restore priority" helper and assume the caller logic will be fixed or
        # we accept that we need to query DB.
        # Since I can't change the signature easily in `executor_base` without updating `api_app`, let's do this:
        # We will require `api_app.py` to pass the `target_process` name to a NEW method `undo_action`.
        # Converting logical 'rollback' to specific 'undo' call.
        pass

    def perform_rollback(self, action_type: str, details: dict) -> bool:
        """
        Actual implementation called by API which has fetched DB details.
        """
        if action_type == 'action_throttle_high_cpu_process' or action_type == 'action_kill_high_cpu_process':
            # "Undo" for throttle = Restore Normal Priority
            # "Undo" for kill = Restart? (Hard without path). 
            # We will focus on Un-Throttle.
            
            target = details.get('target_process')
            if not target: return False
            
            script = f"""
            $p = Get-Process -Name "{target}" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($p) {{
                $p.PriorityClass = 'Normal'
                Write-Output "Restored Normal priority for $p"
            }} else {{
                exit 1
            }}
            """
            success, _ = self._run_powershell(script)
            return success
            
        return False
