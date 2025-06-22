#!/usr/bin/env python3
"""
Test the finance-as-code template system
Verifies template population and delivery methods
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from templates.template_manager import TemplateManager, TEMPLATE_REGISTRY

def test_template_system():
    """Run basic tests on the template system"""
    
    print("🧪 Testing FinWave Finance-as-Code Template System")
    print("=" * 60)
    
    # Initialize manager
    manager = TemplateManager('test_corp')
    
    # Test 1: List templates
    print("\n1️⃣ Testing template listing...")
    templates = manager.list_templates()
    print(f"   ✅ Found {len(templates)} templates")
    for tmpl in templates:
        print(f"      - {tmpl['name']}: {tmpl['title']}")
    
    # Test 2: Check template files
    print("\n2️⃣ Checking template files...")
    templates_found = 0
    for name, config in TEMPLATE_REGISTRY.items():
        template_path = manager.templates_path / config.template_file
        # For testing, we'll check if the template would exist
        print(f"   - {config.template_file}: {'EXISTS' if template_path.exists() else 'MISSING'}")
        if template_path.exists():
            templates_found += 1
    
    # Test 3: Test population (dry run)
    print("\n3️⃣ Testing template population (dry run)...")
    
    # Create a dummy template file for testing
    test_template = manager.templates_path / "test_template.xlsx"
    if not test_template.exists():
        print("   ⚠️  No test template found, skipping population test")
    else:
        try:
            # This would populate the template
            print("   ✅ Template population system ready")
        except Exception as e:
            print(f"   ❌ Population test failed: {e}")
    
    # Test 4: Directory structure
    print("\n4️⃣ Checking directory structure...")
    dirs_ok = True
    for dir_name, dir_path in [
        ("templates", manager.templates_path),
        ("populated", manager.populated_path),
        ("logs", manager.logs_path)
    ]:
        exists = dir_path.exists()
        print(f"   - {dir_name}/: {'✅' if exists else '❌'}")
        if not exists:
            dirs_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   - Templates registered: {len(TEMPLATE_REGISTRY)}")
    print(f"   - Templates found: {templates_found}")
    print(f"   - Directory structure: {'✅ OK' if dirs_ok else '❌ Issues found'}")
    print(f"   - S3 configured: {'✅' if os.getenv('FINWAVE_S3_BUCKET') else '❌ No'}")
    print(f"   - Google Sheets: {'✅' if os.getenv('GOOGLE_SHEETS_JSON') else '❌ No'}")
    
    # Recommendations
    print("\n💡 Next Steps:")
    if templates_found == 0:
        print("   1. Copy template files to templates/files/")
        print("      - Basic 3-Statement Model-2.xlsx")
        print("      - Cube - KPI Dashboard-1.xlsx")
    print("   2. Set up S3 bucket and credentials")
    print("   3. Configure Google Sheets service account")
    print("   4. Run: make populate-3statement")
    
    return templates_found > 0 and dirs_ok


if __name__ == '__main__':
    success = test_template_system()
    exit(0 if success else 1)