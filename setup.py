#!/usr/bin/env python3
"""
Setup script for News02 Enhanced
Helps users configure the system for first use
"""

import os
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "output", "settings/llm_settings"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def check_ollama():
    """Check if Ollama is available"""
    try:
        subprocess.check_call(["ollama", "list"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Ollama is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Ollama not found or not running")
        print("   Install from: https://ollama.com")
        return False

def check_config_files():
    """Check if configuration files exist"""
    config_files = [
        ".env",
        "settings/llm_settings/ai_models.yml",
        "settings/feeds/feeds.yaml"
    ]
    
    all_exist = True
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ Found: {config_file}")
        else:
            print(f"❌ Missing: {config_file}")
            all_exist = False
    
    return all_exist

def setup_ollama_models():
    """Setup default Ollama models"""
    models = ["mistral:latest", "mistral-small:24b-instruct-2501-q8_0"]
    
    if not check_ollama():
        return False
    
    print("\n🤖 Setting up Ollama models...")
    for model in models:
        try:
            print(f"Pulling {model}...")
            subprocess.check_call(["ollama", "pull", model])
            print(f"✅ {model} ready")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to pull {model}")
            return False
    
    return True

def clone_feed_discovery_repo():
    """Clone the awesome-rss-feeds repository for feed discovery"""
    repo_url = "https://github.com/plenaryapp/awesome-rss-feeds.git"
    repo_dir = "awesome-rss-feeds"
    
    print(f"\n📡 Setting up feed discovery database...")
    
    if Path(repo_dir).exists():
        print(f"✅ Feed discovery database already exists")
        
        # Ask if they want to update it
        update = input("Do you want to update the feed database? (y/n): ").lower().strip()
        if update in ['y', 'yes']:
            try:
                print("🔄 Updating feed database...")
                subprocess.check_call(["git", "pull"], cwd=repo_dir)
                print("✅ Feed database updated successfully")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Failed to update feed database: {e}")
                print("   Continuing with existing database...")
        return True
    
    # Check if git is available
    try:
        subprocess.check_call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git not found. Please install Git to enable feed discovery.")
        print("   You can still use News02 without feed discovery.")
        return False
    
    try:
        print(f"📥 Cloning feed discovery database...")
        subprocess.check_call(["git", "clone", repo_url, repo_dir])
        print("✅ Feed discovery database cloned successfully")
        print(f"   📊 This provides access to 300+ curated RSS feeds")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone feed discovery database: {e}")
        print("   You can still use News02 without feed discovery.")
        return False

def main():
    """Main setup function"""
    print("🚀 News02 Enhanced Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Check configuration files
    print("\n⚙️  Checking configuration files...")
    if not check_config_files():
        print("\n⚠️  Some configuration files are missing.")
        print("Please ensure you have:")
        print("- .env (environment variables)")
        print("- settings/llm_settings/ai_models.yml (model configurations)")
        print("- settings/feeds/feeds.yaml (RSS feed URLs)")
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Clone feed discovery repository
    clone_feed_discovery_repo()
    
    # Setup Ollama (optional)
    print("\n🤖 Checking Ollama setup...")
    ollama_setup = input("Do you want to setup Ollama models? (y/n): ").lower().strip()
    if ollama_setup in ['y', 'yes']:
        setup_ollama_models()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Configure your .env file with appropriate settings")
    print("2. Update settings/feeds/feeds.yaml with your preferred RSS feeds")
    print("3. Run: python news_digest_enhanced.py")
    print("\nFor more information, see flow.md")

if __name__ == "__main__":
    main()
