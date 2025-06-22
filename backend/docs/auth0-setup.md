# Auth0 Setup Guide for FinWave

This guide walks through setting up Auth0 for secure multi-tenant authentication.

## 1. Create Auth0 Tenant

1. Sign up at [auth0.com](https://auth0.com)
2. Create a new tenant (e.g., `finwave`)
3. Note your domain: `finwave.auth0.com`

## 2. Create API

1. Go to **APIs** → **Create API**
2. Settings:
   - Name: `FinWave API`
   - Identifier: `https://api.finwave.io`
   - Signing Algorithm: `RS256`

## 3. Create Application

1. Go to **Applications** → **Create Application**
2. Choose **Single Page Application**
3. Settings:
   - Name: `FinWave Web App`
   - Allowed Callback URLs: 
     ```
     http://localhost:3000/api/auth/callback,
     https://app.finwave.io/api/auth/callback
     ```
   - Allowed Logout URLs:
     ```
     http://localhost:3000,
     https://app.finwave.io
     ```
   - Allowed Web Origins:
     ```
     http://localhost:3000,
     https://app.finwave.io
     ```

## 4. Add Custom Claims

Create an Auth0 Action to add workspace_id to tokens:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://finwave.io';
  
  // Get workspace from user metadata
  const workspaceId = event.user.app_metadata?.workspace_id;
  
  if (workspaceId) {
    api.idToken.setCustomClaim(`${namespace}/workspace_id`, workspaceId);
    api.accessToken.setCustomClaim(`${namespace}/workspace_id`, workspaceId);
  }
  
  // Add permissions
  const permissions = event.user.app_metadata?.permissions || ['read'];
  api.idToken.setCustomClaim(`${namespace}/permissions`, permissions);
  api.accessToken.setCustomClaim(`${namespace}/permissions`, permissions);
};
```

## 5. Environment Variables

Backend (.env):
```bash
AUTH0_DOMAIN=finwave.auth0.com
AUTH0_API_AUDIENCE=https://api.finwave.io
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# For development
BYPASS_AUTH=false
```

Frontend (.env.local):
```bash
NEXT_PUBLIC_AUTH0_DOMAIN=finwave.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=your-client-id
NEXT_PUBLIC_AUTH0_REDIRECT_URI=http://localhost:3000/api/auth/callback
NEXT_PUBLIC_AUTH0_AUDIENCE=https://api.finwave.io
AUTH0_SECRET=your-auth0-secret
AUTH0_BASE_URL=http://localhost:3000
```

## 6. User Management

### Create User with Workspace

Using Auth0 Management API:

```bash
curl -X POST https://finwave.auth0.com/api/v2/users \
  -H "Authorization: Bearer YOUR_MGMT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "connection": "Username-Password-Authentication",
    "app_metadata": {
      "workspace_id": "acme-corp",
      "permissions": ["read", "write"]
    }
  }'
```

### Assign Workspace to Existing User

```bash
curl -X PATCH https://finwave.auth0.com/api/v2/users/USER_ID \
  -H "Authorization: Bearer YOUR_MGMT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_metadata": {
      "workspace_id": "acme-corp",
      "permissions": ["read", "write"]
    }
  }'
```

## 7. Testing Authentication

### Test Token Validation

```bash
# Get a test token
TOKEN=$(curl -X POST https://finwave.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://api.finwave.io",
    "grant_type": "client_credentials"
  }' | jq -r .access_token)

# Test protected endpoint
curl http://localhost:8000/api/workspaces/current \
  -H "Authorization: Bearer $TOKEN"
```

### Development Mode

For local development without Auth0:

```bash
# Set in .env
BYPASS_AUTH=true

# All requests will use demo workspace
curl http://localhost:8000/api/workspaces/current
```

## 8. Production Checklist

- [ ] Enable MFA for admin users
- [ ] Set up rate limiting rules
- [ ] Configure session timeout (e.g., 8 hours)
- [ ] Enable anomaly detection
- [ ] Set up log streaming to monitoring service
- [ ] Create separate environments (dev, staging, prod)
- [ ] Implement JWT refresh token rotation
- [ ] Add IP whitelist for admin operations

## 9. Troubleshooting

### Common Issues

1. **"No workspace associated with this user"**
   - Check user's app_metadata contains workspace_id
   - Verify Auth0 Action is deployed and active

2. **"Invalid token"**
   - Check AUTH0_DOMAIN matches your tenant
   - Verify audience matches API identifier
   - Ensure token hasn't expired

3. **CORS errors**
   - Add origin to Auth0 application settings
   - Check FastAPI CORS middleware configuration

### Debug Mode

Enable debug logging:

```python
# In auth_middleware.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. Set up Auth0 Organizations for enterprise customers
2. Implement SSO (SAML/OIDC) for enterprise
3. Add social login providers (Google, Microsoft)
4. Set up passwordless authentication options