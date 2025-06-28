#!/usr/bin/env python3
"""Create metrics table in the database"""

import os
os.environ['DATABASE_URL'] = 'sqlite:///test_finwave.db'

from sqlalchemy import create_engine, text
from metrics.models import Base

# Create engine
engine = create_engine('sqlite:///test_finwave.db')

# Create all tables defined in the models
Base.metadata.create_all(bind=engine)

print("✅ Created metrics table")

# Verify the table exists
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'"))
    if result.fetchone():
        print("✅ Metrics table verified")
    else:
        print("❌ Metrics table not found")