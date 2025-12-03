# Container Build Troubleshooting Guide

## Quick Start for Docker Specialists

Run this first:
```bash
./run-diagnostics.sh
```

This will test each container build and generate detailed error logs.

## Common Container Build Issues & Solutions

### 1. liboqs Quantum Library Issues

**Symptoms**: Build fails during liboqs installation
```
fatal error: 'oqs/oqs.h' file not found
```

**Solutions**:
- Check liboqs version compatibility (currently targeting 0.11.0)
- Verify cmake and build dependencies are installed
- Consider using pre-built liboqs packages

**Known Working Configuration**:
```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch 0.11.0 https://github.com/open-quantum-safe/liboqs.git \
    && cd liboqs \
    && mkdir build && cd build \
    && cmake -GNinja .. \
    && ninja \
    && ninja install
```

### 2. Python Dependencies Conflicts

**Symptoms**: Pip install fails with dependency resolution errors
```
ERROR: Cannot install package due to conflicting dependencies
```

**Solutions**:
- Use pip --no-deps for problematic packages
- Pin specific versions in requirements.txt
- Use virtual environment isolation
- Consider poetry or pipenv for better dependency management

### 3. Multi-Stage Build Issues

**Symptoms**: Files missing in final stage, or build context problems
```
COPY failed: no such file or directory
```

**Solutions**:
- Verify COPY paths between stages
- Check --from=builder stage references
- Ensure build context includes all needed files
- Use .dockerignore to exclude unnecessary files

### 4. Architecture Compatibility

**Symptoms**: Binary incompatibility or missing packages for ARM64/AMD64
```
exec format error
```

**Solutions**:
- Add platform specification: `FROM --platform=linux/amd64 python:3.11-slim`
- Use multi-arch builds if needed
- Check if quantum crypto libraries support target architecture

## Container-Specific Known Issues

### Database Container
- **Primary Issue**: Complex quantum crypto dependencies
- **Focus Area**: ML-DSA-87 signature implementation
- **Common Fix**: Ensure liboqs Python bindings install correctly

### Firewall Container  
- **Primary Issue**: Network packet filtering libraries
- **Focus Area**: iptables/netfilter integration
- **Common Fix**: Add required system packages for networking

### Backup Service
- **Primary Issue**: ChaCha20-Poly1305 encryption dependencies
- **Focus Area**: Cryptographic library compatibility
- **Common Fix**: Ensure openssl and crypto libraries are available

### Rosenpass Container
- **Primary Issue**: ML-KEM-768 VPN integration
- **Focus Area**: WireGuard and quantum crypto integration
- **Common Fix**: Network namespacing and VPN dependencies

### Monitoring Container
- **Primary Issue**: Metrics collection dependencies
- **Focus Area**: Prometheus/monitoring stack integration
- **Common Fix**: System metrics access permissions

### Client API Container
- **Primary Issue**: Flask/FastAPI with quantum crypto
- **Focus Area**: Web server with quantum security
- **Common Fix**: WSGI/ASGI server configuration

## Build Optimization Strategies

### 1. Layer Caching
```dockerfile
# Install system packages first (changes rarely)
RUN apt-get update && apt-get install -y [packages]

# Install Python dependencies next (changes occasionally)  
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code last (changes frequently)
COPY . .
```

### 2. Dependency Pinning
Pin all versions to ensure reproducible builds:
```
liboqs==0.11.0
cryptography==41.0.7
flask==3.0.0
```

### 3. Build Size Reduction
```dockerfile
# Use multi-stage builds
FROM python:3.11-slim as builder
# Build dependencies here

FROM python:3.11-slim as runtime
# Copy only runtime artifacts
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
```

## Testing Strategy

1. **Individual Container Tests**: Build each container separately
2. **Dependency Verification**: Check quantum crypto libraries work
3. **Integration Test**: Full docker-compose stack
4. **Smoke Test**: Basic functionality verification

## Emergency Fallback Options

If builds continue failing:

1. **Simplify Dockerfiles**: Remove complex multi-stage builds temporarily
2. **Use Different Base Images**: Try ubuntu:22.04 instead of python:3.11-slim
3. **Pre-built Quantum Libraries**: Use conda or pre-compiled binaries
4. **Container Registry**: Pull working images from backup registry

## Success Validation

Once fixed, verify:
- [ ] All 6 containers build without errors
- [ ] docker-compose up works end-to-end  
- [ ] Quantum crypto functions are available
- [ ] No regression in functionality
- [ ] Builds are deterministic (same result on rebuild)

---

**Note**: The quantum cryptography integration is the most complex part. If needed, temporarily disable quantum features to get basic containers working, then re-add incrementally.