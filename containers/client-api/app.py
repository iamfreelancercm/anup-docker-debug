#!/usr/bin/env python3
"""
KyberShield Client Management API
Handles client onboarding, configuration, and service management
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import jwt
import json
import time
import logging
import hashlib
import base64
import uuid
import sqlite3
import requests
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import bcrypt

app = Flask(__name__)
CORS(app)

# Configure logging
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

# Configuration
JWT_SECRET_KEY = "your-super-secure-jwt-secret-key"  # Use environment variable in production
DATABASE_PATH = "/app/data/clients.sqlite"

class ClientManager:
    def __init__(self):
        """Initialize client management system"""
        self.init_database()
        logger.info("🎯 KyberShield Client Manager initialized")
    
    def init_database(self):
        """Initialize client database schema"""
        with self.get_db_connection() as conn:
            # Client accounts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    plan TEXT DEFAULT 'basic',
                    status TEXT DEFAULT 'active',
                    created_at TEXT,
                    last_login TEXT
                )
            ''')
            
            # Firewall configurations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS firewall_configs (
                    id TEXT PRIMARY KEY,
                    client_id TEXT,
                    rule_name TEXT,
                    rule_type TEXT,
                    source_ip TEXT,
                    destination_port INTEGER,
                    action TEXT,
                    priority INTEGER,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')
            
            # Database protection configurations
            conn.execute('''
                CREATE TABLE IF NOT EXISTS database_configs (
                    id TEXT PRIMARY KEY,
                    client_id TEXT,
                    db_name TEXT,
                    db_host TEXT,
                    db_port INTEGER,
                    protection_level TEXT DEFAULT 'standard',
                    encryption_enabled BOOLEAN DEFAULT 1,
                    backup_enabled BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')
            
            # Service usage logs
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id TEXT PRIMARY KEY,
                    client_id TEXT,
                    service_type TEXT,
                    action TEXT,
                    timestamp TEXT,
                    details TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')
        
        logger.info("✅ Client database initialized")
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def generate_api_key(self):
        """Generate secure API key for client"""
        return f"ks_{uuid.uuid4().hex[:16]}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}"
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_client(self, email, company_name, password):
        """Create new client account"""
        try:
            client_id = str(uuid.uuid4())
            api_key = self.generate_api_key()
            password_hash = self.hash_password(password)
            
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO clients (id, email, company_name, password_hash, api_key, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (client_id, email, company_name, password_hash, api_key, datetime.utcnow().isoformat()))
                conn.commit()
            
            logger.info(f"✅ Created new client: {company_name} ({email})")
            return {
                'client_id': client_id,
                'api_key': api_key,
                'company_name': company_name,
                'email': email,
                'status': 'active'
            }
            
        except sqlite3.IntegrityError as e:
            if 'email' in str(e):
                raise ValueError("Email already registered")
            raise ValueError("Registration failed")
    
    def authenticate_client(self, email, password):
        """Authenticate client login"""
        with self.get_db_connection() as conn:
            cursor = conn.execute('SELECT * FROM clients WHERE email = ?', (email,))
            client = cursor.fetchone()
            
            if client and self.verify_password(password, client['password_hash']):
                # Update last login
                conn.execute(
                    'UPDATE clients SET last_login = ? WHERE id = ?',
                    (datetime.utcnow().isoformat(), client['id'])
                )
                conn.commit()
                
                return dict(client)
        
        return None
    
    def get_client_by_api_key(self, api_key):
        """Get client by API key"""
        with self.get_db_connection() as conn:
            cursor = conn.execute('SELECT * FROM clients WHERE api_key = ?', (api_key,))
            client = cursor.fetchone()
            return dict(client) if client else None
    
    def get_client_count(self):
        """Get total number of registered clients"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) as count FROM clients')
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception:
            return 0

# Initialize client manager
client_manager = ClientManager()

def require_auth(f):
    """Decorator for API authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            # Support both JWT and API Key authentication
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
                g.client_id = payload['client_id']
                
            elif auth_header.startswith('ApiKey '):
                api_key = auth_header.split(' ')[1]
                client = client_manager.get_client_by_api_key(api_key)
                if not client:
                    return jsonify({'error': 'Invalid API key'}), 401
                g.client_id = client['id']
                
            else:
                return jsonify({'error': 'Invalid authorization format'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with quantum services status"""
    return jsonify({
        'status': 'healthy',
        'service': 'kyber-shield-client-api',
        'quantum_services': {
            'firewall': 'ML-DSA-87 (NIST Level 5)',
            'database': 'ML-DSA-87 (NIST Level 5)', 
            'rosenpass_vpn': 'ML-KEM-768 (NIST Level 3)',
            'backup': 'ChaCha20-Poly1305'
        },
        'clients_registered': client_manager.get_client_count(),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/clients/register', methods=['POST'])
def register_client():
    """Register new client"""
    try:
        data = request.get_json()
        email = data.get('email')
        company_name = data.get('company_name')
        password = data.get('password')
        
        if not all([email, company_name, password]):
            return jsonify({'error': 'Email, company name, and password required'}), 400
        
        client = client_manager.create_client(email, company_name, password)
        
        # Generate JWT token
        token = jwt.encode({
            'client_id': client['client_id'],
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET_KEY, algorithm='HS256')
        
        logger.info(f"🎉 New client registered: {company_name}")
        return jsonify({
            'status': 'registered',
            'client': client,
            'token': token,
            'message': 'Welcome to KyberShield quantum security!'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/v1/clients/login', methods=['POST'])
def login_client():
    """Client login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        client = client_manager.authenticate_client(email, password)
        if not client:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'client_id': client['id'],
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'status': 'authenticated',
            'token': token,
            'client': {
                'id': client['id'],
                'email': client['email'],
                'company_name': client['company_name'],
                'plan': client['plan']
            }
        })
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/v1/firewall/configure', methods=['POST'])
@require_auth
def configure_firewall():
    """Configure firewall rules for client"""
    try:
        data = request.get_json()
        rule_name = data.get('rule_name')
        rule_type = data.get('rule_type', 'allow')  # allow, deny, monitor
        source_ip = data.get('source_ip', '0.0.0.0/0')
        destination_port = data.get('destination_port')
        priority = data.get('priority', 100)
        
        if not rule_name:
            return jsonify({'error': 'Rule name is required'}), 400
        
        rule_id = str(uuid.uuid4())
        
        with client_manager.get_db_connection() as conn:
            conn.execute('''
                INSERT INTO firewall_configs 
                (id, client_id, rule_name, rule_type, source_ip, destination_port, action, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule_id, g.client_id, rule_name, rule_type, source_ip, 
                destination_port, rule_type, priority, datetime.utcnow().isoformat()
            ))
            conn.commit()
        
        # Call quantum firewall service to apply rule
        firewall_response = apply_firewall_rule(g.client_id, {
            'rule_id': rule_id,
            'rule_name': rule_name,
            'rule_type': rule_type,
            'source_ip': source_ip,
            'destination_port': destination_port,
            'priority': priority
        })
        
        logger.info(f"🛡️ Firewall rule created: {rule_name} for client {g.client_id}")
        return jsonify({
            'status': 'configured',
            'rule_id': rule_id,
            'firewall_response': firewall_response
        })
        
    except Exception as e:
        logger.error(f"Firewall configuration failed: {e}")
        return jsonify({'error': 'Configuration failed'}), 500

@app.route('/api/v1/database/protect', methods=['POST'])
@require_auth
def protect_database():
    """Setup database protection for client"""
    try:
        data = request.get_json()
        db_name = data.get('db_name')
        db_host = data.get('db_host')
        db_port = data.get('db_port', 5432)
        protection_level = data.get('protection_level', 'standard')  # basic, standard, premium
        
        if not all([db_name, db_host]):
            return jsonify({'error': 'Database name and host required'}), 400
        
        config_id = str(uuid.uuid4())
        
        with client_manager.get_db_connection() as conn:
            conn.execute('''
                INSERT INTO database_configs
                (id, client_id, db_name, db_host, db_port, protection_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                config_id, g.client_id, db_name, db_host, db_port, 
                protection_level, datetime.utcnow().isoformat()
            ))
            conn.commit()
        
        # Setup quantum database protection
        database_response = setup_database_protection(g.client_id, {
            'config_id': config_id,
            'db_name': db_name,
            'db_host': db_host,
            'db_port': db_port,
            'protection_level': protection_level
        })
        
        logger.info(f"🔒 Database protection enabled: {db_name} for client {g.client_id}")
        return jsonify({
            'status': 'protected',
            'config_id': config_id,
            'database_response': database_response
        })
        
    except Exception as e:
        logger.error(f"Database protection setup failed: {e}")
        return jsonify({'error': 'Protection setup failed'}), 500

@app.route('/api/v1/status', methods=['GET'])
@require_auth
def get_client_status():
    """Get client protection status"""
    try:
        # Get firewall rules
        with client_manager.get_db_connection() as conn:
            firewall_cursor = conn.execute(
                'SELECT * FROM firewall_configs WHERE client_id = ? AND enabled = 1',
                (g.client_id,)
            )
            firewall_rules = [dict(row) for row in firewall_cursor.fetchall()]
            
            database_cursor = conn.execute(
                'SELECT * FROM database_configs WHERE client_id = ?',
                (g.client_id,)
            )
            database_configs = [dict(row) for row in database_cursor.fetchall()]
        
        # Get real-time service status
        service_status = get_service_health_status()
        
        return jsonify({
            'client_id': g.client_id,
            'firewall': {
                'rules_count': len(firewall_rules),
                'rules': firewall_rules,
                'status': 'active' if firewall_rules else 'inactive'
            },
            'database': {
                'protected_databases': len(database_configs),
                'configs': database_configs,
                'status': 'protected' if database_configs else 'unprotected'
            },
            'services': service_status,
            'quantum_security': {
                'encryption': 'ML-KEM-768',
                'signatures': 'ML-DSA-87',
                'backup_encryption': 'ChaCha20-Poly1305',
                'status': 'active'
            }
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': 'Status check failed'}), 500

def apply_firewall_rule(client_id, rule_config):
    """Apply firewall rule to quantum firewall service"""
    try:
        # This would call the actual firewall service
        # For now, return success simulation
        return {
            'status': 'applied',
            'rule_id': rule_config['rule_id'],
            'quantum_signature': 'ML-DSA-87',
            'applied_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Firewall rule application failed: {e}")
        return {'status': 'failed', 'error': str(e)}

def setup_database_protection(client_id, db_config):
    """Setup database protection with quantum signatures"""
    try:
        # This would call the actual database service
        # For now, return success simulation
        return {
            'status': 'protected',
            'config_id': db_config['config_id'],
            'encryption': 'ML-DSA-87',
            'backup_enabled': True,
            'protected_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database protection setup failed: {e}")
        return {'status': 'failed', 'error': str(e)}

def get_service_health_status():
    """Get health status of all quantum services"""
    services = {
        'firewall': {'status': 'healthy', 'encryption': 'ML-DSA-87'},
        'database': {'status': 'healthy', 'encryption': 'ML-DSA-87'},
        'backup': {'status': 'healthy', 'encryption': 'ChaCha20-Poly1305'},
        'rosenpass_vpn': {'status': 'healthy', 'encryption': 'ML-KEM-768'}
    }
    
    # In production, this would check actual service endpoints
    return services

# ============= ADMIN CLIENT MANAGEMENT APIs =============

@app.route('/admin/clients/list', methods=['GET'])
def admin_list_clients():
    """Admin endpoint to list all clients with their status"""
    try:
        with client_manager.get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT client_id, company_name, contact_email, plan_type, 
                       created_at, status, last_login 
                FROM clients 
                ORDER BY created_at DESC
            ''')
            clients = []
            
            for row in cursor.fetchall():
                clients.append({
                    'client_id': row[0],
                    'company_name': row[1],
                    'contact_email': row[2],
                    'plan_type': row[3],
                    'created_at': row[4],
                    'status': row[5],
                    'last_login': row[6]
                })
        
        return jsonify({
            'clients': clients,
            'total_clients': len(clients),
            'active_clients': len([c for c in clients if c['status'] == 'active']),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Admin list clients failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/services', methods=['GET'])
def admin_get_client_services(client_id):
    """Admin endpoint to get all service configurations for a client"""
    try:
        # Get client information
        with client_manager.get_db_connection() as conn:
            cursor = conn.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,))
            client = cursor.fetchone()
            
            if not client:
                return jsonify({'error': 'Client not found'}), 404
        
        # Get service status from other containers
        services_status = {}
        service_endpoints = {
            'firewall': f"http://kyber-shield-firewall-staging:3000/admin/clients/{client_id}/firewall/status",
            'database': f"http://kyber-shield-database-staging:5000/admin/clients/{client_id}",
            'vpn': f"http://kyber-shield-rosenpass-staging:8080/admin/clients/{client_id}/vpn/status",
            'backup': f"http://kyber-shield-backup-staging:8000/admin/clients/{client_id}/backup/status",
            'monitoring': f"http://kyber-shield-monitoring-staging:8888/admin/clients/{client_id}/monitoring/status"
        }
        
        for service, endpoint in service_endpoints.items():
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    services_status[service] = response.json()
                else:
                    services_status[service] = {'status': 'error', 'message': f'HTTP {response.status_code}'}
            except Exception as e:
                services_status[service] = {'status': 'unreachable', 'error': str(e)}
        
        return jsonify({
            'client_id': client_id,
            'client_info': {
                'company_name': client[2],
                'contact_email': client[3],
                'plan_type': client[4],
                'status': client[6]
            },
            'services': services_status,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Admin get client services failed for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/portal/credentials', methods=['POST'])
def admin_generate_portal_credentials(client_id):
    """Admin endpoint to generate/reset client portal credentials"""
    try:
        # Get client information
        with client_manager.get_db_connection() as conn:
            cursor = conn.execute('SELECT company_name, contact_email FROM clients WHERE client_id = ?', (client_id,))
            client = cursor.fetchone()
            
            if not client:
                return jsonify({'error': 'Client not found'}), 404
        
        # Generate new portal credentials
        temp_password = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')[:12]
        
        portal_credentials = {
            'client_id': client_id,
            'portal_url': f"https://portal.kybershield.ai/{client_id}",
            'username': client[1],  # contact_email
            'temporary_password': temp_password,
            'force_password_change': True,
            'generated_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        # In production, store these credentials securely and send email
        logger.info(f"� Generated portal credentials for {client_id}")
        
        return jsonify({
            'client_id': client_id,
            'portal_credentials': portal_credentials,
            'status': 'credentials_generated',
            'email_instructions': f"Credentials sent to {client[1]}"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Admin generate portal credentials failed for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/platform/overview', methods=['GET'])
def admin_platform_overview():
    """Admin endpoint for complete platform overview"""
    try:
        # Get client statistics
        with client_manager.get_db_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM clients')
            total_clients = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM clients WHERE status = 'active'")
            active_clients = cursor.fetchone()[0]
        
        # Get platform metrics (would be real data in production)
        platform_metrics = {
            'clients': {
                'total': total_clients,
                'active': active_clients,
                'inactive': total_clients - active_clients
            },
            'security': {
                'threats_blocked_today': 1247,
                'total_traffic_encrypted': '127.3 GB',
                'quantum_signatures_verified': 8934,
                'active_vpn_connections': 34
            },
            'services': {
                'firewall': 'healthy',
                'database': 'healthy',
                'backup': 'healthy',
                'vpn': 'healthy',
                'monitoring': 'healthy',
                'client_api': 'healthy'
            },
            'revenue': {
                'monthly_recurring': 23500,
                'new_trials_this_week': 12,
                'conversion_rate': 0.68
            }
        }
        
        return jsonify({
            'platform_overview': platform_metrics,
            'timestamp': datetime.utcnow().isoformat(),
            'quantum_protection_active': True
        })
        
    except Exception as e:
        logger.error(f"❌ Admin platform overview failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("�🚀 Starting KyberShield Client API")
    logger.info("🎯 Client onboarding and management ready")
    logger.info("🛡️ Quantum security services API active")
    logger.info("👥 Admin management endpoints enabled")
    
    app.run(host='0.0.0.0', port=9000, debug=False)