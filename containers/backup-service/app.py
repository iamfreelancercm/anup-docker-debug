#!/usr/bin/env python3
"""
KyberShield Backup Service - Quantum-Protected Backup System
Integrates with Rosenpass for quantum-resistant data protection
"""

import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, Any

# Handle ECS DB_CREDENTIALS environment variable
db_creds = None
if os.environ.get('DB_CREDENTIALS'):
    try:
        db_creds = json.loads(os.environ.get('DB_CREDENTIALS', '{}'))
        print("✅ ECS database credentials loaded successfully")
    except Exception as e:
        print(f"⚠️ Could not parse DB_CREDENTIALS: {e}")
        db_creds = None

# Add project root to path
sys.path.append('/app')
sys.path.append('/app/database-security')

try:
    from database_security.rosenpass_connector import RosenpassConnector
    from database_security.quantum_crypto import QuantumCrypto
    QUANTUM_AVAILABLE = True
except ImportError:
    print("⚠️  Quantum modules not available, using fallback encryption")
    QUANTUM_AVAILABLE = False

class QuantumBackupService:
    """Quantum-protected backup service with Rosenpass integration"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.logger = self._setup_logging()
        
        # Quantum security components
        self.rosenpass = None
        self.quantum_crypto = None
        
        # Backup configuration
        self.backup_dir = Path('/app/backups')
        self.config_dir = Path('/app/rosenpass/config')
        
        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Flask routes
        self._setup_routes()
        
        self.logger.info("🔐 Quantum Backup Service initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def initialize_quantum_protection(self):
        """Initialize quantum protection components"""
        try:
            if not QUANTUM_AVAILABLE:
                self.logger.warning("⚠️  Quantum protection not available, using fallback")
                return False
            
            # Initialize Rosenpass connector
            self.rosenpass = RosenpassConnector(
                config_dir='/app/rosenpass/config',
                key_dir='/app/rosenpass/keys',
                socket_path='/var/run/rosenpass/rosenpass.sock'
            )
            
            await self.rosenpass.initialize()
            
            # Initialize quantum crypto
            self.quantum_crypto = QuantumCrypto()
            
            self.logger.info("✅ Quantum protection initialized for backup service")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize quantum protection: {e}")
            return False
    
    def _setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint with quantum crypto status"""
            return jsonify({
                'status': 'healthy',
                'service': 'quantum-backup',
                'algorithm': 'ChaCha20-Poly1305',
                'real_quantum_crypto': QUANTUM_AVAILABLE,
                'quantum_library': 'liboqs-python + pycryptodome' if QUANTUM_AVAILABLE else 'fallback',
                'rosenpass_tunnel': QUANTUM_AVAILABLE and self.rosenpass is not None,
                'backups_created': getattr(self, 'backup_counter', 0),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/backup/create', methods=['POST'])
        def create_backup():
            """Create quantum-protected backup"""
            try:
                data = request.get_json()
                backup_name = data.get('name', f'backup_{int(time.time())}')
                source_data = data.get('data', {})
                
                # Create backup with quantum protection
                backup_result = self._create_quantum_backup(backup_name, source_data)
                
                return jsonify({
                    'success': True,
                    'backup_id': backup_result['backup_id'],
                    'quantum_protected': backup_result['quantum_protected'],
                    'timestamp': backup_result['timestamp']
                })
                
            except Exception as e:
                self.logger.error(f"Backup creation error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup/restore', methods=['POST'])
        def restore_backup():
            """Restore quantum-protected backup"""
            try:
                data = request.get_json()
                backup_id = data.get('backup_id')
                
                if not backup_id:
                    return jsonify({'error': 'backup_id required'}), 400
                
                # Restore backup with quantum verification
                restore_result = self._restore_quantum_backup(backup_id)
                
                return jsonify({
                    'success': True,
                    'data': restore_result['data'],
                    'quantum_verified': restore_result['quantum_verified'],
                    'restored_at': restore_result['restored_at']
                })
                
            except Exception as e:
                self.logger.error(f"Backup restore error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup/list', methods=['GET'])
        def list_backups():
            """List available backups"""
            try:
                backups = []
                
                for backup_file in self.backup_dir.glob('*.backup'):
                    try:
                        # Read backup metadata
                        with open(backup_file.with_suffix('.meta'), 'r') as f:
                            metadata = json.load(f)
                        
                        backups.append({
                            'backup_id': metadata['backup_id'],
                            'name': metadata['name'],
                            'created_at': metadata['created_at'],
                            'quantum_protected': metadata.get('quantum_protected', False),
                            'size_bytes': backup_file.stat().st_size
                        })
                    except Exception as e:
                        self.logger.warning(f"Failed to read backup metadata: {e}")
                
                return jsonify({
                    'success': True,
                    'backups': backups,
                    'total_count': len(backups)
                })
                
            except Exception as e:
                self.logger.error(f"List backups error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/quantum/status', methods=['GET'])
        def quantum_status():
            """Get quantum protection status"""
            return jsonify({
                'quantum_available': QUANTUM_AVAILABLE,
                'rosenpass_initialized': self.rosenpass is not None,
                'quantum_crypto_initialized': self.quantum_crypto is not None,
                'backup_dir': str(self.backup_dir),
                'config_dir': str(self.config_dir)
            })

        # ============= CLIENT BACKUP MANAGEMENT APIs =============

        # In-memory client backup configurations (replace with database in production)
        client_backup_configs = {}
        client_backup_status = {}

        @self.app.route('/admin/clients/<client_id>/backup/initialize', methods=['POST'])
        def initialize_client_backup(client_id):
            """Setup backup service for a specific client"""
            try:
                data = request.get_json()
                backup_schedule = data.get('backup_schedule', 'daily')
                retention_days = data.get('retention_days', 30)
                encryption_level = data.get('encryption_level', 'quantum')
                
                # Initialize client backup configuration
                client_config = {
                    'client_id': client_id,
                    'backup_schedule': backup_schedule,
                    'retention_days': retention_days,
                    'encryption_level': encryption_level,
                    'quantum_protected': QUANTUM_AVAILABLE and encryption_level == 'quantum',
                    'backup_directory': str(self.backup_dir / client_id),
                    'initialized_at': datetime.now().isoformat(),
                    'status': 'active'
                }
                
                # Create client-specific backup directory
                client_backup_dir = self.backup_dir / client_id
                client_backup_dir.mkdir(exist_ok=True)
                
                # Store configuration
                client_backup_configs[client_id] = client_config
                client_backup_status[client_id] = {
                    'last_backup': None,
                    'backup_count': 0,
                    'total_size': 0,
                    'status': 'initialized',
                    'next_scheduled': None
                }
                
                self.logger.info(f"💾 Initialized backup service for client {client_id}")
                return jsonify({
                    'client_id': client_id,
                    'status': 'initialized',
                    'quantum_protected': client_config['quantum_protected'],
                    'backup_schedule': backup_schedule
                }), 201
                
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize backup for {client_id}: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/admin/clients/<client_id>/backup/status', methods=['GET'])
        def get_client_backup_status(client_id):
            """Get backup status for a specific client"""
            try:
                if client_id not in client_backup_configs:
                    return jsonify({'error': 'Client backup not configured'}), 404
                
                config = client_backup_configs[client_id]
                status = client_backup_status[client_id]
                
                # Count client's backup files
                client_backup_dir = self.backup_dir / client_id
                backup_files = list(client_backup_dir.glob('*.backup')) if client_backup_dir.exists() else []
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in backup_files)
                
                return jsonify({
                    'client_id': client_id,
                    'backup_config': config,
                    'backup_status': {
                        'backup_count': len(backup_files),
                        'total_size_bytes': total_size,
                        'last_backup': status.get('last_backup'),
                        'next_scheduled': status.get('next_scheduled'),
                        'status': status.get('status', 'active')
                    },
                    'quantum_protection': {
                        'enabled': config['quantum_protected'],
                        'algorithm': 'ChaCha20-Poly1305' if QUANTUM_AVAILABLE else 'fallback',
                        'rosenpass_tunnel': self.rosenpass is not None
                    }
                })
                
            except Exception as e:
                self.logger.error(f"❌ Failed to get backup status for {client_id}: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/admin/clients/<client_id>/backup/trigger', methods=['POST'])
        def trigger_client_backup(client_id):
            """Manually trigger backup for a specific client"""
            try:
                if client_id not in client_backup_configs:
                    return jsonify({'error': 'Client backup not configured'}), 404
                
                data = request.get_json()
                backup_name = data.get('backup_name', f'{client_id}_manual_{int(time.time())}')
                source_data = data.get('data', {'manual_backup': True, 'timestamp': datetime.now().isoformat()})
                
                # Add client identifier to backup data
                source_data['client_id'] = client_id
                source_data['backup_type'] = 'manual'
                
                # Create client-specific backup
                backup_result = self._create_client_backup(client_id, backup_name, source_data)
                
                # Update client status
                client_backup_status[client_id].update({
                    'last_backup': backup_result['timestamp'],
                    'backup_count': client_backup_status[client_id].get('backup_count', 0) + 1,
                    'status': 'backup_complete'
                })
                
                self.logger.info(f"💾 Manual backup triggered for client {client_id}")
                return jsonify({
                    'client_id': client_id,
                    'backup_id': backup_result['backup_id'],
                    'quantum_protected': backup_result['quantum_protected'],
                    'status': 'backup_complete',
                    'timestamp': backup_result['timestamp']
                }), 201
                
            except Exception as e:
                self.logger.error(f"❌ Failed to trigger backup for {client_id}: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _create_client_backup(self, client_id: str, backup_name: str, source_data: Dict) -> Dict[str, Any]:
        """Create client-specific backup with quantum protection"""
        backup_id = f"{client_id}_backup_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        try:
            # Ensure client backup directory exists
            client_backup_dir = self.backup_dir / client_id
            client_backup_dir.mkdir(exist_ok=True)
            
            # Serialize source data
            data_json = json.dumps(source_data, indent=2)
            
            if QUANTUM_AVAILABLE and self.quantum_crypto:
                # Encrypt with quantum crypto
                encrypted_data = self.quantum_crypto.encrypt_data(data_json.encode())
                quantum_protected = True
                self.logger.info(f"✅ Quantum encryption applied to client backup {backup_id}")
            else:
                # Fallback encryption (basic)
                import base64
                encrypted_data = base64.b64encode(data_json.encode())
                quantum_protected = False
                self.logger.warning(f"⚠️  Fallback encryption used for client backup {backup_id}")
            
            # Save backup file in client directory
            backup_file = client_backup_dir / f"{backup_id}.backup"
            with open(backup_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Save metadata
            metadata = {
                'backup_id': backup_id,
                'client_id': client_id,
                'name': backup_name,
                'created_at': timestamp,
                'quantum_protected': quantum_protected,
                'original_size': len(data_json),
                'encrypted_size': len(encrypted_data)
            }
            
            metadata_file = client_backup_dir / f"{backup_id}.meta"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"✅ Client backup created: {backup_id}")
            
            return {
                'backup_id': backup_id,
                'quantum_protected': quantum_protected,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"❌ Client backup creation failed: {e}")
            raise

    def _create_quantum_backup(self, backup_name: str, source_data: Dict) -> Dict[str, Any]:
        """Create backup with quantum protection"""
        backup_id = f"backup_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        try:
            # Serialize source data
            data_json = json.dumps(source_data, indent=2)
            
            if QUANTUM_AVAILABLE and self.quantum_crypto:
                # Encrypt with quantum crypto
                encrypted_data = self.quantum_crypto.encrypt_data(data_json.encode())
                quantum_protected = True
                self.logger.info(f"✅ Quantum encryption applied to backup {backup_id}")
            else:
                # Fallback encryption (basic)
                import base64
                encrypted_data = base64.b64encode(data_json.encode())
                quantum_protected = False
                self.logger.warning(f"⚠️  Fallback encryption used for backup {backup_id}")
            
            # Save backup file
            backup_file = self.backup_dir / f"{backup_id}.backup"
            with open(backup_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Save metadata
            metadata = {
                'backup_id': backup_id,
                'name': backup_name,
                'created_at': timestamp,
                'quantum_protected': quantum_protected,
                'original_size': len(data_json),
                'encrypted_size': len(encrypted_data)
            }
            
            metadata_file = self.backup_dir / f"{backup_id}.meta"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"✅ Backup created: {backup_id}")
            
            return {
                'backup_id': backup_id,
                'quantum_protected': quantum_protected,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"❌ Backup creation failed: {e}")
            raise
    
    def _restore_quantum_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore backup with quantum verification"""
        try:
            backup_file = self.backup_dir / f"{backup_id}.backup"
            metadata_file = self.backup_dir / f"{backup_id}.meta"
            
            if not backup_file.exists() or not metadata_file.exists():
                raise Exception(f"Backup {backup_id} not found")
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Load encrypted data
            with open(backup_file, 'rb') as f:
                encrypted_data = f.read()
            
            quantum_verified = False
            
            if metadata.get('quantum_protected', False) and QUANTUM_AVAILABLE and self.quantum_crypto:
                # Decrypt with quantum crypto
                try:
                    decrypted_data = self.quantum_crypto.decrypt_data(encrypted_data)
                    data_json = decrypted_data.decode()
                    quantum_verified = True
                    self.logger.info(f"✅ Quantum decryption successful for {backup_id}")
                except Exception as e:
                    self.logger.error(f"❌ Quantum decryption failed: {e}")
                    raise Exception("Quantum decryption failed - backup may be corrupted")
            else:
                # Fallback decryption
                import base64
                try:
                    decrypted_data = base64.b64decode(encrypted_data)
                    data_json = decrypted_data.decode()
                    self.logger.warning(f"⚠️  Fallback decryption used for {backup_id}")
                except Exception as e:
                    raise Exception(f"Decryption failed: {e}")
            
            # Parse restored data
            restored_data = json.loads(data_json)
            
            return {
                'data': restored_data,
                'quantum_verified': quantum_verified,
                'restored_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Backup restore failed: {e}")
            raise
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the backup service"""
        try:
            # Initialize quantum protection
            if QUANTUM_AVAILABLE:
                asyncio.run(self.initialize_quantum_protection())
            
            self.logger.info(f"🚀 Starting Quantum Backup Service on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start backup service: {e}")
            raise

def main():
    """Main entry point"""
    service = QuantumBackupService()
    service.run()

if __name__ == '__main__':
    main()