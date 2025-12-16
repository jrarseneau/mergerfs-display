"""
Web interface for MergerFS Pool Monitor.
"""

from flask import Flask, render_template_string, jsonify
from typing import Dict, List
from .config import Config
from .mergerfs import MergerFSPool
from .disk_info import DiskInfo


# HTML template with embedded CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MergerFS Pool Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .pool-container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .pool-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }

        .pool-name {
            font-size: 1.8em;
            color: #333;
            font-weight: bold;
        }

        .pool-path {
            font-size: 1em;
            color: #666;
            font-family: monospace;
            background: #f5f5f5;
            padding: 5px 10px;
            border-radius: 5px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }

        .summary-card .label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }

        .summary-card .value {
            font-size: 1.5em;
            font-weight: bold;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 20px;
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        th:first-child {
            border-top-left-radius: 10px;
        }

        th:last-child {
            border-top-right-radius: 10px;
        }

        td {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }

        tbody tr {
            transition: background-color 0.2s;
        }

        tbody tr:hover {
            background-color: #f8f9fa;
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        tbody tr:last-child td:first-child {
            border-bottom-left-radius: 10px;
        }

        tbody tr:last-child td:last-child {
            border-bottom-right-radius: 10px;
        }

        .branch-path {
            font-family: monospace;
            color: #333;
            font-weight: 500;
        }

        .disk-device {
            font-family: monospace;
            color: #667eea;
            font-weight: 600;
        }

        .temperature {
            font-weight: 600;
        }

        .temp-ok {
            color: #28a745;
        }

        .temp-warm {
            color: #ffc107;
        }

        .temp-hot {
            color: #dc3545;
        }

        .space-value {
            font-family: monospace;
            font-weight: 600;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }

        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }

        .progress-high {
            background: #28a745;
        }

        .progress-medium {
            background: #ffc107;
        }

        .progress-low {
            background: #dc3545;
        }

        .free-percent {
            font-weight: bold;
            font-size: 1.1em;
        }

        .free-high {
            color: #28a745;
        }

        .free-medium {
            color: #ffc107;
        }

        .free-low {
            color: #dc3545;
        }

        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #f5c6cb;
        }

        .refresh-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 1em;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        .refresh-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }

        .refresh-button:active {
            transform: translateY(0);
        }

        @media (max-width: 768px) {
            header h1 {
                font-size: 1.8em;
            }

            .pool-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .pool-path {
                margin-top: 10px;
            }

            table {
                font-size: 0.9em;
            }

            th, td {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗄️ MergerFS Pool Monitor</h1>
            <p>Real-time monitoring of your MergerFS pools and storage devices</p>
            <button class="refresh-button" onclick="location.reload()">🔄 Refresh</button>
        </header>

        {% for pool in pools %}
        <div class="pool-container">
            <div class="pool-header">
                <div>
                    <div class="pool-name">{{ pool.name }}</div>
                    <div class="pool-path">{{ pool.path }}</div>
                </div>
            </div>

            {% if pool.error %}
            <div class="error-message">
                <strong>Error:</strong> {{ pool.error }}
            </div>
            {% else %}
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="label">Total Branches</div>
                    <div class="value">{{ pool.branch_count }}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Total Space</div>
                    <div class="value">{{ pool.total_space }}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Used Space</div>
                    <div class="value">{{ pool.used_space }}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Free Space</div>
                    <div class="value">{{ pool.free_space }}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Overall Free</div>
                    <div class="value">{{ pool.free_percent }}%</div>
                </div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Branch</th>
                            <th>Physical Disk</th>
                            <th>Temp</th>
                            <th>Size</th>
                            <th>Used Space</th>
                            <th>Free Space</th>
                            <th>Free %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for branch in pool.branches %}
                        <tr>
                            <td><span class="branch-path">{{ branch.branch }}</span></td>
                            <td><span class="disk-device">{{ branch.physical_disk }}</span></td>
                            <td>
                                {% if branch.temperature_str != 'N/A' %}
                                    {% if branch.temperature < 45 %}
                                        <span class="temperature temp-ok">{{ branch.temperature_str }}</span>
                                    {% elif branch.temperature < 55 %}
                                        <span class="temperature temp-warm">{{ branch.temperature_str }}</span>
                                    {% else %}
                                        <span class="temperature temp-hot">{{ branch.temperature_str }}</span>
                                    {% endif %}
                                {% else %}
                                    <span class="temperature">{{ branch.temperature_str }}</span>
                                {% endif %}
                            </td>
                            <td><span class="space-value">{{ branch.size_str }}</span></td>
                            <td><span class="space-value">{{ branch.used_str }}</span></td>
                            <td><span class="space-value">{{ branch.free_str }}</span></td>
                            <td>
                                {% if branch.free_percent > 20 %}
                                    <span class="free-percent free-high">{{ "%.1f"|format(branch.free_percent) }}%</span>
                                {% elif branch.free_percent > 10 %}
                                    <span class="free-percent free-medium">{{ "%.1f"|format(branch.free_percent) }}%</span>
                                {% else %}
                                    <span class="free-percent free-low">{{ "%.1f"|format(branch.free_percent) }}%</span>
                                {% endif %}
                                <div class="progress-bar">
                                    {% if branch.free_percent > 20 %}
                                        <div class="progress-fill progress-high" style="width: {{ branch.free_percent }}%"></div>
                                    {% elif branch.free_percent > 10 %}
                                        <div class="progress-fill progress-medium" style="width: {{ branch.free_percent }}%"></div>
                                    {% else %}
                                        <div class="progress-fill progress-low" style="width: {{ branch.free_percent }}%"></div>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""


def create_app(config: Config) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config: Configuration object

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Render the main page."""
        pools_data = []
        pools_config = config.get_pools()

        for pool_config in pools_config:
            pool_data = {
                'name': pool_config['name'],
                'path': pool_config['path'],
                'error': None,
                'branches': [],
                'branch_count': 0,
                'total_space': 'N/A',
                'used_space': 'N/A',
                'free_space': 'N/A',
                'free_percent': 0
            }

            try:
                # Get MergerFS branches
                pool = MergerFSPool(pool_config['path'])
                branches = pool.get_branches()

                # Collect branch information
                total_space = 0
                total_used = 0
                total_free = 0
                valid_branches = 0

                for branch in branches:
                    info = DiskInfo.get_branch_info(branch)
                    pool_data['branches'].append(info)

                    if info['exists'] and info['total'] > 0:
                        total_space += info['total']
                        total_used += info['used']
                        total_free += info['free']
                        valid_branches += 1

                # Calculate summary
                pool_data['branch_count'] = len(branches)
                if valid_branches > 0:
                    pool_data['total_space'] = DiskInfo.format_bytes(total_space)
                    pool_data['used_space'] = DiskInfo.format_bytes(total_used)
                    pool_data['free_space'] = DiskInfo.format_bytes(total_free)
                    pool_data['free_percent'] = f"{(100 - (total_used / total_space * 100)):.1f}" if total_space > 0 else "0.0"

            except Exception as e:
                pool_data['error'] = str(e)

            pools_data.append(pool_data)

        return render_template_string(HTML_TEMPLATE, pools=pools_data)

    @app.route('/api/pools')
    def api_pools():
        """API endpoint to get pool data as JSON."""
        pools_data = []
        pools_config = config.get_pools()

        for pool_config in pools_config:
            try:
                pool = MergerFSPool(pool_config['path'])
                branches = pool.get_branches()

                branches_info = []
                for branch in branches:
                    branches_info.append(DiskInfo.get_branch_info(branch))

                pools_data.append({
                    'name': pool_config['name'],
                    'path': pool_config['path'],
                    'branches': branches_info
                })
            except Exception as e:
                pools_data.append({
                    'name': pool_config['name'],
                    'path': pool_config['path'],
                    'error': str(e)
                })

        return jsonify(pools_data)

    return app


def run_web_server(config: Config):
    """
    Run the web server.

    Args:
        config: Configuration object
    """
    web_config = config.get_web_config()
    app = create_app(config)

    print(f"\n🚀 Starting MergerFS Pool Monitor Web Server")
    print(f"📡 Server: http://{web_config['host']}:{web_config['port']}")
    print(f"🔗 Access: http://localhost:{web_config['port']}")
    print(f"\nPress Ctrl+C to stop the server\n")

    app.run(
        host=web_config['host'],
        port=web_config['port'],
        debug=False
    )
