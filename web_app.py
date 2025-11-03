"""
Web application backend for Impressions Tool
Provides a REST API and serves the frontend
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

import config_store
import integrations as integrations_mod
import firebase_config
import firebase_service

app = FastAPI(title="Kalshi Internal - Impressions Tool", description="TikTok & Instagram stats updater")

# Enable CORS
# In production, set ALLOWED_ORIGINS env var to comma-separated list of domains
# Example: ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for WebSocket connections
active_connections = []

# Store for OAuth flow state (temporary, during OAuth flow)
oauth_flow_state = {}

# Store for OAuth credentials in memory (after successful OAuth)
oauth_credentials = {}  # user_id -> Credentials object


# Firebase ID Token verification
async def verify_firebase_token(authorization: str = Header(None)) -> str:
    """Verify Firebase ID token and return user_id"""
    print(f"DEBUG: verify_firebase_token called, auth header present: {bool(authorization)}")
    
    if not authorization or not authorization.startswith("Bearer "):
        print("ERROR: Missing or invalid authorization header")
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    id_token = authorization.split("Bearer ")[1]
    print(f"DEBUG: ID token length: {len(id_token)}")
    print(f"DEBUG: ID token preview: {id_token[:50]}...")
    
    try:
        decoded_token = firebase_service.verify_id_token(id_token)
        print(f"DEBUG: Token decoded: {bool(decoded_token)}")
        
        if not decoded_token:
            print("ERROR: verify_id_token returned None")
            raise HTTPException(status_code=401, detail="Invalid token - verification failed")
        
        user_id = decoded_token.get('uid')
        print(f"DEBUG: User ID from token: {user_id}")
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Token verification exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>Kalshi Internal - Impressions Tool</h1><p>Frontend not found</p>"


@app.get("/api/oauth-start")
async def oauth_start(user_id: str = Depends(verify_firebase_token)):
    """Start OAuth flow - returns authorization URL OR service account info"""
    try:
        print(f"DEBUG: OAuth start requested for user {user_id}")
        
        # Get credentials.json from Firebase Storage
        credentials_content = await firebase_service.get_credentials(user_id)
        
        print(f"DEBUG: Credentials retrieved: {bool(credentials_content)}")
        
        if not credentials_content:
            print("ERROR: No credentials found in Firebase Storage")
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Credentials not found. Please upload credentials.json first."}
            )
        
        # Check if it's a service account (much simpler!)
        import json
        creds_data = json.loads(credentials_content)
        
        if creds_data.get("type") == "service_account":
            # Service account - no OAuth needed!
            service_email = creds_data.get("client_email", "")
            print(f"DEBUG: Service account detected: {service_email}")
            return {
                "success": True,
                "is_service_account": True,
                "service_email": service_email,
                "message": f"Service account ready! Share your Google Sheet with: {service_email}"
            }
        
        # OAuth flow for web/installed app credentials
        # Save to temporary file for OAuth flow
        temp_path = Path(tempfile.gettempdir()) / f"impressions_creds_{user_id}.json"
        temp_path.write_text(credentials_content)
        print(f"DEBUG: Saved credentials to {temp_path}")
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        
        from google_auth_oauthlib.flow import Flow
        
        # Get the base URL for redirect
        # Use environment variable or default
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        # Remove trailing slash to avoid double slashes
        base_url = base_url.rstrip('/')
        redirect_uri = f"{base_url}/api/oauth-callback"
        
        # Log for debugging
        print(f"DEBUG: BASE_URL={base_url}")
        print(f"DEBUG: redirect_uri={redirect_uri}")
        
        flow = Flow.from_client_secrets_file(
            str(temp_path),
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen every time to ensure callback executes
        )
        
        # Store the state and user_id for callback
        oauth_flow_state[state] = {
            "user_id": user_id,
            "creds_path": str(temp_path)
        }
        
        print(f"DEBUG: OAuth URL generated successfully")
        
        return {
            "success": True,
            "is_service_account": False,
            "auth_url": authorization_url,
            "state": state
        }
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: OAuth start failed: {error_msg}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to start OAuth: {error_msg}"}
        )


@app.get("/api/oauth-callback")
async def oauth_callback(state: str, code: str):
    """Handle OAuth callback from Google"""
    try:
        if state not in oauth_flow_state:
            # Return HTML with error message
            return HTMLResponse(content="""
                <html>
                <body>
                    <h2>OAuth Error</h2>
                    <p>Invalid OAuth state. Please try again.</p>
                    <script>
                        setTimeout(() => {
                            window.opener.postMessage({type: 'oauth_error', message: 'Invalid state'}, '*');
                            window.close();
                        }, 2000);
                    </script>
                </body>
                </html>
            """)
        
        stored_data = oauth_flow_state[state]
        user_id = stored_data["user_id"]
        creds_path = stored_data["creds_path"]
        
        from google_auth_oauthlib.flow import Flow
        
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        # Remove trailing slash to avoid double slashes
        base_url = base_url.rstrip('/')
        redirect_uri = f"{base_url}/api/oauth-callback"
        
        flow = Flow.from_client_secrets_file(
            creds_path,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
            redirect_uri=redirect_uri,
            state=state
        )
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Store credentials in memory for this session
        oauth_credentials[user_id] = creds
        
        # Save OAuth token to Firestore for persistence
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
        
        await firebase_service.store_oauth_token(user_id, token_data)
        
        # Clean up state
        del oauth_flow_state[state]
        
        print(f"DEBUG: Saved OAuth credentials for user_id={user_id}")
        
        # Return HTML that closes the popup and notifies parent window
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 3rem;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
                .checkmark {
                    font-size: 4rem;
                    animation: scale 0.5s ease-in-out;
                }
                @keyframes scale {
                    0% { transform: scale(0); }
                    50% { transform: scale(1.2); }
                    100% { transform: scale(1); }
                }
                h1 { margin: 1rem 0; font-size: 2rem; }
                p { opacity: 0.9; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="checkmark">✓</div>
                <h1>Authentication Successful!</h1>
                <p>You can close this window now.</p>
            </div>
            <script>
                // Notify parent window if opened in popup
                if (window.opener) {
                    window.opener.postMessage({type: 'oauth-success'}, '*');
                    setTimeout(() => window.close(), 2000);
                } else {
                    // If not a popup, redirect to home
                    setTimeout(() => window.location.href = '/', 2000);
                }
            </script>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Failed</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 3rem;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }}
                .error {{ font-size: 4rem; }}
                h1 {{ margin: 1rem 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">✗</div>
                <h1>Authentication Failed</h1>
                <p>{str(e)}</p>
                <p>Please close this window and try again.</p>
            </div>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{type: 'oauth-error', error: '{str(e)}'}}, '*');
                    setTimeout(() => window.close(), 3000);
                }}
            </script>
        </body>
        </html>
        """, status_code=500)


@app.post("/api/set-defaults")
async def set_defaults(
    spreadsheet: str = Form(...),
    worksheet: str = Form(...)
):
    """Save default spreadsheet and worksheet"""
    try:
        integrations_mod.set_sheet_defaults(spreadsheet, worksheet)
        return {
            "success": True,
            "message": "Defaults saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update-sheets")
async def update_sheets(
    user_id: str = Depends(verify_firebase_token),
    spreadsheet: Optional[str] = Form(None),
    worksheet: Optional[str] = Form(None),
    disable_columns: Optional[str] = Form(""),
    override: bool = Form(True),
    start_row: Optional[int] = Form(None),
    end_row: Optional[int] = Form(None)
):
    """Run the sheet update process"""
    print(f"DEBUG: update_sheets called for user {user_id}")
    print(f"DEBUG: spreadsheet={spreadsheet}, worksheet={worksheet}")
    try:
        # Get credentials.json from Firebase Storage
        creds_content = await firebase_service.get_credentials(user_id)
        if not creds_content:
            raise HTTPException(status_code=400, detail="Credentials not found. Please upload credentials.json first.")
        
        # Save to temporary file
        creds_path = Path(tempfile.gettempdir()) / f"impressions_creds_{user_id}.json"
        creds_path.write_text(creds_content)
        
        # Check if using service account (simpler!) or OAuth
        import json
        creds_content = await firebase_service.get_credentials(user_id)
        if not creds_content:
            raise HTTPException(
                status_code=400,
                detail="Please upload credentials.json first (service account or OAuth client)."
            )
        
        creds_data = json.loads(creds_content)
        oauth_creds = None
        service_account_path = None
        
        if creds_data.get("type") == "service_account":
            # Service account - use directly! No OAuth needed
            print(f"DEBUG: Using service account authentication for user {user_id}")
            service_account_path = str(creds_path)
            # oauth_creds stays None, will use service_account_path in integrations
        else:
            # OAuth flow - get credentials from memory or Firestore
            if user_id in oauth_credentials:
                # Already in memory
                oauth_creds = oauth_credentials[user_id]
                print(f"DEBUG: Using OAuth credentials from memory for user {user_id}")
            else:
                # Try to load from Firestore
                token_data = await firebase_service.get_oauth_token(user_id)
                if token_data:
                    # Reconstruct credentials from token data
                    from google.oauth2.credentials import Credentials
                    from google.auth.transport.requests import Request as GoogleRequest
                    oauth_creds = Credentials(
                        token=token_data.get("token"),
                        refresh_token=token_data.get("refresh_token"),
                        token_uri=token_data.get("token_uri"),
                        client_id=token_data.get("client_id"),
                        client_secret=token_data.get("client_secret"),
                        scopes=token_data.get("scopes")
                    )
                    
                    # Check if token is expired and try to refresh
                    if oauth_creds.expired and oauth_creds.refresh_token:
                        try:
                            oauth_creds.refresh(GoogleRequest())
                            print(f"DEBUG: Refreshed expired token for user {user_id}")
                            
                            # Save refreshed token back to Firestore
                            refreshed_token_data = {
                                "token": oauth_creds.token,
                                "refresh_token": oauth_creds.refresh_token,
                                "token_uri": oauth_creds.token_uri,
                                "client_id": oauth_creds.client_id,
                                "client_secret": oauth_creds.client_secret,
                                "scopes": oauth_creds.scopes
                            }
                            await firebase_service.store_oauth_token(user_id, refreshed_token_data)
                            print(f"DEBUG: Saved refreshed token to Firestore for user {user_id}")
                        except Exception as refresh_error:
                            print(f"ERROR: Failed to refresh token for user {user_id}: {refresh_error}")
                            # Clear the bad token
                            if user_id in oauth_credentials:
                                del oauth_credentials[user_id]
                            raise HTTPException(
                                status_code=401,
                                detail="Your Google Sheets connection has expired. Please click 'Connect to Google Sheets' to re-authenticate."
                            )
                    
                    # Cache in memory
                    oauth_credentials[user_id] = oauth_creds
                    print(f"DEBUG: Loaded OAuth credentials from Firestore for user {user_id}")
            
            # Require OAuth authentication if not service account
            if not oauth_creds:
                raise HTTPException(
                    status_code=400, 
                    detail="Please click 'Connect to Google Sheets' button first to authenticate with your Google account."
                )
        
        disabled_cols = []
        if disable_columns:
            disabled_cols = [col.strip().lower() for col in disable_columns.split(',')]
        
        if start_row is not None:
            if start_row < 2:
                raise HTTPException(status_code=400, detail="Start row must be >= 2")
            if end_row is not None and end_row < start_row:
                raise HTTPException(status_code=400, detail="End row must be >= start row")
        
        await integrations_mod.update_sheet_views_likes_comments(
            spreadsheet=spreadsheet,
            worksheet=worksheet,
            creds_path=str(creds_path),
            disabled_columns=disabled_cols,
            override=override,
            start_row=start_row,
            end_row=end_row,
            oauth_creds=oauth_creds,
        )
        
        return {
            "success": True,
            "message": "Sheet updated successfully"
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        error_msg = str(e)
        print(f"ERROR: Validation error in update_sheets: {error_msg}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: Exception in update_sheets: {error_msg}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Update failed: {error_msg}"}
        )


@app.get("/api/check-apify-token")
async def check_apify_token():
    """Check if APIFY_TOKEN is set"""
    token = config_store.load_config("APIFY_TOKEN")
    return {
        "is_set": bool(token and len(token) > 10),
        "message": "APIFY_TOKEN is set" if token else "APIFY_TOKEN not found",
        "token_prefix": token[:15] + "..." if token and len(token) > 15 else ""
    }


@app.post("/api/set-apify-token")
async def set_apify_token(token: str = Form(...)):
    """Set APIFY_TOKEN and save persistently"""
    clean_token = token.strip()
    
    if not clean_token:
        raise HTTPException(status_code=400, detail="Token cannot be empty")
    
    if not clean_token.startswith("apify_api_"):
        raise HTTPException(status_code=400, detail="Invalid token format")
    
    config_store.save_config("APIFY_TOKEN", clean_token)
    
    return {
        "success": True,
        "message": "APIFY_TOKEN saved successfully",
        "token_length": len(clean_token)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    apify_token = config_store.load_config("APIFY_TOKEN")
    return {
        "status": "healthy",
        "service": "kalshi-impressions-tool",
        "apify_configured": bool(apify_token and apify_token.startswith("apify_api_"))
    }


# Mount static files with cache control
static_path = Path(__file__).parent / "static"
if static_path.exists():
    # Disable caching for static files in development to avoid stale JS/CSS
    class NoCacheStaticFiles(StaticFiles):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
        def file_response(self, *args, **kwargs):
            response = super().file_response(*args, **kwargs)
            # Add cache control headers for development
            # In production, consider using versioned URLs instead
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    
    app.mount("/static", NoCacheStaticFiles(directory=str(static_path)), name="static")


def run_server(host: str = None, port: int = None, reload: bool = False):
    """Run the web server"""
    # Get host and port from environment or use defaults
    if host is None:
        host = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    if port is None:
        port = int(os.getenv("PORT", "8000"))
    
    # Configure logging for production
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Kalshi Internal - Impressions Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🌐 Open in browser: http://{host}:{port}
  📡 API docs: http://{host}:{port}/docs
  
  Press CTRL+C to stop the server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    uvicorn.run(
        "web_app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )


if __name__ == "__main__":
    # Enable reload only in development (when PORT env var is not set)
    is_dev = not os.getenv("PORT")
    run_server(reload=is_dev)

