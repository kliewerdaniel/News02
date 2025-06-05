#!/usr/bin/env python3
"""
Quick Server Status Checker for News02
Checks if web interface, API server, and job scheduler are running
"""

import requests
import socket
import time
from datetime import datetime

def check_port(host, port, timeout=3):
    """Check if a port is open and responsive"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_web_interface(port=5000):
    """Check web interface status"""
    try:
        response = requests.get(f'http://127.0.0.1:{port}', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_api_server(port=7855):
    """Check API server status"""
    try:
        response = requests.get(f'http://127.0.0.1:{port}/api/remote/stats', timeout=5)
        return response.status_code in [200, 401]  # 401 is expected without API key
    except:
        return False

def check_job_scheduler(web_port=5000):
    """Check job scheduler status via web interface"""
    try:
        response = requests.get(f'http://127.0.0.1:{web_port}/api/job_status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('success', False)
        return False
    except:
        return False

def main():
    print("🔍 News02 Server Status Check")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check ports first
    web_port_open = check_port('127.0.0.1', 5000)
    api_port_open = check_port('127.0.0.1', 7855)
    
    print("📡 Port Status:")
    print(f"   🖥️  Web Interface (5000): {'✅ OPEN' if web_port_open else '❌ CLOSED'}")
    print(f"   🌐 API Server (7855):     {'✅ OPEN' if api_port_open else '❌ CLOSED'}")
    print()
    
    # Check service health
    print("🏥 Service Health:")
    
    if web_port_open:
        web_healthy = check_web_interface()
        print(f"   🖥️  Web Interface:  {'✅ HEALTHY' if web_healthy else '❌ UNHEALTHY'}")
        
        # Check job scheduler (runs with web interface)
        if web_healthy:
            scheduler_healthy = check_job_scheduler()
            print(f"   ⏰ Job Scheduler:   {'✅ HEALTHY' if scheduler_healthy else '❌ UNHEALTHY'}")
        else:
            print(f"   ⏰ Job Scheduler:   ❓ UNKNOWN (web unhealthy)")
    else:
        print(f"   🖥️  Web Interface:  ❌ NOT RUNNING")
        print(f"   ⏰ Job Scheduler:   ❌ NOT RUNNING")
    
    if api_port_open:
        api_healthy = check_api_server()
        print(f"   🌐 API Server:      {'✅ HEALTHY' if api_healthy else '❌ UNHEALTHY'}")
    else:
        print(f"   🌐 API Server:      ❌ NOT RUNNING")
    
    print()
    
    # Overall status
    all_healthy = web_port_open and api_port_open
    if all_healthy:
        print("🎯 Overall Status: ✅ ALL SYSTEMS OPERATIONAL")
        print()
        print("📱 Access URLs:")
        print("   🖥️  Web Dashboard: http://127.0.0.1:5000")
        print("   🌐 API Endpoints: http://127.0.0.1:7855/api/remote/*")
        print("   📋 Jobs Manager:  http://127.0.0.1:5000/jobs")
        print("   🎵 Lounge:        http://127.0.0.1:5000/lounge")
    else:
        print("⚠️  Overall Status: ❌ SOME SERVICES DOWN")
        print()
        print("💡 To start all servers:")
        print("   python start_servers.py --web local --api public --api-port 7855 --web-port 5000")
    
    print()

if __name__ == "__main__":
    main()
