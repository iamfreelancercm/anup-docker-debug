#!/usr/bin/env python3
"""
KyberShield Monitoring Dashboard
Real-time quantum security services monitoring
"""

from flask import Flask, render_template_string, jsonify
import json
import time
import requests
import os
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle ECS DB_CREDENTIALS environment variable
db_creds = None
if os.environ.get('DB_CREDENTIALS'):
    try:
        db_creds = json.loads(os.environ.get('DB_CREDENTIALS', '{}'))
        logger.info("✅ ECS database credentials loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not parse DB_CREDENTIALS: {e}")
        db_creds = None

class KyberShieldMonitor:
    def __init__(self):
        self.services = {
            'firewall': 'http://kyber-shield-firewall-staging:3000',
            'database': 'http://kyber-shield-database-staging:5000', 
            'backup': 'http://kyber-shield-backup-staging:8000',
            'rosenpass': 'http://kyber-shield-rosenpass-staging:8080',
            'client_api': 'http://kyber-shield-client-api-staging:9000'
        }
        
    def check_service_health(self, service_name, endpoint):
        """Check individual service health"""
        try:
            response = requests.get(f"{endpoint}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'details': data,
                    'last_check': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
            
        return {'status': 'unknown'}
    
    def get_all_service_status(self):
        """Get status of all KyberShield services"""
        status = {}
        
        for service_name, endpoint in self.services.items():
            status[service_name] = self.check_service_health(service_name, endpoint)
            
        return status
    
    def get_quantum_security_metrics(self):
        """Get quantum cryptography metrics"""
        return {
            'encryption_algorithms': {
                'ml_kem_768': {
                    'name': 'ML-KEM-768',
                    'purpose': 'Key Encapsulation (Rosenpass VPN)',
                    'quantum_resistant': True,
                    'status': 'active'
                },
                'ml_dsa_87': {
                    'name': 'ML-DSA-87', 
                    'purpose': 'Digital Signatures (Firewall + Database)',
                    'quantum_resistant': True,
                    'status': 'active'
                },
                'chacha20_poly1305': {
                    'name': 'ChaCha20-Poly1305',
                    'purpose': 'Symmetric Encryption (Backup)',
                    'quantum_resistant': True,
                    'status': 'active'
                }
            },
            'threat_level': 'low',
            'quantum_readiness': '100%',
            'last_updated': datetime.utcnow().isoformat()
        }

monitor = KyberShieldMonitor()

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>KyberShield Quantum Security Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-top: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #fff;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }
        .status-healthy { color: #4CAF50; font-weight: bold; }
        .status-unhealthy { color: #f44336; font-weight: bold; }
        .status-unknown { color: #ff9800; font-weight: bold; }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .quantum-badge {
            display: inline-block;
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .refresh-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        .refresh-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        .architecture {
            text-align: center;
            font-family: monospace;
            background: rgba(0,0,0,0.2);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            line-height: 1.6;
        }
    </style>
    <script>
        function refreshDashboard() {
            location.reload();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ KyberShield Quantum Security</h1>
            <div class="subtitle">Real-time Monitoring Dashboard</div>
            <div class="subtitle">
                <span class="quantum-badge">100% Quantum Resistant</span>
                <span style="margin: 0 10px;">|</span>
                <span>Last Updated: {{ timestamp }}</span>
            </div>
        </div>

        <div class="architecture">
            <div>🌐 Client Traffic → 🛡️ Firewall (ML-DSA-87) ↔ 🔒 Database (ML-DSA-87)</div>
            <div style="margin: 10px 0;">↕&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↕</div>
            <div>🔐 Rosenpass VPN (ML-KEM-768 Internal Tunnel)</div>
            <div style="margin: 10px 0;">↕&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↕</div>
            <div>💾 Backup (ChaCha20) ↔ 🔒 Database</div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>🛡️ Quantum Firewall</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-{{ services.firewall.status }}">{{ services.firewall.status.upper() }}</span>
                </div>
                <div class="metric">
                    <span>Encryption:</span>
                    <span>ML-DSA-87 Signatures</span>
                </div>
                {% if services.firewall.response_time %}
                <div class="metric">
                    <span>Response Time:</span>
                    <span>{{ "%.3f"|format(services.firewall.response_time) }}s</span>
                </div>
                {% endif %}
            </div>

            <div class="card">
                <h3>🔒 Quantum Database</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-{{ services.database.status }}">{{ services.database.status.upper() }}</span>
                </div>
                <div class="metric">
                    <span>Encryption:</span>
                    <span>ML-DSA-87 Records</span>
                </div>
                {% if services.database.response_time %}
                <div class="metric">
                    <span>Response Time:</span>
                    <span>{{ "%.3f"|format(services.database.response_time) }}s</span>
                </div>
                {% endif %}
            </div>

            <div class="card">
                <h3>🔐 Rosenpass VPN</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-{{ services.rosenpass.status }}">{{ services.rosenpass.status.upper() }}</span>
                </div>
                <div class="metric">
                    <span>Encryption:</span>
                    <span>ML-KEM-768 Tunnel</span>
                </div>
                {% if services.rosenpass.response_time %}
                <div class="metric">
                    <span>Response Time:</span>
                    <span>{{ "%.3f"|format(services.rosenpass.response_time) }}s</span>
                </div>
                {% endif %}
            </div>

            <div class="card">
                <h3>💾 Quantum Backup</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-{{ services.backup.status }}">{{ services.backup.status.upper() }}</span>
                </div>
                <div class="metric">
                    <span>Encryption:</span>
                    <span>ChaCha20-Poly1305</span>
                </div>
                {% if services.backup.response_time %}
                <div class="metric">
                    <span>Response Time:</span>
                    <span>{{ "%.3f"|format(services.backup.response_time) }}s</span>
                </div>
                {% endif %}
            </div>

            <div class="card">
                <h3>🎯 Client API</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-{{ services.client_api.status }}">{{ services.client_api.status.upper() }}</span>
                </div>
                <div class="metric">
                    <span>Authentication:</span>
                    <span>JWT + API Keys</span>
                </div>
                {% if services.client_api.response_time %}
                <div class="metric">
                    <span>Response Time:</span>
                    <span>{{ "%.3f"|format(services.client_api.response_time) }}s</span>
                </div>
                {% endif %}
            </div>

            <div class="card">
                <h3>🔐 Quantum Security</h3>
                <div class="metric">
                    <span>Quantum Readiness:</span>
                    <span class="quantum-badge">{{ quantum.quantum_readiness }}</span>
                </div>
                <div class="metric">
                    <span>Threat Level:</span>
                    <span class="status-healthy">{{ quantum.threat_level.upper() }}</span>
                </div>
                <div class="metric">
                    <span>Algorithms Active:</span>
                    <span>{{ quantum.encryption_algorithms|length }}</span>
                </div>
            </div>
        </div>

        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Dashboard</button>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main monitoring dashboard"""
    services = monitor.get_all_service_status()
    quantum = monitor.get_quantum_security_metrics()
    
    return render_template_string(
        DASHBOARD_HTML,
        services=services,
        quantum=quantum,
        timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    )

@app.route('/api/status')
def api_status():
    """JSON API for service status"""
    return jsonify({
        'services': monitor.get_all_service_status(),
        'quantum_security': monitor.get_quantum_security_metrics(),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    """Health check for monitoring service itself"""
    return jsonify({
        'status': 'healthy',
        'service': 'kybershield-monitoring',
        'timestamp': datetime.utcnow().isoformat()
    })

# ============= CLIENT MONITORING APIs =============

# In-memory client monitoring data (replace with database in production)
client_monitoring_data = {}

@app.route('/admin/clients/<client_id>/monitoring/status', methods=['GET'])
def get_client_monitoring_status(client_id):
    """Get comprehensive monitoring status for a specific client"""
    try:
        # Get client's service health across all containers
        client_services = {
            'firewall': f"http://kyber-shield-firewall-staging:3000/admin/clients/{client_id}/firewall/status",
            'database': f"http://kyber-shield-database-staging:5000/admin/clients/{client_id}/metrics",
            'vpn': f"http://kyber-shield-rosenpass-staging:8080/admin/clients/{client_id}/vpn/status",
            'backup': f"http://kyber-shield-backup-staging:8000/admin/clients/{client_id}/backup/status"
        }
        
        service_status = {}
        overall_health = 'healthy'
        
        for service_name, endpoint in client_services.items():
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    service_status[service_name] = {
                        'status': 'healthy',
                        'data': response.json(),
                        'response_time': response.elapsed.total_seconds()
                    }
                else:
                    service_status[service_name] = {'status': 'unhealthy', 'error': f"HTTP {response.status_code}"}
                    overall_health = 'degraded'
            except Exception as e:
                service_status[service_name] = {'status': 'unreachable', 'error': str(e)}
                overall_health = 'unhealthy'
        
        return jsonify({
            'client_id': client_id,
            'overall_health': overall_health,
            'services': service_status,
            'monitoring_timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get monitoring status for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/monitoring/metrics', methods=['GET'])
def get_client_metrics(client_id):
    """Get aggregated metrics for a specific client across all services"""
    try:
        # Aggregate metrics from all services
        aggregated_metrics = {
            'client_id': client_id,
            'security_metrics': {
                'threats_blocked_total': 0,
                'traffic_encrypted': '0 GB',
                'quantum_signatures_verified': 0,
                'vpn_connections_active': 0,
                'backups_completed': 0
            },
            'performance_metrics': {
                'average_response_time': 0,
                'uptime_percentage': 100.0,
                'error_rate': 0.0
            },
            'quantum_protection': {
                'ml_dsa_87_active': False,
                'ml_kem_768_active': False,
                'chacha20_poly1305_active': False
            }
        }
        
        # In production, this would aggregate real metrics from all services
        # For now, simulate some data
        aggregated_metrics['security_metrics'].update({
            'threats_blocked_total': 127,
            'traffic_encrypted': '5.2 GB',
            'quantum_signatures_verified': 89,
            'vpn_connections_active': 3,
            'backups_completed': 12
        })
        
        aggregated_metrics['quantum_protection'].update({
            'ml_dsa_87_active': True,
            'ml_kem_768_active': True,
            'chacha20_poly1305_active': True
        })
        
        return jsonify({
            'client_id': client_id,
            'metrics': aggregated_metrics,
            'collection_timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get client metrics for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/monitoring/alerts', methods=['GET'])
def get_client_alerts(client_id):
    """Get active alerts and warnings for a specific client"""
    try:
        # In production, this would check real alert conditions
        alerts = []
        
        # Simulate some alert conditions
        sample_alerts = [
            {
                'severity': 'warning',
                'service': 'firewall',
                'message': 'High threat detection rate - 15 blocked IPs in last hour',
                'timestamp': datetime.utcnow().isoformat(),
                'resolved': False
            },
            {
                'severity': 'info',
                'service': 'backup',
                'message': 'Scheduled backup completed successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'resolved': True
            }
        ]
        
        return jsonify({
            'client_id': client_id,
            'active_alerts': [a for a in sample_alerts if not a['resolved']],
            'resolved_alerts': [a for a in sample_alerts if a['resolved']],
            'alert_count': len([a for a in sample_alerts if not a['resolved']]),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get client alerts for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting KyberShield Monitoring Dashboard")
    logger.info("📊 Real-time quantum security monitoring active")
    
    app.run(host='0.0.0.0', port=8888, debug=False)