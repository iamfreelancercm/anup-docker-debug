#!/usr/bin/env python3
"""
KyberShield Real-Time Monitoring Dashboard
Live monitoring with auto-refresh
"""

import time
import os
import json
import sys
from datetime import datetime
import subprocess
from aws_health_checker import KyberShieldHealthChecker

class RealtimeDashboard:
    def __init__(self, refresh_interval=30):
        self.refresh_interval = refresh_interval
        self.checker = KyberShieldHealthChecker()
        self.running = True
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def display_live_dashboard(self):
        """Display live monitoring dashboard"""
        print("🔴 Starting KyberShield Live Monitoring Dashboard...")
        print("Press Ctrl+C to stop")
        time.sleep(2)
        
        while self.running:
            try:
                self.clear_screen()
                
                print("🔴 LIVE KyberShield Monitoring Dashboard")
                print("=" * 60)
                print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Auto-refresh: {self.refresh_interval}s | Press Ctrl+C to exit")
                print("=" * 60)
                
                # Quick status check
                try:
                    report = self.checker.generate_comprehensive_report()
                    
                    # Service status
                    print("🔧 SERVICE STATUS:")
                    for service_name, service_data in report['services'].items():
                        status = service_data['status']
                        response_time = service_data.get('response_time', 0)
                        
                        if status == 'healthy':
                            status_emoji = "🟢"
                        elif status == 'timeout':
                            status_emoji = "🟡"
                        else:
                            status_emoji = "🔴"
                        
                        quantum_emoji = "🔐" if service_data.get('quantum_crypto') else "🔓"
                        ai_emoji = "🤖" if service_data.get('ai_defense') else "🧠"
                        
                        print(f"  {status_emoji} {service_name:15} | {status:10} | {response_time:6.2f}s | {quantum_emoji} {ai_emoji}")
                    
                    # Overall system health
                    overall = report['overall_status']
                    overall_emoji = "🟢" if overall == 'healthy' else "🟡" if overall == 'degraded' else "🔴"
                    print(f"\n{overall_emoji} OVERALL SYSTEM: {overall.upper()}")
                    
                    # Quantum crypto status
                    quantum = report['quantum_crypto']
                    print(f"\n🔐 QUANTUM SECURITY:")
                    print(f"  ML-KEM-768: {'✅' if quantum.get('ml_kem_768') else '❌'}")
                    print(f"  Rosenpass:  {'✅' if quantum.get('rosenpass_vpn') else '❌'}")
                    print(f"  ChaCha20:   {'✅' if quantum.get('chacha20_poly1305') else '❌'}")
                    
                    # AI defense status
                    ai_defense = report['ai_defense']
                    patterns = ai_defense.get('attack_patterns_loaded', 0)
                    print(f"\n🤖 AI DEFENSE:")
                    print(f"  Patterns: {patterns}/243+ loaded")
                    print(f"  SQL Defense: {'✅' if ai_defense.get('sql_injection_defense') else '❌'}")
                    print(f"  Malware Detection: {'✅' if ai_defense.get('malware_detection') else '❌'}")
                    
                    # ECS status
                    ecs = report.get('ecs_cluster', {})
                    cluster_status = ecs.get('cluster_status', 'unknown')
                    print(f"\n☁️ ECS CLUSTER: {cluster_status}")
                    
                    services_info = ecs.get('services', {})
                    if services_info:
                        print("  Services:")
                        for svc_name, svc_info in services_info.items():
                            running = svc_info.get('running_count', 0)
                            desired = svc_info.get('desired_count', 0)
                            emoji = "✅" if running == desired else "⚠️"
                            print(f"    {emoji} {svc_name}: {running}/{desired}")
                    
                    # Recommendations
                    recommendations = report.get('recommendations', [])
                    if recommendations:
                        print(f"\n💡 ACTION ITEMS:")
                        for i, rec in enumerate(recommendations[:3], 1):
                            print(f"  {i}. {rec}")
                    else:
                        print(f"\n✅ No critical issues detected")
                        
                except Exception as e:
                    print(f"\n❌ Monitoring error: {e}")
                    print("Retrying in next cycle...")
                
                print(f"\n⏱️ Next refresh in {self.refresh_interval} seconds...")
                print("📊 Press Ctrl+C to stop monitoring")
                
                # Wait for next refresh
                for i in range(self.refresh_interval):
                    time.sleep(1)
                    if not self.running:
                        break
                
            except KeyboardInterrupt:
                print("\n\n👋 Dashboard stopped by user")
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ Dashboard error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)

def main():
    """Start real-time dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KyberShield Real-Time Monitoring Dashboard')
    parser.add_argument('--refresh', type=int, default=30, help='Refresh interval in seconds (default: 30)')
    args = parser.parse_args()
    
    dashboard = RealtimeDashboard(refresh_interval=args.refresh)
    
    try:
        dashboard.display_live_dashboard()
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
    except Exception as e:
        print(f"❌ Dashboard failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()