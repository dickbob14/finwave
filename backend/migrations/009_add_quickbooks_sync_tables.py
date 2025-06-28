"""
Add tables specifically for QuickBooks sync and KPI calculations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine


def upgrade():
    """Add QuickBooks sync specific tables"""
    with engine.connect() as conn:
        # Create qb_financial_statements table (renamed to avoid conflict)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qb_financial_statements (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                statement_type VARCHAR NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create qb_account_balances table (renamed to avoid conflict)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qb_account_balances (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                account_id VARCHAR NOT NULL,
                account_name VARCHAR NOT NULL,
                account_type VARCHAR NOT NULL,
                account_subtype VARCHAR,
                balance FLOAT NOT NULL,
                currency VARCHAR DEFAULT 'USD',
                as_of_date TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create qb_transactions table (renamed to avoid conflict)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qb_transactions (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                quickbooks_id VARCHAR NOT NULL,
                transaction_type VARCHAR NOT NULL,
                transaction_date TIMESTAMP NOT NULL,
                amount FLOAT NOT NULL,
                currency VARCHAR DEFAULT 'USD',
                customer_id VARCHAR,
                vendor_id VARCHAR,
                account_id VARCHAR,
                description VARCHAR,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create qb_customers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qb_customers (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                quickbooks_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                email VARCHAR,
                phone VARCHAR,
                first_transaction_date TIMESTAMP,
                last_transaction_date TIMESTAMP,
                total_revenue FLOAT DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                status VARCHAR DEFAULT 'active',
                churn_date TIMESTAMP,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create qb_vendors table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS qb_vendors (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                quickbooks_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                email VARCHAR,
                phone VARCHAR,
                total_spend FLOAT DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create kpi_metrics table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kpi_metrics (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                metric_name VARCHAR NOT NULL,
                metric_value FLOAT NOT NULL,
                metric_unit VARCHAR,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                calculation_method VARCHAR,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create sync_logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id VARCHAR PRIMARY KEY,
                company_id VARCHAR NOT NULL,
                sync_type VARCHAR NOT NULL,
                sync_status VARCHAR NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                records_synced INTEGER DEFAULT 0,
                error_message VARCHAR,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """))
        
        # Create indexes for better performance
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qb_financial_statements_company_type ON qb_financial_statements(company_id, statement_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qb_account_balances_company_account ON qb_account_balances(company_id, account_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qb_transactions_company_type ON qb_transactions(company_id, transaction_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qb_transactions_date ON qb_transactions(company_id, transaction_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qb_customers_company ON qb_customers(company_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qb_vendors_company ON qb_vendors(company_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kpi_metrics_company_metric ON kpi_metrics(company_id, metric_name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sync_logs_company ON sync_logs(company_id)"))
        
        conn.commit()
        print("✓ QuickBooks sync tables created successfully")


def downgrade():
    """Remove QuickBooks sync tables"""
    with engine.connect() as conn:
        # Drop tables in reverse order due to foreign key constraints
        conn.execute(text("DROP TABLE IF EXISTS sync_logs"))
        conn.execute(text("DROP TABLE IF EXISTS kpi_metrics"))
        conn.execute(text("DROP TABLE IF EXISTS qb_vendors"))
        conn.execute(text("DROP TABLE IF EXISTS qb_customers"))
        conn.execute(text("DROP TABLE IF EXISTS qb_transactions"))
        conn.execute(text("DROP TABLE IF EXISTS qb_account_balances"))
        conn.execute(text("DROP TABLE IF EXISTS qb_financial_statements"))
        
        conn.commit()
        print("✓ QuickBooks sync tables removed")


if __name__ == "__main__":
    upgrade()