#!/usr/bin/env python3
"""
Test sync trigger manually to capture errors
"""

import sys
import os
import logging
import traceback

# Configure logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler.sync_jobs import enqueue_initial_sync, execute_sync_job

def test_sync_trigger():
    """Test sync trigger and execution"""
    print("=== Testing Sync Trigger ===")
    
    workspace_id = 'default'
    source = 'quickbooks'
    
    # Step 1: Test enqueue
    print("\n1. Testing enqueue_initial_sync...")
    try:
        job_id = enqueue_initial_sync(workspace_id, source)
        print(f"✅ Job enqueued with ID: {job_id}")
    except Exception as e:
        print(f"❌ Enqueue failed: {e}")
        traceback.print_exc()
        return
    
    # Step 2: Test direct execution (bypass thread)
    print("\n2. Testing direct sync execution...")
    
    # Create a test job
    test_job = {
        'id': job_id,
        'workspace_id': workspace_id,
        'source': source,
        'type': 'initial_sync',
        'priority': 'normal',
        'created_at': None
    }
    
    try:
        result = execute_sync_job(test_job)
        print(f"✅ Sync completed: {result}")
    except Exception as e:
        print(f"❌ Sync execution failed: {e}")
        traceback.print_exc()
        
        # Check if it's an import error
        if "No module named" in str(e):
            print("\nPossible missing dependencies. Let's check imports...")
            
            # Try importing each module separately
            modules_to_test = [
                'core.database',
                'models.integration',
                'models.workspace',
                'scheduler.models',
                'metrics.ingest',
                'integrations.quickbooks.sync_v2'
            ]
            
            for module in modules_to_test:
                try:
                    __import__(module)
                    print(f"  ✅ {module} - OK")
                except Exception as import_error:
                    print(f"  ❌ {module} - FAILED: {import_error}")


if __name__ == "__main__":
    test_sync_trigger()