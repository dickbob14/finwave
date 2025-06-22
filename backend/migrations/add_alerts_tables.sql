-- Add alerts table for variance monitoring
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(255) PRIMARY KEY,
    workspace_id VARCHAR(255) NOT NULL REFERENCES workspaces(id),
    metric_id VARCHAR(255) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'warning',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    
    -- Alert content
    message TEXT NOT NULL,
    current_value FLOAT,
    threshold_value FLOAT,
    comparison_value FLOAT,
    
    -- Timestamps
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- User tracking
    acknowledged_by VARCHAR(255),
    resolved_by VARCHAR(255),
    
    -- Notes
    notes TEXT,
    
    -- Indexes
    CONSTRAINT alerts_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_alerts_workspace_triggered ON alerts(workspace_id, triggered_at);
CREATE INDEX IF NOT EXISTS ix_alerts_workspace_status ON alerts(workspace_id, status);
CREATE INDEX IF NOT EXISTS ix_alerts_metric ON alerts(workspace_id, metric_id);
CREATE INDEX IF NOT EXISTS ix_alerts_rule ON alerts(workspace_id, rule_name);

-- Add scheduled jobs table for tracking job execution
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id VARCHAR(255) PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    workspace_id VARCHAR(255),
    
    -- Execution tracking
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    
    -- Results
    records_processed FLOAT,
    error_message TEXT,
    result_json TEXT
);

-- Create indexes for scheduled jobs
CREATE INDEX IF NOT EXISTS ix_scheduled_jobs_name_started ON scheduled_jobs(job_name, started_at);
CREATE INDEX IF NOT EXISTS ix_scheduled_jobs_workspace ON scheduled_jobs(workspace_id, started_at);