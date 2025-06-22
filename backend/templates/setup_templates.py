#!/usr/bin/env python3
"""
Setup script to copy template files to the correct location
"""

import shutil
from pathlib import Path

def setup_templates():
    """Copy template files from Downloads to templates/files/"""
    
    templates_dir = Path(__file__).parent / 'files'
    templates_dir.mkdir(exist_ok=True)
    
    # Template files to copy
    template_files = [
        {
            'source': '/Users/alexandermillar/Downloads/Basic 3-Statement Model-2.xlsx',
            'dest': 'Basic 3-Statement Model-2.xlsx'
        },
        {
            'source': '/Users/alexandermillar/Downloads/Cube - KPI Dashboard-1.xlsx',
            'dest': 'Cube - KPI Dashboard-1.xlsx'
        }
    ]
    
    print("📁 Setting up template files...")
    
    copied = 0
    for template in template_files:
        source = Path(template['source'])
        dest = templates_dir / template['dest']
        
        if source.exists():
            shutil.copy2(source, dest)
            print(f"   ✅ Copied {template['dest']}")
            copied += 1
        else:
            print(f"   ❌ Source not found: {template['source']}")
    
    print(f"\n✅ Setup complete! Copied {copied} templates to {templates_dir}")
    
    if copied == len(template_files):
        print("\n🚀 You can now run:")
        print("   make populate-3statement")
        print("   make populate-kpi")
        print("   make list-templates")
    
    return copied == len(template_files)


if __name__ == '__main__':
    success = setup_templates()
    exit(0 if success else 1)