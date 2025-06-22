-- Add integration_credentials table for OAuth token storage
CREATE TABLE IF NOT EXISTS integration_credentials (
    id VARCHAR(255) PRIMARY KEY,
    workspace_id VARCHAR(255) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    
    -- Encrypted OAuth tokens
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    
    -- Token metadata
    expires_at TIMESTAMP,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    scope TEXT,
    
    -- Integration-specific encrypted metadata
    metadata_encrypted TEXT,
    
    -- Sync tracking
    last_synced_at TIMESTAMP,
    last_sync_error TEXT,
    sync_frequency_minutes VARCHAR(10) DEFAULT '60',
    
    -- Audit
    connected_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one integration per source per workspace
    CONSTRAINT unique_workspace_source UNIQUE (workspace_id, source)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_integration_workspace_source ON integration_credentials(workspace_id, source);
CREATE INDEX IF NOT EXISTS ix_integration_status ON integration_credentials(status);
CREATE INDEX IF NOT EXISTS ix_integration_sync ON integration_credentials(last_synced_at);

-- Add comment
COMMENT ON TABLE integration_credentials IS 'Encrypted storage for OAuth tokens and integration credentials';