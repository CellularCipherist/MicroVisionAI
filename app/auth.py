"""
Authentication module for the FastAPI application.
Provides user authentication using HTTP Basic Auth.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from werkzeug.security import check_password_hash
from .config import load_config

# Load configuration
config = load_config()

# Set up HTTP Basic Auth
security = HTTPBasic()

# User credentials (in production, use a more secure method)
users = {config.get('auth.username'): config.get('auth.password')}

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Validate user credentials and return the username if valid.

    Args:
        credentials (HTTPBasicCredentials): The credentials provided in the request.

    Returns:
        str: The username if credentials are valid.

    Raises:
        HTTPException: If credentials are invalid.
    """
    correct_username = credentials.username in users
    correct_password = check_password_hash(users.get(credentials.username, ''), credentials.password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
