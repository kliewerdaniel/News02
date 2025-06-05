#!/usr/bin/env python3
"""
News02 Flexible Server Launcher
Configurable web interface and API server with command-line options
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

def start_web_server(host='127.0.0.1', port=5000):
    """Start the web interface server"""
    print(f"🖥️  Starting Web Interface Server on {host}:{port}...")
    
    # Set environment variables for the web server
    env = os.environ.copy()
    env['WEB_HOST'] = host
    env['WEB_PORT'] = str(port)
    
    return subprocess.Popen([
        sys.executable, '-c', f'''
import sys
import os
sys.path.insert(0, os.getcwd())

# Import from functions folder
from functions.web_server import app

# Override the run configuration
app.run(host="{host}", port={port}, debug=True)
'''
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def start_api_server(host='0.0.0.0', port=7855):
    """Start the API server"""
    print(f"🌐 Starting API Server on {host}:{port}...")
    
    # Set environment variables for the API server
    env = os.environ.copy()
    env['API_HOST'] = host
    env['API_PORT'] = str(port)
    
    return subprocess.Popen([
        sys.executable, '-c', f'''
import sys
import os
sys.path.insert(0, os.getcwd())

# Import from functions folder
from functions.api_server import api_app

api_app.run(host="{host}", port={port}, debug=False)
'''
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def start_job_scheduler():
    """Start the job scheduler"""
    print("⏰ Starting Job Scheduler...")
    
    return subprocess.Popen([
        sys.executable, '-c', '''
import sys
import os
sys.path.insert(0, os.getcwd())

# Import and start job scheduler
from functions.job_scheduler import job_scheduler

print("🚀 Job scheduler starting...")
job_scheduler.start_scheduler()
print("✅ Job scheduler running")

# Keep the process alive
import time
try:
    while True:
        time.sleep(30)  # Check every 30 seconds
        if not job_scheduler.running:
            print("❌ Job scheduler stopped unexpectedly")
            break
except KeyboardInterrupt:
    print("🛑 Job scheduler shutting down...")
    job_scheduler.stop_scheduler()
    print("✅ Job scheduler stopped")
'''
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='News02 Flexible Server Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                                    # Default: web=localhost:5000, api=0.0.0.0:7855
  %(prog)s --web local --api public           # Explicit local/public
  %(prog)s --web-host 0.0.0.0 --web-port 8000 # Custom web config
  %(prog)s --api-only --api-port 9000         # API server only
  %(prog)s --web-only --web-host 192.168.1.100 # Web server only
  %(prog)s --web public --api local           # Reverse configuration
        '''
    )
    
    # Server selection
    parser.add_argument('--web-only', action='store_true',
                       help='Start only the web interface server')
    parser.add_argument('--api-only', action='store_true',
                       help='Start only the API server')
    parser.add_argument('--no-scheduler', action='store_true',
                       help='Skip starting the job scheduler')
    
    # Web server configuration
    parser.add_argument('--web', choices=['local', 'public'], default='local',
                       help='Web interface access: local (127.0.0.1) or public (0.0.0.0)')
    parser.add_argument('--web-host', type=str,
                       help='Custom web server host (overrides --web)')
    parser.add_argument('--web-port', type=int, default=5000,
                       help='Web server port (default: 5000)')
    
    # API server configuration
    parser.add_argument('--api', choices=['local', 'public'], default='public',
                       help='API server access: local (127.0.0.1) or public (0.0.0.0)')
    parser.add_argument('--api-host', type=str,
                       help='Custom API server host (overrides --api)')
    parser.add_argument('--api-port', type=int, default=7855,
                       help='API server port (default: 7855)')
    
    # Other options
    parser.add_argument('--no-startup-delay', action='store_true',
                       help='Skip startup delay between servers')
    
    return parser.parse_args()

def resolve_host(access_type, custom_host=None):
    """Resolve host based on access type or custom host"""
    if custom_host:
        return custom_host
    return '127.0.0.1' if access_type == 'local' else '0.0.0.0'

def main():
    args = parse_arguments()
    
    print("🚀 News02 Flexible Server Launcher")
    print("=" * 50)
    
    # Resolve hosts
    web_host = resolve_host(args.web, args.web_host)
    api_host = resolve_host(args.api, args.api_host)
    
    # Show configuration
    print("⚙️  Configuration:")
    if not args.api_only:
        access_type = "public" if web_host == "0.0.0.0" else "local"
        print(f"   🖥️  Web Interface: {web_host}:{args.web_port} ({access_type})")
    if not args.web_only:
        access_type = "public" if api_host == "0.0.0.0" else "local"
        print(f"   🌐 API Server: {api_host}:{args.api_port} ({access_type})")
    print()
    
    web_process = None
    api_process = None
    scheduler_process = None
    
    try:
        # Start job scheduler (unless disabled)
        if not args.no_scheduler:
            scheduler_process = start_job_scheduler()
            if not args.no_startup_delay:
                time.sleep(2)  # Give it time to start
            
            # Check if scheduler started successfully
            if scheduler_process.poll() is not None:
                print("❌ Job scheduler failed to start")
                return 1
            
            print("✅ Job Scheduler: Running")
        
        # Start web server
        if not args.api_only:
            web_process = start_web_server(web_host, args.web_port)
            if not args.no_startup_delay:
                time.sleep(2)  # Give it time to start
            
            # Check if web server started successfully
            if web_process.poll() is not None:
                print("❌ Web server failed to start")
                return 1
            
            web_url = f"http://{web_host if web_host != '0.0.0.0' else 'localhost'}:{args.web_port}"
            print(f"✅ Web Interface: {web_url}")
        
        # Start API server
        if not args.web_only:
            api_process = start_api_server(api_host, args.api_port)
            if not args.no_startup_delay:
                time.sleep(2)  # Give it time to start
            
            # Check if API server started successfully
            if api_process.poll() is not None:
                print("❌ API server failed to start")
                return 1
            
            api_url = f"http://{api_host if api_host != '0.0.0.0' else 'YOUR_IP'}:{args.api_port}"
            print(f"✅ API Server: {api_url}")
        
        # Show status summary
        print("\n🎯 Server Status:")
        if not args.no_scheduler:
            print(f"   ⏰ Job Scheduler: Running (scheduled jobs will execute automatically)")
        
        if not args.api_only:
            web_access = "localhost only" if web_host == "127.0.0.1" else "public access"
            print(f"   📱 Web Dashboard: http://{web_host}:{args.web_port} ({web_access})")
        
        if not args.web_only:
            api_access = "localhost only" if api_host == "127.0.0.1" else "external access"
            print(f"   🌐 API Endpoints: http://{api_host}:{args.api_port}/api/remote/* ({api_access})")
            print(f"   🔑 API Key: {os.getenv('REMOTE_DIGEST_API_KEY', 'Not configured')}")
        
        print("\n💡 Press Ctrl+C to stop all servers")
        
        # Wait for user interrupt
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if scheduler_process and scheduler_process.poll() is not None:
                print("❌ Job scheduler stopped unexpectedly")
                break
                
            if web_process and web_process.poll() is not None:
                print("❌ Web server stopped unexpectedly")
                break
                
            if api_process and api_process.poll() is not None:
                print("❌ API server stopped unexpectedly")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean shutdown
        if scheduler_process:
            scheduler_process.terminate()
            try:
                scheduler_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                scheduler_process.kill()
        
        if web_process:
            web_process.terminate()
            try:
                web_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                web_process.kill()
        
        if api_process:
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
        
        print("✅ All servers stopped")
        return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)