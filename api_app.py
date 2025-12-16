import os
import sys
import platform
import json
import logging
from flask import Flask, jsonify, request, send_from_directory, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import atexit

from core.logging_db import DatabaseManager
from core.analyzer import Analyzer
from core.models import Event, Action, AuditEntry
from core.executor_base import get_executor
import config

# Platform Monitor Factory
def get_monitor():
    system = platform.system()
    if system == 'Darwin' or system == 'Linux':
        from platforms.mac.monitor_mac import MacMonitor
        return MacMonitor()
    elif system == 'Windows':
        from platforms.windows.monitor_windows import WindowsMonitor
        return WindowsMonitor()
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)

def get_configured_executor():
    # If Dev, force Mac execution (dry run)
    env = getattr(config, 'ENVIRONMENT', 'dev')
    if env == 'dev':
        from platforms.mac.executor_mac import MacExecutor
        return MacExecutor()
    else:
        # Prod - use OS specific
        return get_executor()

# Initialize
app = Flask(__name__, static_folder='templates/static', template_folder='templates')
monitor = get_monitor()
executor = get_configured_executor()
db_manager = DatabaseManager()
analyzer = Analyzer(db_manager)

# Scheduler Job
def run_health_check_job():
    try:
        # 1. Monitor
        metrics = monitor.get_system_metrics()
        
        # 2. Analyze
        events = analyzer.analyze(metrics)
        
        # 3. Handle Events
        settings = db_manager.get_settings()
        
        # Determine Execution Mode
        # If Config says Dev or Auto Off, we might restrict actions
        # User Requirement: 
        # "If ENVIRONMENT == 'dev' or AUTO_REMEDIATE_ENABLED == False: Always use the Mac executor (dry-run only)" (Conceptually)
        # "If ENVIRONMENT == 'prod' and AUTO_REMEDIATE_ENABLED == True: Use Windows executor"
        
        env = getattr(config, 'ENVIRONMENT', 'dev')
        global_auto = getattr(config, 'AUTO_REMEDIATE_ENABLED', False)
        
        # User settings from DB
        db_auto_val = str(settings.get('auto_remediate', 'false')).lower()
        db_auto_enabled = db_auto_val in ['1', 'true', 'on', 'yes']
        
        # Combine Configuration
        # Logic: If global config forces OFF, it's OFF. 
        # But if global config says we are in 'dev', we force Mac Executor even if on Windows?
        # Actually `executor` is initialized at startup. We might need to swap it dynamically or just rely on platform check.
        # But task says: "If ENVIRONMENT == 'dev'... Always use Mac executor". 
        
        # Note: `executor` variable is global. We initialized it at startup.
        # If we need to support dynamic switching based on config.py (which is static usually), 
        # we should have initialized it correctly.
        # Let's adjust `get_executor` usage if needed, OR just force dry-run behavior here.
        # But `MacExecutor` is hardcoded to be dry-run. 
        # If I am on Windows but Env=Dev, I should use `MacExecutor`?
        # That requires re-initializing or having two executors.
        
        # Let's check startup logic update separately. Here we handle the `auto_remediate` flag logic.
        
        should_remediate = False
        if env == 'prod':
            should_remediate = global_auto and db_auto_enabled
        else:
            # Dev mode: We allow 'remediation' execution but it must be the MacExecutor (dry-run).
            # If default executor is MacExecutor (because we are on Mac), it's fine.
            # If we are on Windows but Config=Dev, we must ensure we don't run real commands?
            # The Task says: "If ENVIRONMENT...dev... Always use Mac executor".
            # I will assume `executor` object is the correct one.
            should_remediate = db_auto_enabled # In dev, we honor DB flag to test the flow (which logs "Would do...")

        auto_remediate = should_remediate
        
        ACTION_MAP = {
            'cpu_high': 'action_throttle_high_cpu_process',
            'memory_high': 'action_log_memory_hog',
            'disk_low': 'action_free_disk_space',
            'service_crashed': 'action_log_service_failure',
            'updates_pending': 'action_log_updates_pending'
        }

        for event in events:
            # Log Event
            event_id = db_manager.log_event(event) # Returns ID
            event.id = event_id
            
            # Auto-Remediate?
            if auto_remediate:
                action_type = ACTION_MAP.get(event.type)
                if action_type:
                    # Execute Fix via new Executor Interface
                    # Pass event fields as dict
                    issue_dict = {
                        'description': event.description,
                        'metric_value': event.metric_value,
                        'threshold': event.threshold,
                        'severity': event.severity
                    }
                    
                    success, output, extra = executor.execute_action(action_type, issue_dict)
                    
                    # Create Action Object
                    duration_ms = 0 
                    
                    action = Action(
                        timestamp=datetime.datetime.now().isoformat(),
                        type=action_type,
                        status='success' if success else 'failed',
                        output=output,
                        duration_ms=duration_ms,
                        event_id=event_id
                    )
                    
                    # Pass extra metadata
                    action_id = db_manager.log_action(action, extra=extra)
                    
                    # Create recommendation if action suggests one
                    recommendation_type = extra.get('recommendation')
                    if recommendation_type:
                        rec_text = ""
                        if recommendation_type == 'close_app':
                            process = extra.get('target_process', 'unknown')
                            rec_text = f"Close {process} to free memory"
                        elif recommendation_type == 'restart_service':
                            service = extra.get('target_service', 'unknown')
                            rec_text = f"Restart service: {service}"
                        elif recommendation_type == 'install_updates':
                            rec_text = "Install pending Windows updates"
                        
                        if rec_text:
                            db_manager.create_recommendation(
                                event_id=event_id,
                                category=event.type,
                                recommendation_text=rec_text,
                                action_type=recommendation_type,
                                priority='high' if event.severity == 'critical' else 'medium'
                            )
                    
                    # Log Audit
                    db_manager.log_audit(
                        AuditEntry(
                            timestamp=action.timestamp,
                            action_id=action_id,
                            affected_resources=event.type,
                            status=action.status
                        )
                    )
    except Exception as e:
        print(f"Error in schedule job: {e}")

# scheduler = BackgroundScheduler()
# scheduler.add_job(func=run_health_check_job, trigger="interval", seconds=30)
# scheduler.start()

# We start scheduler only if not running reloader (to avoid double jobs in dev)
# But for simplicity in this script:
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_health_check_job, trigger="interval", seconds=30)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/health')
def api_health():
    metrics = monitor.get_system_metrics()
    metrics['timestamp'] = datetime.datetime.now().isoformat()
    return jsonify(metrics)

@app.route('/api/events')
def api_events():
    events = db_manager.get_recent_events(limit=100)
    return jsonify(events)

@app.route('/api/actions')
def api_actions():
    actions = db_manager.get_recent_actions(limit=50)
    return jsonify(actions)

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(db_manager.get_settings())

@app.route('/api/settings/<key>', methods=['POST'])
def update_setting(key):
    # data = request.json # simple implementation depends on client
    # For MVP assume plain text or json
    val = request.json.get('value')
    if val is not None:
        db_manager.update_setting(key, str(val))
        return jsonify({'status': 'success', 'key': key, 'value': val})
    return jsonify({'status': 'error', 'message': 'No value provided'}), 400

@app.route('/api/actions/<action_id>/rollback', methods=['POST'])
def rollback_action(action_id):
    success = executor.rollback_action(int(action_id))
    return jsonify({'status': 'success' if success else 'failed'})

@app.route('/api/recommendations')
def get_recommendations():
    """Get all recommendations (pending and historical)."""
    recommendations = db_manager.get_all_recommendations(limit=50)
    return jsonify(recommendations)

@app.route('/api/recommendations/pending')
def get_pending_recommendations():
    """Get only pending recommendations."""
    recommendations = db_manager.get_pending_recommendations(limit=20)
    return jsonify(recommendations)

@app.route('/api/recommendations/<int:rec_id>/apply', methods=['POST'])
def apply_recommendation(rec_id):
    """Mark a recommendation as applied."""
    db_manager.update_recommendation_status(rec_id, 'applied')
    return jsonify({'status': 'success', 'recommendation_id': rec_id})

@app.route('/api/recommendations/<int:rec_id>/dismiss', methods=['POST'])
def dismiss_recommendation(rec_id):
    """Dismiss a recommendation."""
    db_manager.update_recommendation_status(rec_id, 'dismissed')
    return jsonify({'status': 'success', 'recommendation_id': rec_id})

if __name__ == '__main__':
    # Initialize DB (creates file if missing)
    db_manager.init_db()
    print("Self-Healing IT System Started")
    print(f"Platform: {platform.system()}")
    app.run(host='0.0.0.0', port=5000, debug=True)
