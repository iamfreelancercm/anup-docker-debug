#!/usr/bin/env python3
"""
KyberShield AWS Deployment Monitor
Monitor your actual AWS deployment without local credentials
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class AWSDeploymentMonitor:
    def __init__(self):
        self.github_repo = "Chrisofzo/KyberShield-Firewall"
        self.branch = "AWS-Push"
        
    def check_github_actions_status(self) -> Dict[str, Any]:
        """Check GitHub Actions deployment status"""
        print("🚀 Checking GitHub Actions Deployment Status...")
        
        status = {
            'latest_run': {},
            'deployment_status': 'unknown',
            'services_built': [],
            'error': None
        }
        
        try:
            # Check latest workflow runs
            api_url = f"https://api.github.com/repos/{self.github_repo}/actions/runs"
            params = {'branch': self.branch, 'per_page': 5}
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                runs_data = response.json()
                
                if runs_data['workflow_runs']:
                    latest_run = runs_data['workflow_runs'][0]
                    status['latest_run'] = {
                        'id': latest_run['id'],
                        'status': latest_run['status'],
                        'conclusion': latest_run['conclusion'],
                        'created_at': latest_run['created_at'],
                        'html_url': latest_run['html_url'],
                        'workflow_name': latest_run['name']
                    }
                    
                    # Determine deployment status
                    if latest_run['conclusion'] == 'success':
                        status['deployment_status'] = 'successful'
                        status['services_built'] = ['rosenpass', 'backup']  # Based on our workflow
                    elif latest_run['conclusion'] == 'failure':
                        status['deployment_status'] = 'failed'
                    elif latest_run['status'] == 'in_progress':
                        status['deployment_status'] = 'in_progress'
                    else:
                        status['deployment_status'] = 'unknown'
                        
            else:
                status['error'] = f"GitHub API returned {response.status_code}"
                
        except Exception as e:
            status['error'] = str(e)
            
        return status

    def get_aws_monitoring_commands(self) -> Dict[str, List[str]]:
        """Generate AWS CLI commands to check your deployment"""
        return {
            'ecr_repositories': [
                "aws ecr describe-repositories --region us-east-1",
                "aws ecr list-images --repository-name kybershield-rosenpass --region us-east-1",
                "aws ecr list-images --repository-name kybershield-backup --region us-east-1"
            ],
            'ecs_clusters': [
                "aws ecs list-clusters --region us-east-1",
                "aws ecs describe-clusters --clusters kybershield-cluster --region us-east-1",
                "aws ecs list-services --cluster kybershield-cluster --region us-east-1"
            ],
            'service_health': [
                "aws ecs describe-services --cluster kybershield-cluster --services kybershield-rosenpass --region us-east-1",
                "aws ecs describe-services --cluster kybershield-cluster --services kybershield-backup --region us-east-1"
            ],
            'logs': [
                "aws logs describe-log-groups --log-group-name-prefix /ecs/kybershield --region us-east-1",
                "aws logs describe-log-streams --log-group-name /ecs/kybershield-rosenpass --region us-east-1",
                "aws logs get-log-events --log-group-name /ecs/kybershield-backup --log-stream-name <stream-name> --region us-east-1"
            ]
        }

    def check_deployment_urls(self) -> Dict[str, Any]:
        """Check if services are accessible via load balancers"""
        print("🌐 Checking Service Accessibility...")
        
        # Common ECS load balancer patterns
        potential_urls = [
            "https://kybershield-rosenpass.us-east-1.elb.amazonaws.com",
            "https://kybershield-backup.us-east-1.elb.amazonaws.com", 
            "https://kybershield-alb-12345.us-east-1.elb.amazonaws.com",
            "http://kybershield-rosenpass.us-east-1.elb.amazonaws.com",
            "http://kybershield-backup.us-east-1.elb.amazonaws.com"
        ]
        
        accessibility = {}
        
        for url in potential_urls:
            service_name = url.split('//')[1].split('.')[0].replace('kybershield-', '')
            try:
                response = requests.get(f"{url}/health", timeout=10)
                accessibility[service_name] = {
                    'url': url,
                    'status': 'accessible' if response.status_code == 200 else f"http_{response.status_code}",
                    'response_time': response.elapsed.total_seconds()
                }
            except requests.exceptions.Timeout:
                accessibility[service_name] = {'url': url, 'status': 'timeout'}
            except requests.exceptions.ConnectionError:
                accessibility[service_name] = {'url': url, 'status': 'unreachable'}
            except Exception as e:
                accessibility[service_name] = {'url': url, 'status': f'error: {str(e)}'}
                
        return accessibility

    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment monitoring report"""
        print("\n🔍 KyberShield AWS Deployment Monitor")
        print("=" * 50)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'github_actions': self.check_github_actions_status(),
            'service_accessibility': self.check_deployment_urls(),
            'aws_commands': self.get_aws_monitoring_commands(),
            'deployment_health': 'unknown'
        }
        
        # Determine overall deployment health
        github_status = report['github_actions']['deployment_status']
        accessible_services = sum(1 for s in report['service_accessibility'].values() 
                                if s['status'] == 'accessible')
        
        if github_status == 'successful' and accessible_services > 0:
            report['deployment_health'] = 'healthy'
        elif github_status == 'successful':
            report['deployment_health'] = 'deployed_but_not_accessible'
        elif github_status == 'in_progress':
            report['deployment_health'] = 'deploying'
        else:
            report['deployment_health'] = 'deployment_failed'
            
        return report

    def print_deployment_status(self, report: Dict[str, Any]):
        """Print formatted deployment status"""
        print(f"\n📊 DEPLOYMENT STATUS REPORT")
        print("=" * 50)
        
        # GitHub Actions Status
        github = report['github_actions']
        if github.get('latest_run'):
            run = github['latest_run']
            status_emoji = "✅" if run['conclusion'] == 'success' else "❌" if run['conclusion'] == 'failure' else "🔄"
            print(f"🚀 GitHub Actions: {status_emoji} {run['status']} ({run['conclusion']})")
            print(f"   Workflow: {run['workflow_name']}")
            print(f"   Time: {run['created_at']}")
            print(f"   URL: {run['html_url']}")
            
            if github['deployment_status'] == 'successful':
                print(f"   ✅ Services Built: {', '.join(github['services_built'])}")
        else:
            print("🚀 GitHub Actions: ❌ No recent runs found")
        
        # Service Accessibility
        print(f"\n🌐 SERVICE ACCESSIBILITY:")
        accessibility = report['service_accessibility']
        if accessibility:
            for service_name, service_info in accessibility.items():
                status_emoji = "✅" if service_info['status'] == 'accessible' else "❌"
                print(f"   {status_emoji} {service_name}: {service_info['status']}")
                if 'response_time' in service_info:
                    print(f"      Response time: {service_info['response_time']:.2f}s")
        else:
            print("   ⚠️ No accessible endpoints found")
        
        # Overall Health
        health = report['deployment_health']
        health_emoji = "✅" if health == 'healthy' else "🔄" if health == 'deploying' else "❌"
        print(f"\n{health_emoji} OVERALL DEPLOYMENT: {health.replace('_', ' ').upper()}")
        
        # Next Steps
        print(f"\n💡 NEXT STEPS:")
        if health == 'healthy':
            print("   🎉 Your deployment is healthy and accessible!")
            print("   🔐 Run security tests to verify quantum crypto")
            print("   📊 Monitor performance and logs")
        elif health == 'deployed_but_not_accessible':
            print("   ✅ Deployment successful, but services not accessible")
            print("   🔍 Check ECS service configuration")
            print("   🌐 Verify load balancer setup")
            print("   🔓 Check security group rules")
        elif health == 'deploying':
            print("   ⏳ Deployment in progress...")
            print("   🔍 Monitor GitHub Actions for completion")
        else:
            print("   ❌ Deployment failed")
            print("   🔍 Check GitHub Actions logs")
            print("   🛠️ Review build errors")
        
        # AWS Commands to Run
        print(f"\n🛠️ AWS COMMANDS TO CHECK YOUR DEPLOYMENT:")
        commands = report['aws_commands']
        
        print("📦 Check ECR Images:")
        for cmd in commands['ecr_repositories']:
            print(f"   {cmd}")
        
        print("\n☁️ Check ECS Cluster:")
        for cmd in commands['ecs_clusters']:
            print(f"   {cmd}")
        
        print("\n📋 Check Service Health:")
        for cmd in commands['service_health']:
            print(f"   {cmd}")
            
        print(f"\n📅 Report generated: {report['timestamp']}")
        print("=" * 50)

def main():
    """Main monitoring execution"""
    monitor = AWSDeploymentMonitor()
    
    try:
        # Generate deployment report
        report = monitor.generate_deployment_report()
        
        # Print status
        monitor.print_deployment_status(report)
        
        # Save report
        timestamp = int(time.time())
        report_file = f"aws_deployment_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Exit code based on deployment health
        if report['deployment_health'] == 'healthy':
            exit(0)
        elif report['deployment_health'] in ['deployed_but_not_accessible', 'deploying']:
            exit(1)
        else:
            exit(2)
            
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        exit(3)

if __name__ == "__main__":
    main()