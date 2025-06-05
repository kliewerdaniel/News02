# 🚀 News02 Server Commands

## 📋 **Flexible Server Launcher**

### **Basic Commands**

```bash
# Default: Web=localhost:5000, API=public:7855
python start_servers.py

# Show help and all options
python start_servers.py --help
```

### **Your Requested Format**

```bash
# Exactly what you asked for!
python start_servers.py --web local --api public --api-port 7855 --web-port 5000

# Alternative formats
python start_servers.py --web local --api public
python start_servers.py --web-host 127.0.0.1 --api-host 0.0.0.0 --api-port 7855
```

### **Common Scenarios**

#### **Development Setup**
```bash
# Web interface only (localhost)
python start_servers.py --web-only

# Both servers on localhost (secure development)
python start_servers.py --web local --api local
```

#### **Testing External API**
```bash
# Web local, API external (your use case)
python start_servers.py --web local --api public --api-port 7855

# API only for external testing
python start_servers.py --api-only --api-port 7855
```

#### **Public Demo**
```bash
# Both servers public (demo/presentation)
python start_servers.py --web public --api public

# Custom ports for both
python start_servers.py --web public --web-port 8080 --api public --api-port 9000
```

#### **Custom Network Setup**
```bash
# Specific IP addresses
python start_servers.py --web-host 192.168.1.100 --api-host 0.0.0.0

# Different ports
python start_servers.py --web-port 3000 --api-port 8855
```

### **Quick Reference**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--web` | `local`/`public` | `local` | Web interface access |
| `--api` | `local`/`public` | `public` | API server access |
| `--web-host` | IP address | - | Custom web host |
| `--api-host` | IP address | - | Custom API host |
| `--web-port` | Port number | `5000` | Web interface port |
| `--api-port` | Port number | `7855` | API server port |
| `--web-only` | Flag | - | Start only web server |
| `--api-only` | Flag | - | Start only API server |

### **What Each Setting Does**

- **`--web local`**: Web interface only accessible from localhost (127.0.0.1)
- **`--web public`**: Web interface accessible from any IP (0.0.0.0)
- **`--api local`**: API only accessible from localhost (127.0.0.1)
- **`--api public`**: API accessible from external IPs (0.0.0.0)

### **Testing Commands**

```bash
# Test API access after starting servers
python test_api_external.py

# Individual server testing (now in functions folder)
python -c "from functions.web_server import app; app.run(host='127.0.0.1', port=5000, debug=True)"
python -c "from functions.api_server import api_app; api_app.run(host='0.0.0.0', port=7855)"

# Or use the new flexible launcher
python start_servers.py --web-only    # Web only
python start_servers.py --api-only    # API only
```

### **Perfect for Your Setup**

Your ideal command for proxy testing:
```bash
python start_servers.py --web local --api public --api-port 7855 --web-port 5000
```

This gives you:
- 🖥️ **Web Interface**: `localhost:5000` (development access)
- 🌐 **API Server**: `0.0.0.0:7855` (external proxy access)