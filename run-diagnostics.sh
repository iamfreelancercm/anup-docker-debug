#!/bin/bash

echo "=== KyberShield Container Build Diagnostics ==="
echo "Running comprehensive build diagnostics..."
echo

# Check Docker installation
echo "1. Docker Version Check:"
docker --version
echo

# Check available space
echo "2. Disk Space Check:"
df -h
echo

# Test base image pull
echo "3. Base Image Test:"
docker pull python:3.11-slim
echo

# Check each container directory
echo "4. Container Structure Verification:"
for container in database firewall backup-service rosenpass monitoring client-api; do
    echo "  Checking $container..."
    if [ -d "containers/$container" ]; then
        echo "    ✓ Directory exists"
        if [ -f "containers/$container/Dockerfile" ]; then
            echo "    ✓ Dockerfile found"
        else
            echo "    ✗ Dockerfile missing"
        fi
        if [ -f "containers/$container/requirements.txt" ]; then
            echo "    ✓ Requirements.txt found"
            echo "    📋 Dependencies:"
            head -5 "containers/$container/requirements.txt" | sed 's/^/        /'
        else
            echo "    ✗ Requirements.txt missing"
        fi
    else
        echo "    ✗ Directory missing"
    fi
    echo
done

# Test individual builds with verbose output
echo "5. Individual Build Tests (verbose):"
for container in database firewall backup-service rosenpass monitoring client-api; do
    if [ -d "containers/$container" ]; then
        echo "  Building $container..."
        cd "containers/$container"
        
        # Attempt build with no cache to see real errors
        docker build --no-cache --progress=plain -t "test-$container" . > "../../build-log-$container.txt" 2>&1
        
        if [ $? -eq 0 ]; then
            echo "    ✅ $container built successfully"
        else
            echo "    ❌ $container failed to build"
            echo "    📄 Error log saved to build-log-$container.txt"
            echo "    🔍 Last 10 lines of error:"
            tail -10 "../../build-log-$container.txt" | sed 's/^/        /'
        fi
        
        cd ../..
        echo
    fi
done

# Test docker-compose
echo "6. Docker Compose Test:"
if [ -f "docker-compose.yml" ]; then
    echo "  Testing docker-compose build..."
    docker-compose build > compose-build.log 2>&1
    if [ $? -eq 0 ]; then
        echo "    ✅ Docker Compose build successful"
    else
        echo "    ❌ Docker Compose build failed"
        echo "    📄 Error log saved to compose-build.log"
        echo "    🔍 Last 10 lines of error:"
        tail -10 compose-build.log | sed 's/^/        /'
    fi
else
    echo "    ✗ docker-compose.yml not found"
fi

echo
echo "=== Diagnostic Complete ==="
echo "Check build-log-*.txt files for detailed error analysis"
echo "Focus on the first failing step in each container build"