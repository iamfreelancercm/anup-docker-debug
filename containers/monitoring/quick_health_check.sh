#!/bin/bash
# Quick health check script for KyberShield AWS deployment

echo "🔍 KyberShield Quick Health Check"
echo "================================"

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "⚠️ AWS CLI not installed, checking local services only"
    LOCAL_ONLY=true
else
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        echo "⚠️ AWS CLI not configured, checking local services only"
        LOCAL_ONLY=true
    else
        echo "✅ AWS CLI configured"
        LOCAL_ONLY=false
    fi
fi

# Check local service ports
echo "🔧 Checking local service ports..."
services=("3001:firewall" "5000:database" "5001:rosenpass" "5002:backup")

for service in "${services[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    
    if netstat -an 2>/dev/null | grep -q ":$port.*LISTEN" || lsof -i :$port 2>/dev/null | grep -q LISTEN; then
        echo "✅ $name service: Port $port is listening"
    else
        echo "❌ $name service: Port $port not listening"
    fi
done

# Check Docker containers if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Checking Docker containers..."
    if docker ps 2>/dev/null | grep -q kybershield; then
        echo "✅ KyberShield containers found:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep kybershield
    else
        echo "⚠️ No KyberShield containers running"
        echo "Available containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "Docker not accessible"
    fi
fi

if [ "$LOCAL_ONLY" = "false" ]; then
    # Check ECS cluster
    CLUSTER_NAME="kybershield-cluster"
    echo "☁️ Checking ECS cluster: $CLUSTER_NAME"

    if aws ecs describe-clusters --clusters "$CLUSTER_NAME" --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
        echo "✅ ECS cluster is ACTIVE"
        
        # Check services
        echo "🔧 Checking ECS services..."
        for service in kybershield-firewall kybershield-database kybershield-rosenpass kybershield-backup; do
            if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$service" --query 'services[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
                running=$(aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$service" --query 'services[0].runningCount' --output text 2>/dev/null)
                desired=$(aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$service" --query 'services[0].desiredCount' --output text 2>/dev/null)
                echo "✅ $service: $running/$desired running"
            else
                echo "❌ $service: Not found or inactive"
            fi
        done
    else
        echo "❌ ECS cluster not found or inactive"
    fi

    # Check ECR repositories
    echo "📦 Checking ECR repositories..."
    for repo in kybershield-firewall kybershield-database kybershield-rosenpass kybershield-backup; do
        if aws ecr describe-repositories --repository-names "$repo" >/dev/null 2>&1; then
            images=$(aws ecr describe-images --repository-name "$repo" --query 'length(imageDetails)' --output text 2>/dev/null)
            echo "✅ $repo: $images images"
        else
            echo "❌ $repo: Repository not found"
        fi
    done
fi

echo "================================"
echo "🔍 Run 'python3 monitoring/aws_health_checker.py' for detailed analysis"
echo "🔴 Run 'python3 monitoring/real_time_dashboard.py' for live monitoring"