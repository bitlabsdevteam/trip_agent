#!/usr/bin/env python3
"""
Test script to verify Docker setup and configuration.
This script checks if all Docker files are properly configured.
"""

import os
import sys
import yaml
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and return status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} missing: {file_path}")
        return False

def check_dockerfile(dockerfile_path, service_name):
    """Check Dockerfile configuration."""
    print(f"\n📋 Checking {service_name} Dockerfile...")
    
    if not check_file_exists(dockerfile_path, f"{service_name} Dockerfile"):
        return False
    
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for required elements
        checks = {
            'FROM': 'Base image specified',
            'WORKDIR': 'Working directory set',
            'COPY': 'Files copied',
            'EXPOSE': 'Port exposed',
            'CMD': 'Start command defined'
        }
        
        for keyword, description in checks.items():
            if keyword in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading Dockerfile: {e}")
        return False

def check_docker_compose():
    """Check docker-compose.yml configuration."""
    print("\n📋 Checking docker-compose.yml...")
    
    compose_path = "docker-compose.yml"
    if not check_file_exists(compose_path, "Docker Compose file"):
        return False
    
    try:
        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Check version
        if 'version' in compose_config:
            print(f"  ✅ Version: {compose_config['version']}")
        else:
            print("  ❌ Version not specified")
            return False
        
        # Check services
        if 'services' not in compose_config:
            print("  ❌ No services defined")
            return False
        
        services = compose_config['services']
        required_services = ['backend', 'frontend']
        
        for service in required_services:
            if service in services:
                print(f"  ✅ {service.capitalize()} service defined")
                
                # Check service configuration
                service_config = services[service]
                
                # Check build context
                if 'build' in service_config:
                    print(f"    ✅ Build configuration present")
                else:
                    print(f"    ❌ Build configuration missing")
                
                # Check ports
                if 'ports' in service_config:
                    ports = service_config['ports']
                    print(f"    ✅ Ports mapped: {ports}")
                else:
                    print(f"    ❌ Port mapping missing")
                
                # Check environment variables
                if 'environment' in service_config:
                    env_vars = service_config['environment']
                    print(f"    ✅ Environment variables: {len(env_vars)} defined")
                else:
                    print(f"    ⚠️  No environment variables defined")
                    
            else:
                print(f"  ❌ {service.capitalize()} service missing")
                return False
        
        # Check if frontend depends on backend
        if 'depends_on' in services.get('frontend', {}):
            deps = services['frontend']['depends_on']
            if 'backend' in deps:
                print("  ✅ Frontend depends on backend")
            else:
                print("  ❌ Frontend should depend on backend")
        else:
            print("  ❌ Frontend dependencies not specified")
        
        # Check network configuration
        if 'networks' in compose_config:
            print("  ✅ Network configuration present")
        else:
            print("  ⚠️  No custom network configuration")
        
        return True
        
    except yaml.YAMLError as e:
        print(f"  ❌ Error parsing YAML: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error reading docker-compose.yml: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are documented."""
    print("\n📋 Checking environment variables...")
    
    # Check for .env.example or documentation
    env_files = ['.env.example', '.env', 'README.md']
    env_documented = False
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"  ✅ Environment file found: {env_file}")
            env_documented = True
            break
    
    if not env_documented:
        print("  ⚠️  No environment documentation found")
    
    # Required environment variables for the application
    required_env_vars = [
        'OPENAI_API_KEY',
        'GROQ_API_KEY', 
        'WEATHER_API_KEY',
        'GOOGLE_API_KEY'
    ]
    
    print("  📝 Required environment variables:")
    for var in required_env_vars:
        print(f"    - {var}")
    
    return True

def check_package_files():
    """Check package management files."""
    print("\n📋 Checking package files...")
    
    # Backend requirements
    backend_ok = check_file_exists("requirements.txt", "Backend requirements")
    
    # Frontend package files
    frontend_package = check_file_exists("frontend/package.json", "Frontend package.json")
    frontend_lock = check_file_exists("frontend/package-lock.json", "Frontend package-lock.json")
    
    return backend_ok and frontend_package and frontend_lock

def main():
    """Main test function."""
    print("🐳 Docker Setup Verification")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    all_checks_passed = True
    
    # Check Dockerfiles
    backend_dockerfile_ok = check_dockerfile("Dockerfile", "Backend")
    frontend_dockerfile_ok = check_dockerfile("frontend/Dockerfile", "Frontend")
    
    # Check docker-compose
    compose_ok = check_docker_compose()
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Check package files
    packages_ok = check_package_files()
    
    # Check .dockerignore files
    print("\n📋 Checking .dockerignore files...")
    backend_dockerignore = check_file_exists(".dockerignore", "Backend .dockerignore")
    frontend_dockerignore = check_file_exists("frontend/.dockerignore", "Frontend .dockerignore")
    
    all_checks_passed = (
        backend_dockerfile_ok and 
        frontend_dockerfile_ok and 
        compose_ok and 
        env_ok and 
        packages_ok and 
        backend_dockerignore and 
        frontend_dockerignore
    )
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All Docker setup checks passed!")
        print("\n📋 To run the application:")
        print("1. Create a .env file with required API keys")
        print("2. Run: docker-compose up --build")
        print("3. Access frontend at: http://localhost:3000")
        print("4. Backend API at: http://localhost:5001")
        print("\n🔧 Docker Services Configuration:")
        print("- Backend: Python Flask app on port 5001")
        print("- Frontend: Next.js app on port 3000")
        print("- Network: Bridge network for service communication")
        print("- Environment: Production-ready configuration")
    else:
        print("❌ Some Docker setup checks failed!")
        print("Please fix the issues above before running docker-compose.")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())