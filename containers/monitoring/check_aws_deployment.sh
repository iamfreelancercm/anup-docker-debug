#!/bin/bash
# KyberShield AWS Deployment Checker
# This script helps you check your actual AWS deployment

set -e

echo "🔍 KyberShield AWS Deployment Checker"
echo "====================================="

# Step 1: Check GitHub Actions Status
echo -e "\n1️⃣ CHECKING GITHUB ACTIONS DEPLOYMENT..."
echo "📋 Go to: https://github.com/Chrisofzo/KyberShield-Firewall/actions"
echo "🔍 Check the latest 'Deploy Rosenpass + Backup to AWS ECR' workflow"
echo ""
read -p "❓ Is the latest GitHub Actions run successful? (y/n): " github_success

if [ "$github_success" = "y" ] || [ "$github_success" = "Y" ]; then
    echo "✅ GitHub Actions deployment successful!"
    
    # Step 2: Configure AWS Credentials  
    echo -e "\n2️⃣ CONFIGURING AWS CREDENTIALS..."
    echo "🔑 You need the same AWS credentials used in GitHub Secrets:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo ""
    
    if aws sts get-caller-identity >/dev/null 2>&1; then
        echo "✅ AWS credentials already configured"
        AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
        echo "📋 AWS Account: $AWS_ACCOUNT"
    else
        echo "⚠️ AWS credentials not configured"
        echo "🛠️ Run: aws configure"
        echo "   Use the same credentials from your GitHub repository secrets"
        exit 1
    fi
    
    # Step 3: Check ECR Repositories
    echo -e "\n3️⃣ CHECKING ECR REPOSITORIES..."
    
    for repo in kybershield-rosenpass kybershield-backup; do
        if aws ecr describe-repositories --repository-names $repo --region us-east-1 >/dev/null 2>&1; then
            image_count=$(aws ecr list-images --repository-name $repo --region us-east-1 --query 'length(imageIds)' --output text)
            echo "✅ $repo: $image_count images"
            
            # Get latest image
            if [ $image_count -gt 0 ]; then
                latest_image=$(aws ecr describe-images --repository-name $repo --region us-east-1 --query 'sort_by(imageDetails,&imagePushedAt)[-1]' --output json)
                pushed_at=$(echo $latest_image | jq -r '.imagePushedAt')
                size_mb=$(echo $latest_image | jq -r '.imageSizeInBytes / 1024 / 1024 | round')
                echo "   📅 Latest push: $pushed_at"
                echo "   📦 Size: ${size_mb}MB"
            fi
        else
            echo "❌ $repo: Repository not found"
        fi
    done
    
    # Step 4: Check ECS Cluster (if exists)
    echo -e "\n4️⃣ CHECKING ECS DEPLOYMENT..."
    
    if aws ecs describe-clusters --clusters kybershield-cluster --region us-east-1 >/dev/null 2>&1; then
        echo "✅ ECS Cluster 'kybershield-cluster' exists"
        
        # Check services
        services=$(aws ecs list-services --cluster kybershield-cluster --region us-east-1 --query 'serviceArns' --output text)
        if [ -n "$services" ]; then
            echo "🔧 Services in cluster:"
            for service_arn in $services; do
                service_name=$(basename $service_arn)
                service_info=$(aws ecs describe-services --cluster kybershield-cluster --services $service_name --region us-east-1 --query 'services[0]' --output json)
                running=$(echo $service_info | jq -r '.runningCount')
                desired=$(echo $service_info | jq -r '.desiredCount')
                status=$(echo $service_info | jq -r '.status')
                echo "   📋 $service_name: $running/$desired running ($status)"
            done
        else
            echo "⚠️ No services found in cluster"
        fi
    else
        echo "⚠️ ECS Cluster not found"
        echo "💡 Your images are in ECR but no ECS cluster deployed"
        echo "🛠️ You may need to:"
        echo "   - Deploy ECS services manually"
        echo "   - Use docker run with ECR images"
        echo "   - Set up ECS Fargate tasks"
    fi
    
    # Step 5: Service URLs (if load balancers exist)
    echo -e "\n5️⃣ CHECKING SERVICE ACCESSIBILITY..."
    
    # Try to find load balancers
    load_balancers=$(aws elbv2 describe-load-balancers --region us-east-1 --query 'LoadBalancers[?starts_with(LoadBalancerName,`kybershield`)]' --output text 2>/dev/null || echo "")
    
    if [ -n "$load_balancers" ]; then
        echo "✅ Found KyberShield load balancers"
        echo "$load_balancers"
    else
        echo "⚠️ No load balancers found"
        echo "💡 Services may not be publicly accessible"
    fi
    
    # Step 6: Recommendations
    echo -e "\n6️⃣ RECOMMENDATIONS..."
    
    echo "📦 Your container images are successfully built and stored in ECR!"
    echo "🎯 Next steps to make them accessible:"
    echo "   1. Create ECS Cluster: aws ecs create-cluster --cluster-name kybershield-cluster"
    echo "   2. Create ECS Task Definitions for each service"
    echo "   3. Create ECS Services with load balancers"
    echo "   4. Configure security groups for port access"
    echo ""
    echo "🚀 Quick test with Docker:"
    echo "   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com"
    echo "   docker run -p 5001:5001 $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/kybershield-rosenpass:latest"
    
else
    echo "❌ GitHub Actions deployment failed"
    echo "🔍 Check GitHub Actions logs at:"
    echo "   https://github.com/Chrisofzo/KyberShield-Firewall/actions"
    echo ""
    echo "🛠️ Common issues:"
    echo "   - Docker build errors"
    echo "   - AWS credential problems"  
    echo "   - ECR permission issues"
    echo "   - Missing repository"
fi

echo -e "\n✅ Deployment check complete!"
echo "📊 Run this script again after fixing any issues"