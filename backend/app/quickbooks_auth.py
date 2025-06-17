import os, json, time, pathlib
from typing import Dict, Optional
from urllib.parse import urlencode
import requests

TOKEN_PATH = pathlib.Path(__file__).with_name(".qb_token.json")

def get_auth_url() -> str:
    """Generate QuickBooks OAuth2 authorization URL manually"""
    base_url = "https://appcenter.intuit.com/connect/oauth2"
    params = {
        "client_id": os.getenv("QB_CLIENT_ID"),
        "scope": "com.intuit.quickbooks.accounting",
        "redirect_uri": os.getenv("QB_REDIRECT_URI"),
        "response_type": "code",
        "access_type": "offline",
        "state": "finwave_local"
    }
    return f"{base_url}?{urlencode(params)}"

def _save(token_dict: Dict):
    TOKEN_PATH.write_text(json.dumps(token_dict, indent=2))

def _load() -> Optional[Dict]:
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text())
    return None

def exchange_code(auth_code: str, realm_id: str):
    """Exchange authorization code for access token"""
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": os.getenv("QB_REDIRECT_URI")
    }
    
    auth = (os.getenv("QB_CLIENT_ID"), os.getenv("QB_CLIENT_SECRET"))
    
    response = requests.post(token_url, data=data, auth=auth)
    response.raise_for_status()
    
    token_data = response.json()
    token_data["realm_id"] = realm_id  # Store realm_id with token
    token_data["expires_at"] = time.time() + token_data["expires_in"]
    
    _save(token_data)

def ensure_token() -> Optional[Dict]:
    data = _load()
    if not data:
        return None
    
    # Check if token is expired (with 5 min buffer)
    if data.get("expires_at", 0) - time.time() < 300:
        # Refresh token
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": data["refresh_token"]
        }
        
        auth = (os.getenv("QB_CLIENT_ID"), os.getenv("QB_CLIENT_SECRET"))
        
        response = requests.post(token_url, data=refresh_data, auth=auth)
        response.raise_for_status()
        
        new_token = response.json()
        new_token["realm_id"] = data["realm_id"]  # Preserve realm_id
        new_token["expires_at"] = time.time() + new_token["expires_in"]
        
        _save(new_token)
        data = new_token
    
    return data