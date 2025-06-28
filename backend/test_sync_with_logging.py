#!/usr/bin/env python3
"""
Test QuickBooks sync with proper logging
"""

import sys
import os
import logging

# Configure logging to see all messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_sync_direct import test_direct_sync

if __name__ == "__main__":
    test_direct_sync()