const API_BASE = '/api';

// State
let charts = {};

async function updateMetrics() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();

        // Update DOM
        updateCard('cpu', data.cpu_percent, data.top_processes);
        updateCard('mem', data.memory_percent);
        updateCard('disk', data.disk_percent);

        document.getElementById('connection-status').textContent = `Live: ${new Date().toLocaleTimeString()}`;
        document.getElementById('connection-status').style.color = 'green';
    } catch (e) {
        document.getElementById('connection-status').textContent = 'Disconnected';
        document.getElementById('connection-status').style.color = 'red';
    }
}

function updateCard(type, value, extra = []) {
    document.getElementById(`${type}-val`).textContent = `${value.toFixed(1)}%`;
    const bar = document.getElementById(`${type}-bar`);
    bar.style.width = `${value}%`;

    // Color logic
    if (value > 90) bar.style.backgroundColor = '#ef4444';
    else if (value > 75) bar.style.backgroundColor = '#f59e0b';
    else bar.style.backgroundColor = '#3b82f6';

    // Top processes for CPU
    if (type === 'cpu' && extra) {
        const list = document.getElementById('cpu-top-list');
        list.innerHTML = extra.map(p =>
            `<div>${p.name} (pid: ${p.pid}): ${p.cpu_percent}%</div>`
        ).join('');
    }
}

async function updateEvents() {
    const res = await fetch(`${API_BASE}/events`);
    const events = await res.json();
    const tbody = document.querySelector('#events-table tbody');
    tbody.innerHTML = events.map(e => `
        <tr>
            <td>${new Date(e.timestamp).toLocaleString()}</td>
            <td>${e.type}</td>
            <td class="severity-${e.severity}">${e.severity}</td>
            <td>${e.description}</td>
        </tr>
    `).join('');
}

async function updateActions() {
    const res = await fetch(`${API_BASE}/actions`);
    const actions = await res.json();
    const tbody = document.querySelector('#actions-table tbody');
    tbody.innerHTML = actions.map(a => `
        <tr>
            <td>${new Date(a.timestamp).toLocaleString()}</td>
            <td>${a.type}</td>
            <td class="status-${a.status}">${a.status}</td>
            <td><div style="max-width: 200px; overflow:hidden; text-overflow:ellipsis;" title="${a.output}">${a.output}</div></td>
            <td>${a.duration_ms}</td>
            <td>
                ${a.status === 'success' ? `<button onclick="rollback(${a.id})">Rollback</button>` : ''}
            </td>
        </tr>
    `).join('');
}

async function loadSettings() {
    const res = await fetch(`${API_BASE}/settings`);
    const settings = await res.json();

    document.getElementById('cpu-threshold').value = settings.cpu_threshold;
    document.getElementById('memory-threshold').value = settings.memory_threshold;
    document.getElementById('disk-threshold').value = settings.disk_threshold;

    const toggle = document.getElementById('auto-remediate-toggle');
    toggle.checked = (String(settings.auto_remediate).toLowerCase() === 'true');

    // Listen for toggle change
    toggle.onchange = (e) => saveSetting('auto_remediate', e.target.checked);
}

async function saveSetting(key, val = null) {
    if (val === null) {
        // Find input
        const input = document.getElementById(key.replace('_', '-'));
        val = input.value;
    }

    await fetch(`${API_BASE}/settings/${key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: val })
    });
    alert(`Saved ${key}`);
}

async function rollback(id) {
    if (!confirm('Are you sure you want to rollback this action?')) return;
    const res = await fetch(`${API_BASE}/actions/${id}/rollback`, { method: 'POST' });
    const data = await res.json();
    alert(data.status);
    updateActions();
}

// Initial Load
loadSettings();
updateMetrics();
updateEvents();
updateActions();

// Poll intervals
setInterval(updateMetrics, 5000);
setInterval(updateEvents, 10000);
setInterval(updateActions, 30000);
