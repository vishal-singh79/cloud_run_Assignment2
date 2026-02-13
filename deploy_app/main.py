import os
import time
import random
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)


START_TIME = time.time()
CPU_HISTORY = []
MEMORY_HISTORY = []



def get_cgroup_cpu_usage():
    """Reads the cumulative CPU usage in microseconds from cgroup v2."""
    try:
       
        if os.path.exists("/sys/fs/cgroup/cpu.stat"):
            with open("/sys/fs/cgroup/cpu.stat", "r") as f:
                for line in f:
                    if line.startswith("usage_usec"):
                        return int(line.split()[1])
        
        elif os.path.exists("/sys/fs/cgroup/cpuacct/cpuacct.usage"):
            with open("/sys/fs/cgroup/cpuacct/cpuacct.usage", "r") as f:
                return int(f.read().strip()) // 1000
    except:
        return None
    return None

def get_cgroup_memory():
    try:
        with open("/sys/fs/cgroup/memory/memory.usage_in_bytes", "r") as f:
            usage = int(f.read().strip())

        with open("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r") as f:
            limit = int(f.read().strip())

        return usage, limit
    except:
        return 0, 0


def get_cpu_metric():
    """Calculates real CPU % by measuring usage delta over 100ms."""
 
    t1_usage = get_cgroup_cpu_usage()
    t1_time = time.time()
    

    time.sleep(0.1)
    
 
    t2_usage = get_cgroup_cpu_usage()
    t2_time = time.time()

    if t1_usage is not None and t2_usage is not None:
      
        usage_delta = t2_usage - t1_usage
        time_delta = (t2_time - t1_time) * 1_000_000
        cpu_percent = (usage_delta / time_delta) * 100
    else:
        # If we are not in a Linux/Cgroup environment, fallback to 0
        cpu_percent = 0.0
    
  
    cpu_percent = cpu_percent / (os.cpu_count() or 1)

    CPU_HISTORY.append(cpu_percent)
    return {
        "current": round(cpu_percent, 2),
        "highest": round(max(CPU_HISTORY), 2),
        "lowest": round(min(CPU_HISTORY), 2),
        "average": round(sum(CPU_HISTORY) / len(CPU_HISTORY), 2)
    }

def get_memory_metric():
    cg_usage, cg_limit = get_cgroup_memory()
    try:
        with open("/proc/meminfo", "r") as f:
            m = {l.split(':')[0]: int(l.split(':')[1].split()[0]) for l in f}
    except:
        m = {"MemTotal": 1024, "MemAvailable": 512}
    
    if cg_limit > 0:
        current_percent = (cg_usage / cg_limit) * 100
        total_mb, used_mb = cg_limit / 1048576, cg_usage / 1048576
        source = "cgroup_v2"
    else:
        total_mb = m['MemTotal'] / 1024
        used_mb = (m['MemTotal'] - m.get('MemAvailable', m['MemFree'])) / 1024
        current_percent = (used_mb / total_mb) * 100
        source = "proc_meminfo"

    MEMORY_HISTORY.append(current_percent)
    return {
        "total_mb": round(total_mb, 2),
        "used_mb": round(used_mb, 2),
        "available_mb": round((total_mb - used_mb), 2),
        "current": round(current_percent, 2),
        "highest": round(max(MEMORY_HISTORY), 2),
        "source_engine": source
    }

def calculate_health_score(cpu, mem, uptime):
    score = 100.0
    if cpu < 30: score -= cpu * 0.5 
    elif cpu < 70: score -= (15 + (cpu - 30) * 1.0)
    else: score -= (55 + (cpu - 70) * 1.5)
    
    if mem < 50: score -= mem * 0.4 
    elif mem < 80: score -= (20 + (mem - 50) * 1.0)
    else: score -= (50 + (mem - 80) * 1.5)
    
    if uptime > 300: score += 5
    if cpu > 90 or mem > 90: score -= 15
    return round(max(0, min(100, score)))


BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg-color: #050505;
            --blue: #007acc;
            --green: #85c46c;
            --grid: rgba(40, 40, 40, 0.4);
        }
        body { 
            background: var(--bg-color); color: #fff; font-family: 'Courier New', monospace; 
            margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh;
            background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
            background-size: 25px 25px;
        }
        .box { 
            border: 1px solid #333; padding: 40px 20px; width: 90%; max-width: 500px; 
            background: #000; position: relative; text-align: center; box-sizing: border-box;
        }
        .dot { width: 6px; height: 6px; background: var(--blue); position: absolute; border-radius: 50%; }
        .tl{top:-3px;left:-3px} .tr{top:-3px;right:-3px} .bl{bottom:-3px;left:-3px} .br{bottom:-3px;right:-3px}
        
        h2 { font-size: 1.6rem; margin: 0 0 10px 0; letter-spacing: 1px; }
        .subtitle { color: #666; font-size: 0.8rem; margin-bottom: 30px; }

        .btn { 
            display: block; width: 100%; padding: 15px; margin: 10px 0;
            border: 1px solid var(--blue); color: var(--blue); background: none;
            text-decoration: none; font-family: inherit; font-size: 0.9rem; font-weight: bold;
            cursor: pointer; transition: 0.2s; text-transform: uppercase; box-sizing: border-box;
        }
        .btn-green { border-color: var(--green); color: var(--green); }
        .btn:hover { background: rgba(0, 122, 204, 0.1); }
        .btn-green:hover { background: rgba(133, 196, 108, 0.1); }

        .log-container { 
            height: 250px; overflow-y: auto; background: #080808; border: 1px solid #222; 
            padding: 10px; margin-top: 15px; text-align: left;
        }
        .log-entry { font-size: 11px; border-bottom: 1px solid #1a1a1a; padding: 8px 0; color: var(--green); }
        .log-time { color: var(--blue); font-weight: bold; margin-right: 10px; }
    </style>
    <script>
        async function runAnalysis() {
            const res = await fetch('/api/analyze');
            const data = await res.json();
            
            let history = JSON.parse(localStorage.getItem('sys_history') || '[]');
            history.unshift({
                time: data.machine_time, 
                cpu: data.cpu_metric.current,
                mem: data.memory_metric.current,
                score: data.health_score
            });
            localStorage.setItem('sys_history', JSON.stringify(history.slice(0, 100)));
            window.location.href = '/api/analyze';
        }
        function loadHistory() {
            const container = document.getElementById('log-box');
            let history = JSON.parse(localStorage.getItem('sys_history') || '[]');
            container.innerHTML = history.map(e => `
                <div class="log-entry"><span class="log-time">[${e.time}]</span> CPU: ${e.cpu}% | MEM: ${e.mem}% | Score: ${e.score}</div>
            `).join('') || '<div style="text-align:center;margin-top:100px;color:#444">NO HISTORY DATA</div>';
        }
    </script>
</head>
<body onload="{{ 'loadHistory()' if page == 'logs' else '' }}">
    <div class="box">
        <div class="dot tl"></div><div class="dot tr"></div>
        <div class="dot bl"></div><div class="dot br"></div>
        {{ content | safe }}
    </div>
</body>
</html>
"""

@app.route('/')
def root():
    content = """
        <h2>Container Health Monitor</h2>
        <div class="subtitle">Real-time Cgroup CPU Delta Analysis</div>
        <button onclick="runAnalysis()" class="btn">GENERATE JSON REPORT</button>
        <a href="/logs" class="btn btn-green">VIEW HISTORICAL LOGS</a>
    """
    return render_template_string(BASE_HTML, content=content, page='home')

@app.route('/api/analyze')
def analyze_api():
    cpu, mem = get_cpu_metric(), get_memory_metric()
    uptime = time.time() - START_TIME
    score = calculate_health_score(cpu['current'], mem['current'], uptime)
    
    return jsonify({
        "machine_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "health_score": score,
        "cpu_metric": cpu,
        "memory_metric": mem,
        "container_info": {
            "uptime_seconds": round(uptime, 2),
            "engine": mem['source_engine'],
            "cpu_cores": os.cpu_count()
        }
    })

@app.route('/logs')
def logs():
    content = """
        <h3 style="margin:0; text-transform:uppercase; color:#ccc;">Persistent History</h3>
        <div id="log-box" class="log-container"></div>
        <div style="display:flex; gap:10px;">
            <a href="/" class="btn" style="flex:1">BACK</a>
            <button onclick="localStorage.removeItem('sys_history');location.reload();" class="btn btn-green" style="flex:1; border-color:#f55; color:#f55;">CLEAR</button>
        </div>
    """
    return render_template_string(BASE_HTML, content=content, page='logs')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

