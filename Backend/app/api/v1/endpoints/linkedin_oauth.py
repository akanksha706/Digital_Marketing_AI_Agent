"""LinkedIn OAuth 2.0 Authorization and Callback Flow."""

import logging
import re
import urllib.parse
from pathlib import Path
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["LinkedIn OAuth"])


@router.get("/auth/linkedin/status", summary="Check LinkedIn Connection Status")
async def linkedin_status():
    """Returns current LinkedIn connection status and author URN."""
    connected = bool(settings.LINKEDIN_ACCESS_TOKEN and settings.LINKEDIN_AUTHOR_URN)
    return {
        "connected": connected,
        "author_urn": settings.LINKEDIN_AUTHOR_URN,
        "is_organization": "organization" in (settings.LINKEDIN_AUTHOR_URN or ""),
    }


@router.get("/auth/linkedin/login", summary="Initiate LinkedIn OAuth 2.0 Authorization")
async def linkedin_login():
    """Redirects the user to LinkedIn OAuth 2.0 consent screen."""
    client_id = settings.LINKEDIN_CLIENT_ID or "78mgjvj3dz8ve5"
    redirect_uri = settings.LINKEDIN_REDIRECT_URI or "http://localhost:8000/auth/linkedin/callback"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": "poster_studio_oauth_state",
        "scope": "w_member_social openid profile email",
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)


@router.get("/auth/linkedin/callback", summary="LinkedIn OAuth 2.0 Callback Handler")
async def linkedin_callback(
    code: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
):
    """Handles OAuth 2.0 callback, exchanges code for access token, and resolves Member URN."""
    if error:
        logger.error("LinkedIn OAuth error: %s (%s)", error, error_description)
        return HTMLResponse(
            f"""
            <html>
                <body style="font-family:sans-serif; text-align:center; padding: 50px;">
                    <h2 style="color: #dc2626;">LinkedIn Authorization Failed</h2>
                    <p>{error_description or error}</p>
                    <a href="http://localhost:5173" style="display:inline-block; margin-top:20px; padding:10px 20px; background:#FFC20E; color:#000; text-decoration:none; border-radius:8px; font-weight:bold;">Return to Poster Studio</a>
                </body>
            </html>
            """,
            status_code=400,
        )

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code in callback.")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    redirect_uri = settings.LINKEDIN_REDIRECT_URI or "http://localhost:8000/auth/linkedin/callback"

    client_id = settings.LINKEDIN_CLIENT_ID
    client_secret = settings.LINKEDIN_CLIENT_SECRET

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            # 1. Exchange code for access token
            token_res = await client.post(token_url, data=data)
            if token_res.status_code != 200:
                logger.error("Failed to exchange code: %s", token_res.text)
                return HTMLResponse(
                    f"""
                    <html>
                        <body style="font-family:sans-serif; text-align:center; padding: 50px;">
                            <h2 style="color: #dc2626;">Failed to Retrieve Access Token</h2>
                            <pre style="background:#f1f5f9; padding:15px; border-radius:8px; text-align:left; max-width:600px; margin:0 auto;">{token_res.text}</pre>
                            <a href="http://localhost:5173" style="display:inline-block; margin-top:20px; padding:10px 20px; background:#FFC20E; color:#000; text-decoration:none; border-radius:8px; font-weight:bold;">Return to Poster Studio</a>
                        </body>
                    </html>
                    """,
                    status_code=400,
                )

            token_json = token_res.json()
            access_token = token_json.get("access_token")

            # 2. Query userinfo to resolve Member URN
            userinfo_res = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_name = "LinkedIn Member"
            author_urn = ""
            if userinfo_res.status_code == 200:
                user_data = userinfo_res.json()
                user_sub = user_data.get("sub")
                user_name = user_data.get("name", "LinkedIn Member")
                if user_sub:
                    author_urn = f"urn:li:person:{user_sub}"

        # 3. Update in-memory settings
        settings.LINKEDIN_ACCESS_TOKEN = access_token
        if author_urn:
            settings.LINKEDIN_AUTHOR_URN = author_urn

        # 4. Save to Backend/.env
        for env_file in [
            Path(__file__).resolve().parents[4] / ".env",
            Path(__file__).resolve().parents[3] / ".env",
            Path("Backend/.env"),
            Path(".env"),
        ]:
            if env_file.exists():
                txt = env_file.read_text(encoding="utf-8")
                txt = re.sub(r"LINKEDIN_ACCESS_TOKEN=.*", f"LINKEDIN_ACCESS_TOKEN={access_token}", txt)
                if author_urn:
                    txt = re.sub(r"LINKEDIN_AUTHOR_URN=.*", f"LINKEDIN_AUTHOR_URN={author_urn}", txt)
                env_file.write_text(txt, encoding="utf-8")
                logger.info("Updated LinkedIn credentials in %s", env_file)

        return HTMLResponse(
            f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>LinkedIn Connected - 42 WORKS Poster Studio</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                            background: #f8fafc;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                        }}
                        .card {{
                            background: white;
                            border: 1px solid #e2e8f0;
                            border-radius: 24px;
                            padding: 40px;
                            max-width: 480px;
                            text-align: center;
                            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
                        }}
                        .badge {{
                            width: 60px;
                            height: 60px;
                            background: #ecfdf5;
                            color: #059669;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 28px;
                            margin: 0 auto 20px;
                            border: 2px solid #a7f3d0;
                        }}
                        h1 {{ font-size: 22px; color: #0f172a; margin-bottom: 8px; }}
                        p {{ font-size: 14px; color: #64748b; line-height: 1.5; margin-bottom: 24px; }}
                        .info {{
                            background: #f1f5f9;
                            border-radius: 12px;
                            padding: 12px;
                            font-size: 12px;
                            font-family: monospace;
                            color: #334155;
                            word-break: break-all;
                            margin-bottom: 24px;
                        }}
                        .btn {{
                            background: #FFC20E;
                            color: #0f172a;
                            text-decoration: none;
                            padding: 12px 28px;
                            border-radius: 12px;
                            font-weight: 700;
                            font-size: 13px;
                            display: inline-block;
                            transition: all 0.2s;
                        }}
                        .btn:hover {{ background: #e6ad0a; transform: translateY(-1px); }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="badge">&#10003;</div>
                        <h1>LinkedIn Connected Successfully!</h1>
                        <p>Authenticated as <strong>{user_name}</strong>.<br>Poster Studio can now dispatch live social posts directly to your LinkedIn feed.</p>
                        <div class="info">
                            Author URN: {author_urn or "urn:li:person:connected"}
                        </div>
                        <a href="http://localhost:5173" class="btn">Return to Poster Studio</a>
                    </div>
                </body>
            </html>
            """
        )
    except Exception as e:
        logger.error("Exception during LinkedIn callback: %s", str(e))
        return HTMLResponse(
            f"""
            <html>
                <body style="font-family:sans-serif; text-align:center; padding: 50px;">
                    <h2 style="color: #dc2626;">Error Processing LinkedIn Callback</h2>
                    <p>{str(e)}</p>
                    <a href="http://localhost:5173" style="display:inline-block; margin-top:20px; padding:10px 20px; background:#FFC20E; color:#000; text-decoration:none; border-radius:8px; font-weight:bold;">Return to Poster Studio</a>
                </body>
            </html>
            """,
            status_code=500,
        )
