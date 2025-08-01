#!/usr/bin/env python3
import time
import httpx
from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict

class PortSettings(BaseSettings):
    """Settings for Port API authentication and configuration."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    PORT_BASE_URL: str = "https://api.port.io/v1"
    PORT_CLIENT_ID: str
    PORT_CLIENT_SECRET: str
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._access_token = None
        self._token_expiry = 0  # Unix timestamp when token expires
        self._buffer_seconds = 60  # Buffer time before expiry to refresh token
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get headers for API requests, including authorization."""
        if not self._access_token:
            raise ValueError("Access token not obtained. Call get_access_token() first.")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }
    
    @property
    def token_expired(self) -> bool:
        """Check if the token has expired or will expire soon."""
        # Return True if token will expire within buffer period
        return time.time() + self._buffer_seconds >= self._token_expiry
    
    async def get_access_token(self, client: httpx.AsyncClient) -> str:
        """Obtain an access token from Port API using client credentials."""
        # If we already have a valid token, return it
        if self._access_token and not self.token_expired:
            return self._access_token
            
        url = f"{self.PORT_BASE_URL}/auth/access_token"
        payload = {
            "clientId": self.PORT_CLIENT_ID,
            "clientSecret": self.PORT_CLIENT_SECRET
        }
        
        try:
            print(f"Requesting token from {url}")
            response = await client.post(url, json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Auth error: {response.text}")
                raise ValueError(f"Failed to obtain access token: {response.text}")
                
            data = response.json()
            self._access_token = data.get("accessToken")
            if not self._access_token:
                raise ValueError("Access token not found in response")
                
            # Set token expiry time
            expires_in = data.get("expiresIn", 3600)  # Default to 1 hour if not specified
            self._token_expiry = time.time() + expires_in
                
            print("✅ Successfully obtained access token (expires in", expires_in, "seconds)")
            return self._access_token
            
        except Exception as e:
            print(f"❌ Error during token request: {str(e)}")
            raise ValueError(f"Failed to obtain access token: {str(e)}")
