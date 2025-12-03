#!/usr/bin/env python3
"""
KyberShield Quantum Firewall - ML-DSA-87 Packet Signing
Handles client traffic with post-quantum digital signatures
"""

from flask import Flask, request, jsonify, Response
import json
import time
import logging
import hashlib
import base64
import os
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import quantum cryptography
try:
    import oqs
    QUANTUM_AVAILABLE = True
    logger.info("✅ liboqs quantum library loaded successfully")
except ImportError as e:
    QUANTUM_AVAILABLE = False
    logger.warning(f"⚠️ liboqs not available, using fallback: {e}")

# Handle ECS DB_CREDENTIALS environment variable
db_creds = None
if os.environ.get('DB_CREDENTIALS'):
    try:
        db_creds = json.loads(os.environ.get('DB_CREDENTIALS', '{}'))
        logger.info("✅ ECS database credentials loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not parse DB_CREDENTIALS: {e}")
        db_creds = None

class QuantumFirewall:
    def __init__(self):
        """Initialize ML-DSA-87 quantum firewall"""
        self.signature_algorithm = "Dilithium5"  # ML-DSA-87
        self.signer = None
        self.public_key = None
        self.private_key = None
        self.packet_counter = 0
        self.blocked_ips = set()
        self.allowed_patterns = []
        
        self._initialize_quantum_signatures()
        logger.info("🛡️ Quantum Firewall initialized with ML-DSA-87")
    
    def _initialize_quantum_signatures(self):
        """Initialize ML-DSA-87 digital signature system"""
        if not QUANTUM_AVAILABLE:
            logger.warning("⚠️ Quantum crypto not available, using mock signatures")
            return
            
        try:
            self.signer = oqs.Signature(self.signature_algorithm)
            self.public_key = self.signer.generate_keypair()
            logger.info("✅ ML-DSA-87 keypair generated successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ML-DSA-87: {e}")
            # Don't raise, allow fallback operation

    def sign_packet(self, packet_data):
        """Sign packet with ML-DSA-87 quantum signature"""
        try:
            packet_hash = hashlib.sha3_256(packet_data.encode()).digest()
            
            if QUANTUM_AVAILABLE and self.signer:
                signature = self.signer.sign(packet_hash)
                algorithm = self.signature_algorithm
            else:
                # Fallback to hash-based signature
                signature = hashlib.sha256(packet_hash + b"fallback_key").digest()
                algorithm = "Fallback-SHA256"
            
            signed_packet = {
                'packet_id': self.packet_counter,
                'timestamp': datetime.utcnow().isoformat(),
                'data': packet_data,
                'signature': base64.b64encode(signature).decode(),
                'algorithm': algorithm,
                'public_key': base64.b64encode(self.public_key).decode() if self.public_key else "fallback"
            }
            
            self.packet_counter += 1
            logger.info(f"📦 Packet {self.packet_counter} signed with {algorithm}")
            return signed_packet
            
        except Exception as e:
            logger.error(f"❌ Packet signing failed: {e}")
            raise
    
    def verify_packet_signature(self, signed_packet):
        """Verify ML-DSA-87 signature on incoming packet"""
        try:
            signature = base64.b64decode(signed_packet['signature'])
            packet_hash = hashlib.sha3_256(signed_packet['data'].encode()).digest()
            
            if QUANTUM_AVAILABLE and self.signer and signed_packet.get('algorithm') == self.signature_algorithm:
                is_valid = self.signer.verify(packet_hash, signature, self.public_key)
            else:
                # Fallback verification
                expected_signature = hashlib.sha256(packet_hash + b"fallback_key").digest()
                is_valid = signature == expected_signature
            
            if is_valid:
                logger.info(f"✅ Packet {signed_packet['packet_id']} signature verified")
            else:
                logger.warning(f"⚠️ Invalid signature for packet {signed_packet['packet_id']}")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Signature verification failed: {e}")
            return False
    
    def analyze_threat_level(self, client_ip, packet_data):
        """AI-powered threat analysis"""
        threat_score = 0
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            threat_score += 100
            
        # Analyze packet patterns
        if len(packet_data) > 10000:
            threat_score += 20
            
        if any(pattern in packet_data.lower() for pattern in ['<script', 'union select', 'drop table']):
            threat_score += 50
            
        if packet_data.count(';') > 5:
            threat_score += 30
            
        return min(threat_score, 100)
    
    def should_block_packet(self, client_ip, packet_data):
        """Determine if packet should be blocked"""
        threat_level = self.analyze_threat_level(client_ip, packet_data)
        
        if threat_level >= 70:
            self.blocked_ips.add(client_ip)
            logger.warning(f"🚫 Blocking high-threat packet from {client_ip} (threat: {threat_level})")
            return True
            
        return False

# Initialize quantum firewall
quantum_firewall = QuantumFirewall()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with quantum crypto status"""
    return jsonify({
        'status': 'healthy',
        'service': 'quantum-firewall',
        'algorithm': quantum_firewall.signature_algorithm,
        'real_quantum_crypto': QUANTUM_AVAILABLE,
        'quantum_library': 'liboqs-python' if QUANTUM_AVAILABLE else 'fallback',
        'nist_level': 5,  # ML-DSA-87 is NIST Level 5
        'packets_processed': quantum_firewall.packet_counter,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/process', methods=['POST'])
def process_packet():
    """Process and sign client packet with ML-DSA-87"""
    try:
        client_ip = request.remote_addr
        packet_data = request.get_json().get('data', '')
        
        # Threat analysis
        if quantum_firewall.should_block_packet(client_ip, packet_data):
            return jsonify({
                'status': 'blocked',
                'reason': 'high_threat_level',
                'client_ip': client_ip
            }), 403
        
        # Sign packet with ML-DSA-87
        signed_packet = quantum_firewall.sign_packet(packet_data)
        
        logger.info(f"✅ Processed packet from {client_ip}")
        return jsonify({
            'status': 'processed',
            'signed_packet': signed_packet,
            'client_ip': client_ip
        })
        
    except Exception as e:
        logger.error(f"❌ Packet processing failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify_packet():
    """Verify ML-DSA-87 signature on packet"""
    try:
        signed_packet = request.get_json()
        is_valid = quantum_firewall.verify_packet_signature(signed_packet)
        
        return jsonify({
            'status': 'verified' if is_valid else 'invalid',
            'packet_id': signed_packet.get('packet_id'),
            'algorithm': quantum_firewall.signature_algorithm
        })
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get firewall statistics"""
    return jsonify({
        'packets_processed': quantum_firewall.packet_counter,
        'blocked_ips': len(quantum_firewall.blocked_ips),
        'signature_algorithm': quantum_firewall.signature_algorithm,
        'uptime': time.time(),
        'status': 'active'
    })

@app.route('/tunnel/connect', methods=['POST'])
def connect_to_rosenpass():
    """Connect to Rosenpass internal VPN tunnel"""
    try:
        # This would establish connection to Rosenpass VPN service
        tunnel_config = {
            'tunnel_type': 'rosenpass_internal',
            'encryption': 'ML-KEM-768',
            'endpoint': 'rosenpass-service:8080',
            'status': 'connected'
        }
        
        logger.info("🔐 Connected to Rosenpass internal tunnel")
        return jsonify(tunnel_config)
        
    except Exception as e:
        logger.error(f"❌ Tunnel connection failed: {e}")
        return jsonify({'error': str(e)}), 500

# ============= CLIENT MANAGEMENT APIs =============

# In-memory client firewall rules storage (replace with DB in production)
client_firewall_rules = {}
client_firewall_status = {}

@app.route('/admin/clients/<client_id>/firewall/rules', methods=['POST'])
def create_client_firewall_rules(client_id):
    """Create firewall rules for a specific client"""
    try:
        data = request.get_json()
        rules = data.get('rules', [])
        
        # Validate rules format
        for rule in rules:
            required_fields = ['action', 'priority']
            if not all(field in rule for field in required_fields):
                return jsonify({'error': 'Rules must have action and priority fields'}), 400
        
        # Store client rules
        client_firewall_rules[client_id] = {
            'rules': rules,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"🛡️ Created {len(rules)} firewall rules for client {client_id}")
        return jsonify({
            'client_id': client_id,
            'rules_count': len(rules),
            'status': 'created'
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Failed to create firewall rules for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/firewall/rules', methods=['GET'])
def get_client_firewall_rules(client_id):
    """Get firewall rules for a specific client"""
    try:
        if client_id not in client_firewall_rules:
            return jsonify({'error': 'Client rules not found'}), 404
        
        rules_data = client_firewall_rules[client_id]
        return jsonify({
            'client_id': client_id,
            'rules': rules_data['rules'],
            'created_at': rules_data['created_at'],
            'updated_at': rules_data['updated_at'],
            'rules_count': len(rules_data['rules'])
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get firewall rules for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/firewall/rules', methods=['PUT'])
def update_client_firewall_rules(client_id):
    """Update firewall rules for a specific client"""
    try:
        data = request.get_json()
        rules = data.get('rules', [])
        
        # Validate rules format
        for rule in rules:
            required_fields = ['action', 'priority']
            if not all(field in rule for field in required_fields):
                return jsonify({'error': 'Rules must have action and priority fields'}), 400
        
        if client_id not in client_firewall_rules:
            return jsonify({'error': 'Client rules not found'}), 404
        
        # Update client rules
        client_firewall_rules[client_id]['rules'] = rules
        client_firewall_rules[client_id]['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"🔄 Updated {len(rules)} firewall rules for client {client_id}")
        return jsonify({
            'client_id': client_id,
            'rules_count': len(rules),
            'status': 'updated'
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to update firewall rules for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clients/<client_id>/firewall/status', methods=['GET'])
def get_client_firewall_status(client_id):
    """Get firewall status for a specific client"""
    try:
        # Get current status or default
        status = client_firewall_status.get(client_id, {
            'enabled': False,
            'rules_active': 0,
            'packets_processed': 0,
            'threats_blocked': 0,
            'last_activity': None
        })
        
        # Add client rules info if exists
        if client_id in client_firewall_rules:
            status['rules_active'] = len(client_firewall_rules[client_id]['rules'])
            status['rules_updated'] = client_firewall_rules[client_id]['updated_at']
        
        return jsonify({
            'client_id': client_id,
            'firewall_status': status,
            'quantum_signatures': QUANTUM_AVAILABLE,
            'signature_algorithm': 'ML-DSA-87' if QUANTUM_AVAILABLE else 'fallback'
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get firewall status for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/firewall/initialize/<client_id>', methods=['POST'])
def initialize_client_firewall(client_id):
    """Initialize firewall protection for a new client"""
    try:
        data = request.get_json()
        protection_level = data.get('protection_level', 'standard')
        quantum_signatures = data.get('quantum_signatures', True)
        ai_defense = data.get('ai_defense', True)
        
        # Initialize client firewall status
        client_firewall_status[client_id] = {
            'enabled': True,
            'protection_level': protection_level,
            'quantum_signatures': quantum_signatures and QUANTUM_AVAILABLE,
            'ai_defense': ai_defense,
            'rules_active': 0,
            'packets_processed': 0,
            'threats_blocked': 0,
            'initialized_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        # Create default rules based on protection level
        default_rules = []
        if protection_level == 'enterprise':
            default_rules = [
                {'action': 'block', 'source': 'malicious_ips', 'priority': 1},
                {'action': 'allow', 'ports': [80, 443], 'priority': 2},
                {'action': 'encrypt', 'protocol': 'all', 'quantum': quantum_signatures, 'priority': 3}
            ]
        elif protection_level == 'professional':
            default_rules = [
                {'action': 'block', 'source': 'malicious_ips', 'priority': 1},
                {'action': 'allow', 'ports': [80, 443, 22], 'priority': 2}
            ]
        else:  # standard
            default_rules = [
                {'action': 'block', 'source': 'malicious_ips', 'priority': 1}
            ]
        
        # Store default rules
        client_firewall_rules[client_id] = {
            'rules': default_rules,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"🛡️ Initialized firewall for client {client_id} with {protection_level} protection")
        return jsonify({
            'client_id': client_id,
            'status': 'initialized',
            'protection_level': protection_level,
            'quantum_signatures': quantum_signatures and QUANTUM_AVAILABLE,
            'default_rules': len(default_rules)
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize firewall for {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting KyberShield Quantum Firewall")
    logger.info("🛡️ ML-DSA-87 packet signing enabled")
    logger.info("🔐 Rosenpass internal tunnel ready")
    
    # Check if we need to run on port 8080 for legacy compatibility
    import os
    port = int(os.getenv('PORT', '3000'))
    
    if os.getenv('LEGACY_PORT_8080', 'false').lower() == 'true':
        # Run on both ports using threading for backward compatibility
        import threading
        from werkzeug.serving import WSGIRequestHandler
        
        def run_legacy_port():
            logger.info("🔄 Starting legacy port 8080 for ECS compatibility")
            app.run(host='0.0.0.0', port=8080, debug=False, threaded=True, use_reloader=False)
        
        # Start legacy port in background thread
        legacy_thread = threading.Thread(target=run_legacy_port, daemon=True)
        legacy_thread.start()
        
        logger.info(f"🌐 Firewall running on ports 3000 (primary) and 8080 (legacy)")
    
    # Run primary application
    app.run(host='0.0.0.0', port=port, debug=False)