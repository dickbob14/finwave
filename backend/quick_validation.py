#!/usr/bin/env python3
"""
Quick validation script to check critical components
"""

import os
import sys
from pathlib import Path

print("🔍 FinWave Quick Validation")
print("=" * 40)

# Check 1: Critical files exist
print("\n1️⃣ Critical Files Check")
critical_files = [
    "backend/app/main.py",
    "backend/models/workspace.py", 
    "backend/integrations/quickbooks/client.py",
    "backend/metrics/ingest.py",
    "backend/reports/pdf_service.py",
    "backend/routes/oauth.py",
    "backend/static/theme.json",
    "frontend/src/app/page.tsx",
    "frontend/src/components/navigation.tsx",
    "frontend/tailwind.config.js",
    "backend/.env.example"
]

all_exist = True
for file in critical_files:
    path = Path(file.replace("backend/", "").replace("frontend/", "../frontend/"))
    if path.exists():
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} MISSING")
        all_exist = False

# Check 2: Import test
print("\n2️⃣ Import Test")
try:
    sys.path.append(str(Path(__file__).parent))
    
    # Test critical imports
    imports = [
        "from models.workspace import Workspace",
        "from core.database import get_db_session",
        "from metrics.ingest import MetricIngestor",
        "from reports.pdf_service import PDFReportService"
    ]
    
    for imp in imports:
        try:
            exec(imp)
            print(f"  ✅ {imp}")
        except Exception as e:
            print(f"  ❌ {imp} - {str(e)}")
            
except Exception as e:
    print(f"  ❌ Import setup failed: {e}")

# Check 3: Environment variables
print("\n3️⃣ Environment Variables")
required_vars = [
    "QB_CLIENT_ID",
    "QB_CLIENT_SECRET", 
    "QB_COMPANY_ID",
    "QB_ENVIRONMENT",
    "DATABASE_URL",
    "FERNET_SECRET"
]

env_file = Path(".env")
if env_file.exists():
    print("  ✅ .env file exists")
    # Load env vars
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var} is set")
        else:
            print(f"  ⚠️  {var} not set")
else:
    print("  ❌ .env file missing")

# Check 4: Frontend build
print("\n4️⃣ Frontend Check")
frontend_checks = [
    ("package.json", "../frontend/package.json"),
    ("tailwind.config.js", "../frontend/tailwind.config.js"),
    ("FinWave logo", "../frontend/public/finwave-logo.svg"),
    ("Navigation component", "../frontend/src/components/navigation.tsx")
]

for name, path in frontend_checks:
    if Path(path).exists():
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} missing")

# Check 5: API routes
print("\n5️⃣ API Routes")
route_files = [
    "routes/oauth.py",
    "routes/metrics.py",
    "routes/reports.py",
    "routes/forecast.py",
    "routes/alerts.py"
]

for route in route_files:
    if Path(route).exists():
        print(f"  ✅ {route}")
    else:
        print(f"  ❌ {route} missing")

print("\n" + "=" * 40)
if all_exist:
    print("✅ All critical components present!")
    print("Next steps:")
    print("  1. Run: ./scripts/dev_quick_setup.sh")
    print("  2. Visit: http://localhost:3000")
else:
    print("❌ Some components missing - check above")