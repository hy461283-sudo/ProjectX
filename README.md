# ProjectX - Enterprise Edition
**Self-Healing IT Infrastructure Automation**

![Dashboard Preview](https://via.placeholder.com/800x400?text=ProjectX+Live+Dashboard)

## 🚀 Executive Summary
ProjectX is an AI-driven, self-healing system monitor designed for large-scale enterprise environments. It autonomously detects, analyzes, and resolves system performance issues (CPU, Memory, Disk) without user intervention, ensuring 99.9% uptime and optimal employee productivity.

**Key Features:**
- **Zero-Touch Remediation:** Automatically throttles high-priority processes instead of killing them.
- **AI Recommendations:** Analyzes long-term trends to predict resource exhaustion.
- **Enterprise Security:** Whitelist-based protection for core business applications.
- **Live Observability:** Real-time dashboards with historical trend analysis.

---

## 📦 Zero-Install Demo (How to Run)

We have packaged ProjectX as a **standalone executable**. No Python installation, dependencies, or configuration is required.

### **For Windows (Target Environment)**
1.  **Download** the `ProjectX-Demo.zip` package.
2.  **Extract** to any folder (e.g., Desktop).
3.  **Double-click** `ProjectX.exe`.
4.  The system will start silently. Open your browser to:
    👉 **http://localhost:5000/dashboard**

### **For MacOS / Linux (Dev Demo)**
1.  Open Terminal in the folder.
2.  Run: `./ProjectX`
3.  Open browser to: **http://127.0.0.1:5000/dashboard**

---

## 🛠️ Building From Source (For Developers)

If you wish to modify the source code or rebuild the binary:

### Prerequisites
- Python 3.10+
- `pip`

### Step 1: Setup Environment
```bash
git clone https://github.com/your-org/ProjectX.git
cd ProjectX
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Build Executable
We provide a unified build script that detects your OS and packages the app.
```bash
python build_demo.py
```
*   **Artifacts**: The standalone binary will be in the `dist/` folder.
*   **Windows Note**: Run this script on a Windows machine to generate the `.exe` file.

---

## 🛡️ Security & Configuration

### Application Whitelist
To prevent critical business apps from being throttled:
1.  Go to **Settings** > **Protected Applications**.
2.  Search for the process (e.g., `Teams`, `Outlook`).
3.  Click **Add**.
*   *Result:* These apps will be deprioritized (`BelowNormal`) rather than terminated during CPU spikes.

### Architecture
- **Core**: Python 3.12 (Flask + psutil)
- **Database**: SQLite (Embedded, Zero-Config)
- **Frontend**: Vanilla JS + Chart.js (No Node.js required)
- **Deployment**: PyInstaller (Single Binary)

---

## 📞 Enterprise Support
For POCs, licensing, and white-labeling inquiries:
- **Contact**: enterprise@projectx.ai
- **Docs**: [Internal Wiki Link]

---
*© 2025 ProjectX Enterprise Solutions. All rights reserved.*
