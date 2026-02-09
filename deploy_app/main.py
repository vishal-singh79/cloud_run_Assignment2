import os
import time
import psutil
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)


START_TIME = time.time()


HOME_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask System Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 50px 40px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
            width: 100%;
            border: 1px solid #e0e0e0;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 2em;
            font-weight: 600;
        }
        
        p {
            color: #666;
            margin-bottom: 35px;
            font-size: 1em;
            line-height: 1.6;
        }
        
        .button {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 14px 40px;
            text-decoration: none;
            border-radius: 6px;
            font-size: 1em;
            font-weight: 500;
            transition: background 0.2s ease;
            cursor: pointer;
        }
        
        .button:hover {
            background: #2980b9;
        }
        
        .button:active {
            background: #2574a9;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #27ae60;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        .info {
            margin-top: 30px;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
            border: 1px solid #e8e8e8;
        }
        
        .info h3 {
            color: #2c3e50;
            margin-bottom: 12px;
            font-size: 1.1em;
            font-weight: 600;
        }
        
        .info ul {
            text-align: left;
            color: #555;
            line-height: 1.8;
            font-size: 0.95em;
        }
        
        .info li {
            margin-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        
        <p>
            <span class="status-indicator"></span>
            Hello from Cloud Run! System check complete.
        </p>
        <a href="/analyze" class="button">View System Analysis</a>
        
    </div>
</body>
</html>
"""


@app.route('/')
def hello():
    """Render the home page with a button to navigate to /analyze"""
    return render_template_string(HOME_PAGE_HTML)


@app.route('/analyze')
def analyze():
    """
    Returns dynamic system information from the running container.
    
    Returns:
        JSON response containing:
        - timestamp: Current UTC time
        - uptime_seconds: Container uptime
        - cpu_metric: CPU usage percentage
        - memory_metric: Memory usage percentage
        - health_score: Computed health score (0-100)
        - message: Human-readable status message
    """

    current_timestamp = datetime.now(timezone.utc).isoformat()
 
    uptime_seconds = round(time.time() - START_TIME, 2)

    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_metric = round(cpu_percent, 2)

    memory = psutil.virtual_memory()
    memory_metric = round(memory.percent, 2)

    health_score = calculate_health_score(cpu_metric, memory_metric, uptime_seconds)
 
    message = generate_status_message(health_score)
    
    response = {
        "timestamp": current_timestamp,
        "uptime_seconds": uptime_seconds,
        "cpu_metric": cpu_metric,
        "memory_metric": memory_metric,
        "health_score": health_score,
        "message": message
    }
    
    return jsonify(response)


def calculate_health_score(cpu_percent, memory_percent, uptime_seconds):
    """
    Custom algorithm to calculate system health score (0-100).
    
    Algorithm logic:
    - Start with base score of 100
    - Deduct points based on CPU usage (higher usage = more deduction)
    - Deduct points based on memory usage (higher usage = more deduction)
    - Add bonus points for stable uptime
    - Apply penalties for critical thresholds
    
    Args:
        cpu_percent: CPU usage percentage
        memory_percent: Memory usage percentage
        uptime_seconds: System uptime in seconds
        
    Returns:
        int: Health score between 0 and 100
    """
    score = 100.0
    

    if cpu_percent < 30:
        cpu_penalty = cpu_percent * 0.5 
    elif cpu_percent < 70:
        cpu_penalty = 15 + (cpu_percent - 30) * 1.0 
    else:
        cpu_penalty = 55 + (cpu_percent - 70) * 1.5  
    
    score -= cpu_penalty
    
   
    if memory_percent < 50:
        memory_penalty = memory_percent * 0.4 
    elif memory_percent < 80:
        memory_penalty = 20 + (memory_percent - 50) * 1.0 
    else:
        memory_penalty = 50 + (memory_percent - 80) * 1.5  
    
    score -= memory_penalty

    if uptime_seconds > 3600: 
        uptime_bonus = min(10, uptime_seconds / 3600)  
    elif uptime_seconds > 300: 
        uptime_bonus = 5
    else:
        uptime_bonus = 0  
    
    score += uptime_bonus
    
   
    if cpu_percent > 90:
        score -= 15 
    if memory_percent > 90:
        score -= 15 
    
   
    score = max(0, min(100, score))
    
    return round(score)


def generate_status_message(health_score):
    """
    Generate a human-readable status message based on health score.
    
    Args:
        health_score: Health score between 0 and 100
        
    Returns:
        str: Status message
    """
    if health_score >= 90:
        return "Excellent - System running optimally"
    elif health_score >= 75:
        return "Good - System performing well"
    elif health_score >= 60:
        return "Fair - System under moderate load"
    elif health_score >= 40:
        return "Warning - System experiencing elevated resource usage"
    elif health_score >= 20:
        return "Critical - System resources heavily strained"
    else:
        return "Emergency - System resources critically exhausted"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)