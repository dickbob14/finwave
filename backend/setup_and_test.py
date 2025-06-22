#!/usr/bin/env python3
"""
Complete setup and test script for Block D
This will set up everything needed to test all functionality
"""
import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def setup_environment():
    """Set up the environment and dependencies"""
    print("🚀 Setting up FinWave Block D environment...")
    
    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print(f"📁 Working directory: {backend_dir}")
    
    # Check if virtual environment exists
    venv_path = backend_dir / ".venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("Please run: python -m venv .venv")
        return False
    
    # Check if we can import required modules
    try:
        import fastapi
        import sqlalchemy
        import alembic
        print("✅ Core dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: source .venv/bin/activate && pip install -r requirements.txt")
        return False
    
    return True

def setup_database():
    """Set up database with SQLite for easy testing"""
    print("\n🗄️ Setting up database...")
    
    # Use SQLite for testing to avoid PostgreSQL dependency
    test_db_path = "test_finwave.db"
    
    # Remove existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("🗑️ Removed existing test database")
    
    # Create database connection string
    database_url = f"sqlite:///{test_db_path}"
    
    # Set environment variable for database
    os.environ["DATABASE_URL"] = database_url
    print(f"📊 Using database: {database_url}")
    
    return True

def create_database_tables():
    """Create database tables using SQLAlchemy directly"""
    print("\n🏗️ Creating database tables...")
    
    try:
        from sqlalchemy import create_engine
        from models.financial import Base
        
        database_url = os.environ.get("DATABASE_URL")
        engine = create_engine(database_url)
        
        # Create all tables
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def seed_test_data():
    """Seed database with test data"""
    print("\n🌱 Seeding test data...")
    
    try:
        # Import and run the seeder
        sys.path.append('.')
        from test_data_seeder import seed_test_data
        seed_test_data()
        return True
    except Exception as e:
        print(f"❌ Failed to seed data: {e}")
        print(f"Error details: {str(e)}")
        return False

def fix_imports():
    """Fix import issues in the main FastAPI app"""
    print("\n🔧 Fixing import paths...")
    
    # Read the main.py file
    main_py_path = "app/main.py"
    
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Fix the import statement
        old_import = "from routes import export_router, report_router, insight_router, charts_router"
        new_import = """import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes.export import router as export_router
from routes.report import router as report_router
from routes.insight import router as insight_router
from routes.charts import router as charts_router"""
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            with open(main_py_path, 'w') as f:
                f.write(content)
            
            print("✅ Fixed import paths in main.py")
        else:
            print("⚠️ Import paths already fixed or not found")
            
    except Exception as e:
        print(f"❌ Failed to fix imports: {e}")

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    print("Server will start at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        os.system("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    
    import requests
    import time
    
    # Give server time to start
    time.sleep(2)
    
    base_url = "http://localhost:8000"
    
    tests = [
        ("Health check", f"{base_url}/health"),
        ("Export status", f"{base_url}/export/status"),
        ("Chart status", f"{base_url}/charts/status"),
        ("Available charts", f"{base_url}/charts/available-charts"),
    ]
    
    for test_name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {test_name}: PASS")
            else:
                print(f"⚠️ {test_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {test_name}: {e}")

def create_test_script():
    """Create a comprehensive test script"""
    print("\n📝 Creating test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
Quick test script for FinWave Block D
Run this after the server is started
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test all major endpoints"""
    print("🧪 Testing FinWave Block D endpoints...")
    
    # Date range for testing
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    tests = [
        # Basic health checks
        ("GET", "/health", {}, "Health check"),
        ("GET", "/export/status", {}, "Export system status"),
        ("GET", "/charts/status", {}, "Charts system status"),
        ("GET", "/insight/status", {}, "Insights system status"),
        
        # Chart endpoints
        ("GET", "/charts/available-charts", {}, "Available chart types"),
        ("GET", "/charts/revenue-trend", {
            "start_date": start_date, 
            "end_date": end_date, 
            "grouping": "monthly"
        }, "Revenue trend chart"),
        ("GET", "/charts/expense-breakdown", {
            "start_date": start_date, 
            "end_date": end_date, 
            "chart_type": "pie"
        }, "Expense breakdown chart"),
        
        # Insight endpoints
        ("GET", "/insight/variance", {
            "start_date": start_date, 
            "end_date": end_date
        }, "Variance analysis"),
        ("POST", "/insight/analyze", {
            "question": "Why are expenses higher this month?",
            "start_date": start_date,
            "end_date": end_date
        }, "WHY question analysis"),
        
        # Export endpoints
        ("GET", "/export/formats", {}, "Export formats"),
    ]
    
    results = []
    
    for method, endpoint, params, description in tests:
        try:
            url = f"{BASE_URL}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            else:
                response = requests.post(url, json=params, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {description}: PASS")
                results.append((description, "PASS", response.status_code))
            else:
                print(f"⚠️ {description}: HTTP {response.status_code}")
                results.append((description, "FAIL", response.status_code))
                
        except Exception as e:
            print(f"❌ {description}: {e}")
            results.append((description, "ERROR", str(e)))
    
    print(f"\\n📊 Test Results: {len([r for r in results if r[1] == 'PASS'])}/{len(results)} passed")
    
    return results

def test_chart_data():
    """Test chart data structure"""
    print("\\n📊 Testing chart data structure...")
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    try:
        response = requests.get(f"{BASE_URL}/charts/revenue-trend", params={
            "start_date": start_date,
            "end_date": end_date,
            "grouping": "monthly"
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Check data structure
            required_keys = ["chart_type", "plotly_data", "data_points", "generated_at"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if not missing_keys:
                print("✅ Chart data structure: VALID")
                print(f"   └─ Data points: {data.get('data_points', 0)}")
                print(f"   └─ Chart type: {data.get('chart_type', 'unknown')}")
                
                # Check Plotly data structure
                plotly_data = data.get("plotly_data", {})
                if "data" in plotly_data and "layout" in plotly_data:
                    print("✅ Plotly data structure: VALID")
                else:
                    print("⚠️ Plotly data structure: INVALID")
            else:
                print(f"⚠️ Chart data missing keys: {missing_keys}")
        else:
            print(f"❌ Chart data request failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Chart data test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 FinWave Block D Test Suite\\n")
    
    # Run endpoint tests
    test_endpoints()
    
    # Test chart data structure
    test_chart_data()
    
    print("\\n✅ Testing complete!")
    print("\\n📝 Frontend Integration:")
    print("Use the chart data from /charts/* endpoints directly in React components")
    print("Example: <Plot data={chartData.plotly_data.data} layout={chartData.plotly_data.layout} />")

if __name__ == "__main__":
    main()
'''
    
    with open("quick_test.py", "w") as f:
        f.write(test_script)
    
    print("✅ Created quick_test.py")

def main():
    """Main setup and test function"""
    print("🎯 FinWave Block D Complete Setup & Test")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        return
    
    # Setup database
    if not setup_database():
        return
    
    # Create tables
    if not create_database_tables():
        return
    
    # Fix imports
    fix_imports()
    
    # Seed test data
    if not seed_test_data():
        return
    
    # Create test script
    create_test_script()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Start the server: uvicorn app.main:app --reload")
    print("2. In another terminal, run: python quick_test.py")
    print("3. Visit http://localhost:8000/docs for API documentation")
    print("4. Test charts at: http://localhost:8000/charts/available-charts")
    
    # Ask if user wants to start server now
    response = input("\n🚀 Start the server now? (y/n): ")
    if response.lower() in ['y', 'yes']:
        start_server()

if __name__ == "__main__":
    main()