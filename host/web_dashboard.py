"""
EvoClaw Web Dashboard - 簡易監控面板
提供 logs、sessions、container 狀態的即時監控介面
"""
import asyncio
import json
import logging
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from aiohttp import web

from . import config, db

log = logging.getLogger(__name__)

# 全域狀態
_app: Optional[web.Application] = None
_db_conn: Optional[sqlite3.Connection] = None

def get_db() -> sqlite3.Connection:
    """取得資料庫連線"""
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(str(config.STORE_DIR / "messages.db"))
        _db_conn.row_factory = sqlite3.Row
    return _db_conn

# ── HTML 模板 ─────────────────────────────────────────────────────────────

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EvoClaw Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        header h1 { font-size: 2em; margin-bottom: 10px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 { color: #667eea; font-size: 2.5em; margin-bottom: 5px; }
        .stat-card p { color: #666; font-size: 0.9em; }
        .section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f8f9fa;
            color: #667eea;
            font-weight: 600;
        }
        tr:hover { background: #f8f9fa; }
        .status-active { color: #10b981; font-weight: bold; }
        .status-pending { color: #f59e0b; font-weight: bold; }
        .status-error { color: #ef4444; font-weight: bold; }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 15px;
        }
        .refresh-btn:hover { background: #5568d3; }
        .log-entry {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            padding: 8px;
            border-left: 3px solid #667eea;
            margin: 5px 0;
            background: #f8f9fa;
        }
        .log-time { color: #666; }
        .log-info { color: #10b981; }
        .log-warning { color: #f59e0b; }
        .log-error { color: #ef4444; }
        .container-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .container-running { background: #d1fae5; color: #10b981; }
        .container-stopped { background: #fee2e2; color: #ef4444; }
        .auto-refresh {
            text-align: right;
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .loading { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 EvoClaw Dashboard</h1>
            <p>AI Assistant Monitoring Panel</p>
        </header>

        <div class="auto-refresh">
            Auto-refresh: <span id="countdown">5</span>s
            <button class="refresh-btn" onclick="refreshData()" style="margin-left: 10px;">Refresh Now</button>
        </div>

        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <h3 id="totalGroups">-</h3>
                <p>Registered Groups</p>
            </div>
            <div class="stat-card">
                <h3 id="totalTasks">-</h3>
                <p>Scheduled Tasks</p>
            </div>
            <div class="stat-card">
                <h3 id="totalMessages">-</h3>
                <p>Messages (24h)</p>
            </div>
            <div class="stat-card">
                <h3 id="successRate">-</h3>
                <p>Success Rate</p>
            </div>
        </div>

        <div class="section">
            <h2>📋 Scheduled Tasks</h2>
            <table>
                <thead>
                    <tr>
                        <th>Task ID</th>
                        <th>Group</th>
                        <th>Type</th>
                        <th>Schedule</th>
                        <th>Next Run</th>
                        <th>Status</th>
                        <th>Last Result</th>
                    </tr>
                </thead>
                <tbody id="tasksTable">
                    <tr><td colspan="7" class="loading">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📊 Recent Activity Logs</h2>
            <div id="logsContainer">
                <div class="loading">Loading logs...</div>
            </div>
        </div>

        <div class="section">
            <h2>🐳 Container Status</h2>
            <table>
                <thead>
                    <tr>
                        <th>Container Name</th>
                        <th>Group</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="containersTable">
                    <tr><td colspan="5" class="loading">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📈 Evolution Stats (Last 7 Days)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Group JID</th>
                        <th>Total Runs</th>
                        <th>Success Rate</th>
                        <th>Avg Response (ms)</th>
                        <th>Style</th>
                        <th>Formality</th>
                    </tr>
                </thead>
                <tbody id="evolutionTable">
                    <tr><td colspan="6" class="loading">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function refreshData() {
            try {
                // Stats
                const statsRes = await fetch('/api/stats');
                const stats = await statsRes.json();
                document.getElementById('totalGroups').textContent = stats.total_groups || 0;
                document.getElementById('totalTasks').textContent = stats.total_tasks || 0;
                document.getElementById('totalMessages').textContent = stats.messages_24h || 0;
                document.getElementById('successRate').textContent = (stats.success_rate || 0) + '%';

                // Tasks
                const tasksRes = await fetch('/api/tasks');
                const tasks = await tasksRes.json();
                const tasksTbody = document.getElementById('tasksTable');
                if (tasks.length === 0) {
                    tasksTbody.innerHTML = '<tr><td colspan="7">No scheduled tasks</td></tr>';
                } else {
                    tasksTbody.innerHTML = tasks.map(task => `
                        <tr>
                            <td>${task.id.substring(0, 8)}...</td>
                            <td>${task.group_folder}</td>
                            <td>${task.schedule_type}</td>
                            <td>${task.schedule_value}</td>
                            <td>${task.next_run ? new Date(task.next_run).toLocaleString() : '- '}</td>
                            <td class="status-${task.status}">${task.status}</td>
                            <td>${task.last_result ? (task.last_result.length > 50 ? task.last_result.substring(0, 50) + '...' : task.last_result) : '-'}</td>
                        </tr>
                    `).join('');
                }

                // Containers
                const containersRes = await fetch('/api/containers');
                const containers = await containersRes.json();
                const containersTbody = document.getElementById('containersTable');
                if (containers.length === 0) {
                    containersTbody.innerHTML = '<tr><td colspan="5">No containers running</td></tr>';
                } else {
                    containersTbody.innerHTML = containers.map(c => `
                        <tr>
                            <td>${c.name}</td>
                            <td>${c.group || '-'}</td>
                            <td><span class="container-status container-${c.status}">${c.status}</span></td>
                            <td>${c.created || '-'}</td>
                            <td><button onclick="stopContainer('${c.name}')">Stop</button></td>
                        </tr>
                    `).join('');
                }

                // Logs
                const logsRes = await fetch('/api/logs');
                const logs = await logsRes.json();
                const logsContainer = document.getElementById('logsContainer');
                if (logs.length === 0) {
                    logsContainer.innerHTML = '<div class="log-entry">No recent logs</div>';
                } else {
                    logsContainer.innerHTML = logs.map(l => `
                        <div class="log-entry">
                            <span class="log-time">[${l.timestamp}]</span>
                            <span class="log-${l.level}">[${l.level.toUpperCase()}]</span>
                            ${l.message}
                        </div>
                    `).join('');
                }

                // Evolution
                const evolutionRes = await fetch('/api/evolution');
                const evolution = await evolutionRes.json();
                const evolutionTbody = document.getElementById('evolutionTable');
                if (evolution.length === 0) {
                    evolutionTbody.innerHTML = '<tr><td colspan="6">No evolution data</td></tr>';
                } else {
                    evolutionTbody.innerHTML = evolution.map(e => `
                        <tr>
                            <td>${e.jid}</td>
                            <td>${e.total_runs}</td>
                            <td>${e.success_rate}%</td>
                            <td>${e.avg_response_ms}ms</td>
                            <td>${e.response_style || 'balanced'}</td>
                            <td>${e.formality ? (e.formality * 100).toFixed(0) + '%' : '-'}</td>
                        </tr>
                    `).join('');
                }
            } catch (err) {
                console.error('Error refreshing data:', err);
            }
        }

        async function stopContainer(name) {
            if (confirm('Stop container ' + name + '?')) {
                await fetch('/api/containers/' + name, { method: 'POST' });
                refreshData();
            }
        }

        // Auto-refresh countdown
        let countdown = 5;
        setInterval(() => {
            countdown = countdown <= 1 ? 5 : countdown - 1;
            document.getElementById('countdown').textContent = countdown;
            if (countdown === 5) refreshData();
        }, 1000);

        // Initial load
        refreshData();
    </script>
</body>
</html>
"""

# ── API Handlers ─────────────────────────────────────────────────────────────

async def handle_dashboard(request: web.Request) -> web.Response:
    """主頁面"""
    return web.Response(text=DASHBOARD_HTML, content_type='text/html')

async def handle_stats(request: web.Request) -> web.Response:
    """統計數據"""
    try:
        db_conn = get_db()
        
        # Total groups
        row = db_conn.execute("SELECT COUNT(*) as count FROM registered_groups").fetchone()
        total_groups = row["count"] if row else 0
        
        # Total tasks
        row = db_conn.execute("SELECT COUNT(*) as count FROM scheduled_tasks WHERE status='active'").fetchone()
        total_tasks = row["count"] if row else 0
        
        # Messages in last 24h
        row = db_conn.execute("""
            SELECT COUNT(*) as count FROM messages 
            WHERE timestamp > (strftime('%s', 'now') - 86400) * 1000
        """).fetchone()
        messages_24h = row["count"] if row else 0
        
        # Success rate (last 7 days)
        row = db_conn.execute("""
            SELECT 
                CAST(SUM(success) AS FLOAT) / COUNT(*) * 100 as rate
            FROM evolution_runs
            WHERE timestamp > datetime('now', '-7 days')
        """).fetchone()
        success_rate = round(row["rate"], 1) if row and row["rate"] else 0
        
        return web.json_response({
            "total_groups": total_groups,
            "total_tasks": total_tasks,
            "messages_24h": messages_24h,
            "success_rate": success_rate
        })
    except Exception as e:
        log.error(f"Error getting stats: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_tasks(request: web.Request) -> web.Response:
    """所有排程任務"""
    try:
        db_conn = get_db()
        rows = db_conn.execute("SELECT * FROM scheduled_tasks ORDER BY created_at DESC").fetchall()
        tasks = [dict(row) for row in rows]
        return web.json_response(tasks)
    except Exception as e:
        log.error(f"Error getting tasks: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_logs(request: web.Request) -> web.Response:
    """最近的活動日誌"""
    try:
        db_conn = get_db()
        
        # 合併 evolution runs 和 task runs
        logs = []
        
        # Evolution runs
        evo_rows = db_conn.execute("""
            SELECT 
                'evolution' as type,
                jid as target,
                success,
                response_ms as duration,
                timestamp,
                run_id as id
            FROM evolution_runs
            ORDER BY timestamp DESC
            LIMIT 25
        """).fetchall()
        
        for row in evo_rows:
            level = "info" if row["success"] else "error"
            logs