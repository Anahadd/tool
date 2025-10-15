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

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import config_store
import integrations as integrations_mod

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

# Store for uploaded credentials (temporary)
credentials_store = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>Kalshi Internal - Impressions Tool</h1><p>Frontend not found</p>"


@app.post("/api/upload-credentials")
async def upload_credentials(file: UploadFile = File(...)):
    """Upload Google OAuth credentials JSON file"""
    try:
        content = await file.read()
        
        try:
            credentials_data = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        
        import uuid
        file_id = str(uuid.uuid4())
        
        temp_path = Path(tempfile.gettempdir()) / f"impressions_creds_{file_id}.json"
        temp_path.write_bytes(content)
        
        credentials_store[file_id] = str(temp_path)
        
        return {
            "success": True,
            "file_id": file_id,
            "message": "Credentials uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/connect-sheets")
async def connect_sheets(file_id: str = Form(...)):
    """Authenticate with Google Sheets using uploaded credentials"""
    try:
        if file_id not in credentials_store:
            raise HTTPException(status_code=400, detail="Credentials file not found")
        
        creds_path = credentials_store[file_id]
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        
        token_path = integrations_mod.connect_sheets_oauth(
            scopes=scopes,
            client_secrets_path=creds_path
        )
        
        return {
            "success": True,
            "message": "Successfully connected to Google Sheets",
            "token_path": str(token_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")


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
    spreadsheet: Optional[str] = Form(None),
    worksheet: Optional[str] = Form(None),
    file_id: Optional[str] = Form(None),
    disable_columns: Optional[str] = Form(""),
    override: bool = Form(True),
    start_row: Optional[int] = Form(None),
    end_row: Optional[int] = Form(None)
):
    """Run the sheet update process"""
    try:
        creds_path = None
        if file_id and file_id in credentials_store:
            creds_path = credentials_store[file_id]
        
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
            creds_path=creds_path,
            disabled_columns=disabled_cols,
            override=override,
            start_row=start_row,
            end_row=end_row,
        )
        
        return {
            "success": True,
            "message": "Sheet updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


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


# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


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

