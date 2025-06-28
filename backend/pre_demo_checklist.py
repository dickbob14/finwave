#!/usr/bin/env python3
"""
FinWave Pre-Demo Checklist
Validates everything is ready for demo
"""

import os
import json
from pathlib import Path
from datetime import datetime

print("""
🚀 FinWave Pre-Demo Checklist
=============================
""")

# Track overall status
all_good = True

def check_status(condition, pass_msg, fail_msg):
    global all_good
    if condition:
        print(f"✅ {pass_msg}")
        return True
    else:
        print(f"❌ {fail_msg}")
        all_good = False
        return False

print("1️⃣  STATIC SAFETY CHECKS")
print("-" * 30)

# Check critical Python files for obvious issues
python_files = [
    "app/main.py",
    "models/workspace.py",
    "routes/oauth.py", 
    "integrations/quickbooks/client.py",
    "metrics/ingest.py"
]

for file in python_files:
    if Path(file).exists():
        with open(file, 'r') as f:
            content = f.read()
            # Check for debug prints
            has_debug = "print(" in content and "# DEBUG" not in content
            check_status(
                not has_debug,
                f"{file} - no debug prints",
                f"{file} - contains debug print statements"
            )

print("\n2️⃣  CONFIGURATION CHECKS")
print("-" * 30)

# Check .env exists
check_status(
    Path(".env").exists(),
    ".env file exists",
    ".env file missing - copy from .env.example"
)

# Check critical environment variables
if Path(".env").exists():
    with open(".env", 'r') as f:
        env_content = f.read()
        required = ["QB_CLIENT_ID", "QB_CLIENT_SECRET", "DATABASE_URL", "FERNET_SECRET"]
        for var in required:
            check_status(
                f"{var}=" in env_content and f"{var}=\n" not in env_content,
                f"{var} is configured",
                f"{var} not configured in .env"
            )

# Check theme.json
theme_path = Path("static/theme.json")
if theme_path.exists():
    with open(theme_path, 'r') as f:
        theme = json.load(f)
        check_status(
            theme.get("colors", {}).get("primary") == "#1E2A38",
            "Theme uses FinWave colors",
            "Theme colors not updated"
        )

print("\n3️⃣  FRONTEND CHECKS")
print("-" * 30)

# Check frontend build files
frontend_path = Path("../frontend")
check_status(
    (frontend_path / "package.json").exists(),
    "Frontend package.json exists",
    "Frontend package.json missing"
)

check_status(
    (frontend_path / "tailwind.config.js").exists(),
    "Tailwind config exists",
    "Tailwind config missing"
)

check_status(
    (frontend_path / "public/finwave-logo.svg").exists(),
    "FinWave logo present",
    "FinWave logo missing"
)

# Check for node_modules
check_status(
    (frontend_path / "node_modules").exists(),
    "Frontend dependencies installed",
    "Frontend dependencies not installed - run npm install"
)

print("\n4️⃣  DATA READINESS")
print("-" * 30)

# Check for database
db_path = Path("dev.duckdb")
check_status(
    db_path.exists(),
    "Database file exists",
    "Database not initialized - run make init-db"
)

# Check for demo workspace script
check_status(
    Path("scripts/seed_demo.py").exists(),
    "Demo seed script exists",
    "Demo seed script missing"
)

# Check for QuickBooks integration files
qb_files = [
    "integrations/quickbooks/client.py",
    "integrations/quickbooks/sync.py"
]
for file in qb_files:
    check_status(
        Path(file).exists(),
        f"{file} exists",
        f"{file} missing - QuickBooks integration incomplete"
    )

print("\n5️⃣  API ROUTES")
print("-" * 30)

# Check critical routes
routes = [
    "routes/oauth.py",
    "routes/metrics.py", 
    "routes/reports.py",
    "routes/alerts.py",
    "routes/forecast.py"
]

for route in routes:
    check_status(
        Path(route).exists(),
        f"{route} exists",
        f"{route} missing"
    )

print("\n6️⃣  DEMO SCRIPTS")  
print("-" * 30)

# Check for quick setup script
check_status(
    Path("scripts/dev_quick_setup.sh").exists(),
    "Quick setup script exists",
    "Quick setup script missing"
)

# Check if script is executable
if Path("scripts/dev_quick_setup.sh").exists():
    check_status(
        os.access("scripts/dev_quick_setup.sh", os.X_OK),
        "Quick setup script is executable",
        "Quick setup script not executable - run chmod +x"
    )

print("\n7️⃣  PDF GENERATION")
print("-" * 30)

# Check PDF templates
pdf_templates = [
    "pdf_templates/base.html",
    "pdf_templates/report.html"
]

for template in pdf_templates:
    check_status(
        Path(template).exists(),
        f"{template} exists",
        f"{template} missing - PDF generation will fail"
    )

print("\n" + "=" * 50)

if all_good:
    print("""
✅ ALL CHECKS PASSED! Ready for demo.

Next steps:
1. Run: ./scripts/dev_quick_setup.sh
2. Visit: http://localhost:3000
3. Click "Connect QuickBooks" to start demo

Demo talking points:
- Real QuickBooks sandbox data (Craig's Landscaping)
- One-click board report generation
- AI-powered variance analysis
- Interactive scenario planning
- Beautiful FinWave branding throughout
""")
else:
    print("""
⚠️  SOME CHECKS FAILED - Fix issues above before demo.

Quick fixes:
- Missing .env? Copy .env.example and add credentials
- Missing dependencies? Run: npm install (frontend) 
- Database not initialized? Run: make init-db
""")

print(f"\nChecklist completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")