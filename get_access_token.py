import google.auth
from google.oauth2 import service_account
import requests

def get_access_token(service_account_file):
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes
    )
    access_token = credentials.token
    if not access_token:
        # Refresh token
        credentials.refresh(requests.Request())
        access_token = credentials.token
    return access_token
