#!/usr/bin/env python3
"""
Check for QuickBooks sync errors in logs and database
"""

import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db_session, engine
from sqlalchemy import text

def check_log_files():
    """Check log files for QuickBooks errors"""
    print("\n" + "="*80)
    print("LOG FILE ANALYSIS")
    print("="*80)
    
    # Common log locations
    log_paths = [
        Path("logs"),
        Path("/var/log/finwave"),
        Path("finwave.log"),
        Path("app.log"),
        Path("error.log"),
        Path("quickbooks.log"),
        Path("sync.log")
    ]
    
    found_logs = False
    
    for log_path in log_paths:
        if log_path.exists():
            found_logs = True
            
            if log_path.is_file():
                print(f"\n📄 Checking {log_path}...")
                check_single_log(log_path)
            elif log_path.is_dir():
                print(f"\n📁 Checking directory {log_path}...")
                for log_file in log_path.glob("*.log"):
                    print(f"\n   📄 {log_file.name}:")
                    check_single_log(log_file)
    
    if not found_logs:
        print("\n⚠️  No log files found in common locations")
        print("   Logs might be in a different location or sent to stdout/stderr")

def check_single_log(file_path):
    """Check a single log file for QuickBooks errors"""
    error_patterns = [
        r"(?i)quickbooks.*error",
        r"(?i)qb.*error",
        r"(?i)oauth.*error",
        r"(?i)token.*expired",
        r"(?i)refresh.*failed",
        r"(?i)sync.*failed",
        r"(?i)integration.*error",
        r"(?i)authentication.*failed",
        r"(?i)401.*unauthorized",
        r"(?i)403.*forbidden"
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        errors_found = []
        
        for i, line in enumerate(lines):
            for pattern in error_patterns:
                if re.search(pattern, line):
                    # Get context (previous and next line if available)
                    context = []
                    if i > 0:
                        context.append(f"      {lines[i-1].strip()}")
                    context.append(f"   >> {line.strip()}")
                    if i < len(lines) - 1:
                        context.append(f"      {lines[i+1].strip()}")
                    
                    errors_found.append('\n'.join(context))
                    break
        
        if errors_found:
            print(f"   ❌ Found {len(errors_found)} error(s):")
            for i, error in enumerate(errors_found[:5]):  # Show first 5
                print(f"\n   Error {i+1}:")
                print(error)
            
            if len(errors_found) > 5:
                print(f"\n   ... and {len(errors_found) - 5} more errors")
        else:
            print("   ✅ No QuickBooks-related errors found")
    
    except Exception as e:
        print(f"   ⚠️  Error reading file: {e}")

def check_recent_sync_attempts():
    """Check for recent sync attempts and their results"""
    print("\n" + "="*80)
    print("RECENT SYNC ATTEMPTS")
    print("="*80)
    
    with engine.connect() as conn:
        # Check integration_credentials for recent updates
        result = conn.execute(text("""
            SELECT workspace_id, source, status, last_synced_at, last_sync_error, updated_at
            FROM integration_credentials
            WHERE source = 'quickbooks'
            AND updated_at > :since
            ORDER BY updated_at DESC
        """), {"since": datetime.utcnow() - timedelta(days=7)})
        
        recent_attempts = result.fetchall()
        
        if recent_attempts:
            print(f"\n📋 Found {len(recent_attempts)} integration update(s) in the last 7 days:")
            
            for attempt in recent_attempts:
                print(f"\n   🏢 Workspace: {attempt.workspace_id}")
                print(f"      Status: {attempt.status}")
                print(f"      Last Updated: {attempt.updated_at}")
                print(f"      Last Synced: {attempt.last_synced_at or 'Never'}")
                
                if attempt.last_sync_error:
                    print(f"      ❌ Error: {attempt.last_sync_error}")
                else:
                    print("      ✅ No errors")
        else:
            print("\n⚠️  No QuickBooks integration updates in the last 7 days")

def check_sync_patterns():
    """Analyze sync patterns and potential issues"""
    print("\n" + "="*80)
    print("SYNC PATTERN ANALYSIS")
    print("="*80)
    
    with engine.connect() as conn:
        # Check for stuck or incomplete syncs
        result = conn.execute(text("""
            SELECT workspace_id, source, status, last_synced_at, 
                   EXTRACT(EPOCH FROM (NOW() - last_synced_at))/3600 as hours_since_sync
            FROM integration_credentials
            WHERE source = 'quickbooks'
            AND status = 'connected'
            AND last_synced_at IS NOT NULL
        """))
        
        syncs = result.fetchall()
        
        if syncs:
            print("\n⏰ Sync Timing Analysis:")
            
            for sync in syncs:
                hours = sync.hours_since_sync or 0
                
                if hours > 24:
                    status = f"⚠️  {hours:.1f} hours ago (may be overdue)"
                elif hours > 12:
                    status = f"⏰ {hours:.1f} hours ago"
                else:
                    status = f"✅ {hours:.1f} hours ago"
                
                print(f"   • {sync.workspace_id}: Last sync {status}")
        
        # Check for error patterns
        result = conn.execute(text("""
            SELECT status, COUNT(*) as count
            FROM integration_credentials
            WHERE source = 'quickbooks'
            GROUP BY status
        """))
        
        status_counts = result.fetchall()
        
        if status_counts:
            print("\n📊 Integration Status Distribution:")
            for status in status_counts:
                emoji = {
                    'connected': '✅',
                    'error': '❌',
                    'expired': '⚠️',
                    'pending': '⏳',
                    'refreshing': '🔄'
                }.get(status.status, '❓')
                
                print(f"   {emoji} {status.status}: {status.count}")

def check_common_errors():
    """Check for common QuickBooks integration errors"""
    print("\n" + "="*80)
    print("COMMON ERROR PATTERNS")
    print("="*80)
    
    with engine.connect() as conn:
        # Group errors by pattern
        result = conn.execute(text("""
            SELECT last_sync_error, COUNT(*) as count
            FROM integration_credentials
            WHERE source = 'quickbooks'
            AND last_sync_error IS NOT NULL
            GROUP BY last_sync_error
            ORDER BY count DESC
        """))
        
        error_patterns = result.fetchall()
        
        if error_patterns:
            print("\n❌ Error Frequency:")
            for error in error_patterns:
                print(f"\n   Count: {error.count}")
                print(f"   Error: {error.last_sync_error[:200]}...")
                
                # Provide diagnosis
                if "token" in error.last_sync_error.lower():
                    print("   💡 Diagnosis: OAuth token issue - may need re-authorization")
                elif "401" in error.last_sync_error or "unauthorized" in error.last_sync_error.lower():
                    print("   💡 Diagnosis: Authentication failed - check credentials")
                elif "timeout" in error.last_sync_error.lower():
                    print("   💡 Diagnosis: Connection timeout - check network/firewall")
                elif "rate limit" in error.last_sync_error.lower():
                    print("   💡 Diagnosis: API rate limit - reduce sync frequency")
        else:
            print("\n✅ No error patterns found")

def suggest_fixes():
    """Suggest fixes based on findings"""
    print("\n" + "="*80)
    print("RECOMMENDED ACTIONS")
    print("="*80)
    
    with engine.connect() as conn:
        # Check for common issues
        result = conn.execute(text("""
            SELECT 
                COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
                COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_count,
                COUNT(CASE WHEN last_synced_at IS NULL THEN 1 END) as never_synced,
                COUNT(CASE WHEN last_synced_at < NOW() - INTERVAL '24 hours' THEN 1 END) as stale_syncs
            FROM integration_credentials
            WHERE source = 'quickbooks'
        """))
        
        stats = result.fetchone()
        
        if stats:
            print("\n🔧 Suggested Actions:")
            
            if stats.error_count > 0:
                print(f"\n   ❌ {stats.error_count} integration(s) in error state:")
                print("      1. Check error messages above")
                print("      2. Re-authorize QuickBooks connection")
                print("      3. Verify API credentials are valid")
            
            if stats.expired_count > 0:
                print(f"\n   ⚠️  {stats.expired_count} expired token(s):")
                print("      1. Use refresh token to get new access token")
                print("      2. If refresh fails, re-authorize the integration")
            
            if stats.never_synced > 0:
                print(f"\n   ⏳ {stats.never_synced} integration(s) never synced:")
                print("      1. Trigger initial sync manually")
                print("      2. Check if sync scheduler is running")
            
            if stats.stale_syncs > 0:
                print(f"\n   🕐 {stats.stale_syncs} integration(s) not synced in 24+ hours:")
                print("      1. Check if sync scheduler is running")
                print("      2. Review sync frequency settings")
                print("      3. Check for blocking errors")

def main():
    """Run all error checks"""
    try:
        print("\n🔍 QUICKBOOKS SYNC ERROR ANALYSIS")
        print("=" * 80)
        print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Run all checks
        check_log_files()
        check_recent_sync_attempts()
        check_sync_patterns()
        check_common_errors()
        suggest_fixes()
        
        print("\n" + "="*80)
        print("✅ Error analysis complete!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()