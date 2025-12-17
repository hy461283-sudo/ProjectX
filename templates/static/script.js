const API_BASE = '/api';

// --- Navigation Logic ---
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    // Show select tab
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Update Sidebar Active State
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    // We assume the clicked element triggered this, but since we call it from onclick in HTML, 
    // we need to find the nav item that corresponds to the tab.
    // A simple way is to match index or just select by checking text content or attribute.
    // Let's iterate and find the one with onclick containing the tabname.
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('onclick').includes(tabName)) {
            item.classList.add('active');
        }
    });
}


// --- Core Data Logic ---

async function updateMetrics() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();

        // Update DOM
        updateCard('cpu', data.cpu_percent, data.top_processes);
        updateCard('mem', data.memory_percent);
        updateCard('disk', data.disk_percent);

        document.getElementById('connection-status').textContent = `Live: ${new Date().toLocaleTimeString()}`;
        document.getElementById('connection-status').style.color = 'var(--success)';

        // After metrics, load quick insights
        loadRecommendations();

    } catch (e) {
        document.getElementById('connection-status').textContent = 'Disconnected';
        document.getElementById('connection-status').style.color = 'var(--danger)';
    }
}

async function loadRecommendations() {
    try {
        const res = await fetch(`${API_BASE}/recommendations`);
        const data = await res.json();
        const header = document.querySelector('#tab-dashboard .tab-header');

        // Remove old alerts
        const oldAlerts = header.querySelectorAll('.insight-alert');
        oldAlerts.forEach(el => el.remove());

        if (data.length > 0) {
            data.forEach(item => {
                const div = document.createElement('div');
                div.className = `insight-alert ${item.severity}`;
                div.style.cssText = "margin-top:16px; padding:12px; background:rgba(255,255,255,0.05); border-left:4px solid var(--accent); border-radius:4px; font-size:14px; display:flex; gap:10px;";
                div.innerHTML = `<strong>Insight:</strong> ${item.message}`;
                header.appendChild(div);
            });
        }
    } catch (e) { console.error(e); }
}

async function loadWhitelist() {
    try {
        const res = await fetch(`${API_BASE}/settings/whitelist`);
        const list = await res.json();
        const container = document.getElementById('whitelist-tags');
        if (!container) return; // Should exist in HTML

        container.innerHTML = list.map(name => `
            <span class="badge badge-success" style="padding:6px 10px; margin-right:6px; margin-bottom:6px; display:inline-flex; align-items:center; gap:6px;">
                ${name}
                <span onclick="removeWhitelist('${name}')" style="cursor:pointer; opacity:0.6; font-weight:bold;">×</span>
            </span>
        `).join('');
    } catch (e) { console.error(e); }
}

async function addWhitelist() {
    const input = document.getElementById('new-whitelist-name');
    const name = input.value.trim();
    if (!name) return;

    await fetch(`${API_BASE}/settings/whitelist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });
    input.value = '';
    loadWhitelist();
}

async function removeWhitelist(name) {
    if (!confirm(`Remove ${name} from whitelist?`)) return;
    await fetch(`${API_BASE}/settings/whitelist/${name}`, { method: 'DELETE' });
    loadWhitelist();
}

function updateCard(type, value, extra = []) {
    const valEl = document.getElementById(`${type}-val`);
    if (valEl) valEl.textContent = `${value.toFixed(1)}%`;

    const bar = document.getElementById(`${type}-bar`);
    if (bar) {
        bar.style.width = `${value}%`;
        // Color logic
        if (value > 90) bar.style.backgroundColor = 'var(--danger)';
        else if (value > 75) bar.style.backgroundColor = 'var(--warning)';
        else bar.style.backgroundColor = 'var(--accent)'; // specific blue/red from css
    }

    // Top processes for CPU
    if (type === 'cpu' && extra) {
        const list = document.getElementById('cpu-top-list');
        if (list) {
            list.innerHTML = extra.map(p =>
                `<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span>${p.name}</span>
                    <span style="color:white;">${p.cpu_percent}%</span>
                 </div>`
            ).join('');
        }
    }
}

async function updateEvents() {
    try {
        const res = await fetch(`${API_BASE}/events`);
        const events = await res.json();
        const tbody = document.querySelector('#events-table tbody');
        if (!tbody) return;

        tbody.innerHTML = events.map(e => `
            <tr>
                <td>${new Date(e.timestamp).toLocaleString()}</td>
                <td><span style="font-weight:600; color: white;">${e.type}</span></td>
                <td><span class="badge badge-${e.severity.toLowerCase()}">${e.severity}</span></td>
                <td>${e.description}</td>
            </tr>
        `).join('');
    } catch (e) { console.error("Err updating events", e); }
}

async function updateActions() {
    try {
        const res = await fetch(`${API_BASE}/actions`);
        const actions = await res.json();
        const tbody = document.querySelector('#actions-table tbody');
        if (!tbody) return;

        const rows = actions.map(act => {
            return `
            <tr>
                <td>${new Date(act.timestamp).toLocaleTimeString()}</td>
                <td><span class="badge ${getBadgeClass(act.type)}">${formatType(act.type)}</span></td>
                <td style="font-family:monospace; font-size:12px;">${formatOutput(act)}</td>
                <td>
                    <span class="badge ${act.status === 'success' ? 'badge-success' : 'badge-critical'}">${act.status}</span>
                </td>
                 <td>
                    ${canRollback(act) ? `<button onclick="rollbackAction(${act.id})" class="btn-save" style="background:#333; color:white; font-size:11px; padding:4px 8px;">Undo</button>` : ''}
                </td>
            </tr>
            `;
        }).join('');
        tbody.innerHTML = rows;
    } catch (e) { console.error("Err updating actions", e); }
}

function canRollback(act) {
    // Only support rollback for Throttling right now
    return act.type === 'action_throttle_high_cpu_process' && act.status === 'success';
}

async function rollbackAction(id) {
    if (!confirm("Undo this action? (Restore process priority)")) return;
    try {
        const res = await fetch(`${API_BASE}/actions/${id}/rollback`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            alert("Action Undone Successfully");
            updateActions();
        } else {
            alert("Undo Failed: " + (data.message || 'Unknown error'));
        }
    } catch (e) { console.error(e); }
}

function formatType(type) {
    return type.replace('action_', '').replace(/_/g, ' ').toUpperCase();
}

function formatOutput(act) {
    if (act.target_process) return `Target: ${act.target_process}`;
    if (act.target_service) return `Service: ${act.target_service}`;
    if (act.files_deleted) return `Files: ${act.files_deleted}`;
    return act.output.substring(0, 50) + '...';
}

function getBadgeClass(type) {
    if (type.includes('kill') || type.includes('service')) return 'badge-critical';
    if (type.includes('throttle')) return 'badge-warning';
    return 'badge-success';
}

async function loadSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        const settings = await res.json();

        const cpuEl = document.getElementById('cpu-threshold');
        if (cpuEl) cpuEl.value = settings.cpu_threshold;

        const memEl = document.getElementById('memory-threshold');
        if (memEl) memEl.value = settings.memory_threshold;

        const diskEl = document.getElementById('disk-threshold');
        if (diskEl) diskEl.value = settings.disk_threshold;

        const toggle = document.getElementById('auto-remediate-toggle');
        if (toggle) {
            toggle.checked = (String(settings.auto_remediate).toLowerCase() === 'true');
            // Listen for toggle change
            toggle.onchange = (e) => saveSetting('auto_remediate', e.target.checked);
        }
    } catch (e) { console.error("Settings load error", e); }
}

async function saveSetting(key, val) {
    await fetch(`${API_BASE}/settings/${key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: val })
    });
    // Optional: show a toast or notification instead of alert
    // alert(`Saved ${key}`); 
}

// Chart Global
let historyChart = null;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadWhitelist();
    loadProcessList(); // New
    initChart();       // New
    updateMetrics();
    updateEvents();
    updateActions();

    // Poll intervals
    setInterval(updateMetrics, 2000);
    setInterval(updateEvents, 10000);
    setInterval(updateActions, 30000);
    setInterval(updateChartData, 2000); // Poll chart history
});

// --- NEW FEATURES LOGIC ---

async function loadProcessList() {
    try {
        const res = await fetch(`${API_BASE}/processes`);
        if (!res.ok) return;
        const list = await res.json();
        const dataList = document.getElementById('running-processes');
        if (dataList) {
            dataList.innerHTML = list.map(p => `<option value="${p}">`).join('');
        }
    } catch (e) { console.error("Proc list error", e); }
}

async function initChart() {
    const ctx = document.getElementById('historyChart');
    if (!ctx) return;

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU %',
                    borderColor: '#2563eb', // Electric Blue
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    data: [],
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Memory %',
                    borderColor: '#10b981', // Success Green
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    data: [],
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { labels: { color: '#a1a1a1' } }
            },
            scales: {
                x: { ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { min: 0, max: 100, ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
    updateChartData();
}

async function updateChartData() {
    if (!historyChart) return;
    try {
        const res = await fetch(`${API_BASE}/history`);
        const data = await res.json();

        // Data format: [{timestamp, cpu_percent, memory_percent}, ...]
        const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        const cpuData = data.map(d => d.cpu_percent);
        const memData = data.map(d => d.memory_percent);

        historyChart.data.labels = labels;
        historyChart.data.datasets[0].data = cpuData;
        historyChart.data.datasets[1].data = memData;
        historyChart.update('none'); // Animate quietly
    } catch (e) { console.error("Chart error", e); }
}
