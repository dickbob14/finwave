# FinWave Production Setup Guide

This guide walks you through setting up FinWave with real OAuth credentials to pull live data from QuickBooks, Salesforce, and other integrations.

## Prerequisites

1. Python 3.8+ installed
2. Node.js 16+ installed
3. Developer accounts for the services you want to integrate

## Backend Setup

### 1. Initialize the Database

```bash
cd backend
python init_db_simple.py
```

This creates the database with all required tables including the new `oauth_app_configs` table for storing OAuth credentials.

### 2. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key (required for AI features):

```
OPENAI_API_KEY=your-openai-api-key-here
```

The OAuth credentials can now be configured through the UI, so you don't need to add them to the .env file.

### 3. Create Initial Workspace

```bash
python init_production.py
```

This creates an initial workspace without any sample data.

### 4. Start the Backend Server

```bash
cd app
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## Frontend Setup

### 1. Install Dependencies

```bash
cd ../frontend
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Setting Up OAuth Integrations

### 1. Access the Connect Data Sources Dialog

1. Navigate to http://localhost:3000
2. Click on "Connect Data Sources" in the dashboard
3. You'll see a list of available integrations

### 2. Configure OAuth Credentials

For each integration you want to use:

1. Click the "Configure" button next to the integration
2. In the OAuth Configuration dialog:
   - Follow the setup guide to create an OAuth app in the service's developer portal
   - Copy your Client ID and Client Secret
   - Paste them into the form
   - Select the appropriate environment (Production or Sandbox)
   - Click "Save Credentials"

### 3. Connect to Services

After configuring credentials:

1. Click the "Connect" button for the integration
2. A popup window will open for OAuth authorization
3. Log in to the service and authorize FinWave
4. The window will close automatically when complete
5. Your data will begin syncing

## OAuth Setup for Each Service

### QuickBooks

1. Go to https://developer.intuit.com
2. Create a new app or select an existing one
3. Add OAuth 2.0 redirect URI: `http://localhost:8000/api/oauth/callback`
4. Select the "Accounting" scope
5. Copy your Client ID and Client Secret

### Salesforce

1. Go to Salesforce Setup > App Manager
2. Create a new Connected App
3. Enable OAuth Settings
4. Add callback URL: `http://localhost:8000/api/oauth/callback`
5. Select OAuth scopes: `api`, `refresh_token`
6. Copy Consumer Key (Client ID) and Consumer Secret

### HubSpot

1. Go to https://developers.hubspot.com
2. Create a new app
3. Navigate to Auth settings
4. Add redirect URL: `http://localhost:8000/api/oauth/callback`
5. Copy App ID (Client ID) and Client Secret

### Gusto

1. Go to https://dev.gusto.com
2. Create a new application
3. Set redirect URI: `http://localhost:8000/api/oauth/callback`
4. Copy Client ID and Client Secret

## Testing Your Setup

1. After connecting a data source, click "Sync Now" to trigger an immediate sync
2. Navigate to the Dashboard to see your real financial data
3. Use the AI-powered insights to analyze your business metrics

## Security Notes

- OAuth credentials are encrypted before storage using Fernet symmetric encryption
- Credentials are stored per workspace, allowing multi-tenant usage
- Access tokens are automatically refreshed when needed
- All API communications use HTTPS in production

## Troubleshooting

### OAuth Not Configured Error

If you see "OAuth not configured" when trying to connect:
1. Make sure you've clicked "Configure" and saved your credentials
2. Check that both Client ID and Client Secret were entered correctly
3. Verify the credentials in your developer dashboard

### Connection Failed

If the OAuth flow fails:
1. Check that your redirect URI matches exactly: `http://localhost:8000/api/oauth/callback`
2. Ensure your app is approved/activated in the service's developer portal
3. For sandbox/test environments, make sure you're using test credentials

### Data Not Syncing

If data doesn't appear after connecting:
1. Click "Sync Now" to trigger a manual sync
2. Check the integration status in the Connect Data Sources dialog
3. Review backend logs for any sync errors

## Production Deployment

For production deployment:
1. Update redirect URIs to your production domain
2. Use environment-specific OAuth apps
3. Enable HTTPS for all endpoints
4. Configure proper CORS origins in the backend
5. Set up regular backup of the DuckDB database