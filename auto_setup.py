#!/usr/bin/env python3
"""
News02 Automatic Setup Script
Creates virtual environment, installs dependencies, and sets up the project
"""

import os
import sys
import subprocess
import platform
import venv
import shutil
from pathlib import Path
import time

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_step(step_num, total_steps, description):
    """Print step progress"""
    print(f"{Colors.OKCYAN}[{step_num}/{total_steps}] {description}{Colors.ENDC}")

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, 9, "Checking Python version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_virtual_environment():
    """Create virtual environment"""
    print_step(2, 9, "Creating virtual environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        response = input("Do you want to recreate it? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print_info("Removing existing virtual environment...")
            shutil.rmtree(venv_path)
        else:
            print_info("Using existing virtual environment")
            return True
    
    try:
        print_info("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        print_success("Virtual environment created successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get path to virtual environment Python executable"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def get_venv_pip():
    """Get path to virtual environment pip executable"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "pip.exe"
    else:
        return Path("venv") / "bin" / "pip"

def upgrade_pip():
    """Upgrade pip in virtual environment"""
    print_step(3, 9, "Upgrading pip")
    
    pip_path = get_venv_pip()
    python_path = get_venv_python()
    
    try:
        subprocess.run([
            str(python_path), "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, capture_output=True, text=True)
        print_success("Pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to upgrade pip: {e}")
        return False

def install_dependencies():
    """Install project dependencies"""
    print_step(4, 9, "Installing dependencies")
    
    python_path = get_venv_python()
    
    if not Path("requirements.txt").exists():
        print_error("requirements.txt not found")
        return False
    
    try:
        print_info("Installing packages (this may take several minutes)...")
        print_info("This will install web interface, RSS processing, and TTS components...")
        
        # First, try installing with normal output
        result = subprocess.run([
            str(python_path), "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("All dependencies installed successfully")
            return True
        else:
            print_warning("Full requirements installation failed")
            print_info("Trying minimal requirements for web interface only...")
            
            # Try minimal requirements
            if Path("requirements_minimal.txt").exists():
                result_minimal = subprocess.run([
                    str(python_path), "-m", "pip", "install", "-r", "requirements_minimal.txt"
                ], capture_output=True, text=True)
                
                if result_minimal.returncode == 0:
                    print_success("Minimal dependencies installed successfully")
                    print_info("Web interface will work with basic functionality")
                    print_warning("Some features may be limited until you install additional packages")
                    return True
            
            # If minimal also fails, try core packages individually
            print_info("Trying to install core packages individually...")
            core_packages = [
                "flask>=2.3.0",
                "werkzeug>=2.3.0",
                "jinja2>=3.1.0",
                "feedparser>=6.0.0",
                "pyyaml>=6.0",
                "python-dotenv>=1.0.0",
                "requests>=2.28.0"
            ]
            
            success_count = 0
            for package in core_packages:
                try:
                    subprocess.run([
                        str(python_path), "-m", "pip", "install", package
                    ], check=True, capture_output=True, text=True)
                    print_info(f"✓ {package}")
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    print_warning(f"✗ {package}")
            
            if success_count >= 5:  # At least Flask + core deps
                print_success(f"Installed {success_count}/{len(core_packages)} core packages")
                print_warning("Some packages failed, but web interface should work")
                return True
            else:
                print_error("Too many core packages failed to install")
                print_error("Error details from main installation:")
                if result.stderr:
                    error_lines = result.stderr.split('\n')[:15]
                    for line in error_lines:
                        if line.strip():
                            print(f"  {line.strip()}")
                return False
            
    except Exception as e:
        print_error(f"Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print_step(5, 9, "Creating directories")
    
    directories = ["logs", "output", "settings/llm_settings"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_info(f"Created directory: {directory}")
    
    print_success("All directories created")
    return True

def setup_configuration():
    """Setup configuration files"""
    print_step(7, 9, "Setting up configuration")
    
    config_files = {
        ".env": "Environment variables",
        "settings/llm_settings/ai_models.yml": "Model configurations", 
        "settings/feeds/feeds.yaml": "RSS feeds"
    }
    
    missing_files = []
    for config_file, description in config_files.items():
        if Path(config_file).exists():
            print_info(f"Found: {description}")
        else:
            missing_files.append((config_file, description))
    
    if missing_files:
        print_warning(f"Missing configuration files: {len(missing_files)}")
        for file, desc in missing_files:
            print_warning(f"  - {file} ({desc})")
        print_info("These will be created with default values")
    else:
        print_success("All configuration files found")
    
    return True

def clone_feed_discovery_repo():
    """Clone the awesome-rss-feeds repository for feed discovery"""
    print_step(6, 9, "Setting up feed discovery database")
    
    repo_url = "https://github.com/plenaryapp/awesome-rss-feeds.git"
    repo_dir = Path("awesome-rss-feeds")
    
    if repo_dir.exists():
        print_info("Feed discovery database already exists")
        
        # Check if it's a git repository and try to update
        if (repo_dir / ".git").exists():
            try:
                print_info("Updating feed database...")
                subprocess.run(["git", "pull"], cwd=repo_dir, check=True, capture_output=True)
                print_success("Feed database updated successfully")
            except subprocess.CalledProcessError:
                print_warning("Failed to update feed database, using existing version")
        
        print_success(f"Feed discovery available with 300+ RSS feeds")
        return True
    
    # Check if git is available
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("Git not found - feed discovery database will not be available")
        print_info("You can still use News02 with manual RSS feed management")
        return True  # Not a failure, just a missing feature
    
    try:
        print_info("Cloning feed discovery database (awesome-rss-feeds)...")
        subprocess.run([
            "git", "clone", repo_url, str(repo_dir)
        ], check=True, capture_output=True)
        print_success("Feed discovery database cloned successfully")
        print_success("📊 Access to 300+ curated RSS feeds enabled")
        return True
    except subprocess.CalledProcessError as e:
        print_warning("Failed to clone feed discovery database")
        print_info("You can still use News02 with manual RSS feed management")
        return True  # Not a failure, just a missing feature

def test_installation():
    """Test the installation"""
    print_step(8, 9, "Testing installation")
    
    python_path = get_venv_python()
    
    # Test core imports first
    core_imports = [
        ("flask", "Web framework"),
        ("yaml", "YAML processing"),
        ("feedparser", "RSS feed parsing"),
        ("requests", "HTTP client"),
        ("dotenv", "Environment variables"),
    ]
    
    # Optional imports
    optional_imports = [
        ("edge_tts", "Text-to-speech"),
        ("openai", "OpenAI API"),
        ("ollama", "Ollama client"),
        ("google.generativeai", "Google Gemini"),
    ]
    
    core_failed = []
    optional_failed = []
    
    # Test core imports
    for module, description in core_imports:
        try:
            result = subprocess.run([
                str(python_path), "-c", f"import {module}; print(f'{module} OK')"
            ], capture_output=True, text=True, check=True)
            print_info(f"{description}: ✓")
        except subprocess.CalledProcessError:
            core_failed.append((module, description))
            print_error(f"{description}: ✗")
    
    # Test optional imports
    for module, description in optional_imports:
        try:
            result = subprocess.run([
                str(python_path), "-c", f"import {module}; print(f'{module} OK')"
            ], capture_output=True, text=True, check=True)
            print_info(f"{description}: ✓")
        except subprocess.CalledProcessError:
            optional_failed.append((module, description))
            print_warning(f"{description}: ✗ (optional)")
    
    if core_failed:
        print_error(f"Failed to import {len(core_failed)} core modules")
        print_error("These are required for basic functionality:")
        for module, desc in core_failed:
            print_error(f"  - {desc} ({module})")
        return False
    else:
        print_success("All core modules imported successfully")
        if optional_failed:
            print_warning(f"{len(optional_failed)} optional modules failed to import")
            print_warning("Web interface will work, but some features may be limited")
        return True

def show_completion_instructions():
    """Show completion instructions"""
    print_step(9, 9, "Setup complete!")
    
    # Determine activation command based on OS
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        python_cmd = "python"
    else:
        activate_cmd = "source venv/bin/activate"
        python_cmd = "python"
    
    print_success("News02 setup completed successfully!")
    
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}🚀 How to run the Web GUI:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}1. Activate virtual environment:{Colors.ENDC}")
    print(f"   {activate_cmd}")
    
    print(f"\n{Colors.OKCYAN}2. Start the web interface:{Colors.ENDC}")
    print(f"   {python_cmd} run_web.py")
    
    print(f"\n{Colors.OKCYAN}3. Open your browser to:{Colors.ENDC}")
    print(f"   http://127.0.0.1:5000")
    
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}📋 Alternative commands:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• Test configuration: {python_cmd} news_cli.py test-all{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• Command line version: {python_cmd} news_digest_enhanced.py{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• View help: {python_cmd} news_cli.py --help{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.WARNING}📝 Next steps:{Colors.ENDC}")
    print(f"{Colors.WARNING}1. Configure your LLM provider in the web interface Settings tab{Colors.ENDC}")
    print(f"{Colors.WARNING}2. Add your RSS feeds in the Feeds tab (or discover 300+ feeds!){Colors.ENDC}")
    print(f"{Colors.WARNING}3. Generate your first news digest!{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}🆕 Feed Discovery Features:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Browse 300+ curated RSS feeds by category{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Search feeds by topic or keyword{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Filter to English-only sources{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• One-click add to your feed list{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}🔧 If you have issues:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• Install missing packages: {python_cmd} -m pip install package-name{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• Try minimal install: {python_cmd} -m pip install -r requirements_minimal.txt{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• Check logs in the terminal where you run run_web.py{Colors.ENDC}")
    print(f"{Colors.OKBLUE}• See README_SETUP.md for detailed troubleshooting{Colors.ENDC}")

def create_activation_script():
    """Create convenient activation scripts"""
    print_info("Creating activation scripts...")
    
    if platform.system() == "Windows":
        # Windows batch file
        batch_content = """@echo off
echo Activating News02 virtual environment...
call venv\\Scripts\\activate.bat
echo.
echo News02 environment activated!
echo Run: python run_web.py
echo.
cmd /k
"""
        with open("activate_news02.bat", "w") as f:
            f.write(batch_content)
        print_info("Created activate_news02.bat")
    else:
        # Unix shell script
        script_content = """#!/bin/bash
echo "Activating News02 virtual environment..."
source venv/bin/activate
echo ""
echo "News02 environment activated!"
echo "Run: python run_web.py"
echo ""
exec "$SHELL"
"""
        with open("activate_news02.sh", "w") as f:
            f.write(script_content)
        os.chmod("activate_news02.sh", 0o755)
        print_info("Created activate_news02.sh")

def main():
    """Main setup function"""
    print_header("News02 Automatic Setup")
    print_info("This script will set up News02 with a virtual environment")
    print_info("and install all required dependencies.")
    
    # Confirmation
    response = input(f"\n{Colors.BOLD}Continue with setup? (y/n): {Colors.ENDC}").lower().strip()
    if response not in ['y', 'yes']:
        print_info("Setup cancelled.")
        return
    
    start_time = time.time()
    
    # Run setup steps
    steps = [
        check_python_version,
        create_virtual_environment,
        upgrade_pip,
        install_dependencies,
        create_directories,
        clone_feed_discovery_repo,
        setup_configuration,
        test_installation,
    ]
    
    for step in steps:
        if not step():
            print_error("Setup failed. Please check the errors above.")
            sys.exit(1)
        time.sleep(0.5)  # Brief pause between steps
    
    # Create convenience scripts
    create_activation_script()
    
    # Show completion
    show_completion_instructions()
    
    elapsed_time = time.time() - start_time
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}Setup completed in {elapsed_time:.1f} seconds!{Colors.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)