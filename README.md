# ProjectX - Self-Healing Windows System Monitor

## What It Does
- **Monitors** CPU, Memory, Disk, and Windows Services in real-time
- **Auto-throttles** high-CPU processes (lowers priority instead of killing)
- **Cleans up** temp files when disk space is low
- **Logs recommendations** for memory-heavy apps and stopped services
- **Web dashboard** to view system health and manage settings

## Installation (For End Users)

### Quick Install
1. Download `ProjectX-Setup.exe`
2. Run as Administrator (right-click → Run as administrator)
3. Open your browser to **http://localhost:5000**
4. Adjust thresholds in Settings if needed
5. Enable **Auto-Remediate** toggle to activate monitoring

### Manual Install (Developers)
```bash
# Clone repository
git clone https://github.com/yourusername/ProjectX.git
cd ProjectX

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from core.logging_db import DatabaseManager; DatabaseManager().init_db()"

# Run application
python api_app.py
```

## Usage

### Dashboard
- Navigate to **http://localhost:5000**
- View real-time system metrics (CPU, Memory, Disk)
- See recent events and actions taken
- Manage settings and thresholds

### Settings
- **CPU Threshold**: Default 80% - triggers throttling when exceeded
- **Memory Threshold**: Default 85% - triggers logging and recommendations
- **Disk Threshold**: Default 90% - triggers temp file cleanup
- **Auto-Remediate**: Enable to allow automatic actions

### What Happens When Issues Are Detected

| Issue | Action Taken | Result |
|-------|--------------|--------|
| High CPU | Lowers process priority to "Below Normal" | Process continues running but uses less CPU |
| High Memory | Logs memory usage + creates recommendation | Dashboard shows "Close [app] to free memory" |
| Disk Full | Cleans temp folders and recycle bin | Frees up disk space safely |
| Service Stopped | Logs service failure + creates recommendation | Dashboard shows "Restart [service]" button |
| Updates Pending | Logs pending updates + creates recommendation | Dashboard shows "Install updates" reminder |

**Important:** No processes are killed, no services are auto-restarted. You stay in control.

## Configuration

Edit `config.py` to change behavior:

```python
ENVIRONMENT = "prod"              # "dev" or "prod"
AUTO_REMEDIATE_ENABLED = True     # Enable/disable auto-remediation
```

## API Endpoints

- `GET /api/health` - Current system metrics
- `GET /api/events` - Recent events
- `GET /api/actions` - Actions taken
- `GET /api/recommendations/pending` - Pending recommendations
- `POST /api/recommendations/<id>/apply` - Mark recommendation as applied
- `POST /api/recommendations/<id>/dismiss` - Dismiss recommendation
- `GET /api/settings` - Current settings
- `POST /api/settings/<key>` - Update setting

## Troubleshooting

### Application Won't Start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process if needed
taskkill /PID <PID> /F

# Restart application
.\venv\Scripts\python.exe api_app.py
```

### Auto-Remediate Not Working
1. Check `config.py` - ensure `AUTO_REMEDIATE_ENABLED = True`
2. Check dashboard settings - ensure auto_remediate toggle is ON
3. Check logs in terminal for errors

### Process Not Being Throttled
- Check if process is in the whitelist (see `executor_windows.py`)
- System processes (MsMpEng, svchost, etc.) are never throttled for safety
- Check action logs to see if throttling was attempted

## How to Uninstall

### Using Installer
1. Control Panel → Programs and Features
2. Find "ProjectX"
3. Click Uninstall

### Manual Uninstall
1. Stop the application (Ctrl+C in terminal)
2. Delete the ProjectX folder
3. Remove any scheduled tasks (if configured)

## Support
- **Email**: support@projectx.com
- **Documentation**: https://github.com/yourusername/ProjectX/wiki
- **Issues**: https://github.com/yourusername/ProjectX/issues

## License
MIT License - See LICENSE file for details

## Credits
Developed by [Your Name/Team]
