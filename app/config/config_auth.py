import os
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from nylas import Client
from nylas.models.auth import CodeExchangeRequest, URLForAuthenticationConfig
from nylas.models.drafts import EmailName, SendMessageRequest
from pydantic import BaseModel

# Load env variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Nylas Email App")
PORT = 5010

# Session storage (in production, use a proper session store)
sessions: Dict[str, Dict[str, Any]] = {}


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        session_id = os.urandom(16).hex()
        sessions[session_id] = {}

    request.state.session = sessions[session_id]
    response = await call_next(request)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=14 * 24 * 60 * 60,
        samesite="lax",
        secure=False,
    )

    return response


# Initialize Nylas client
nylas = Client(
    api_key=os.environ.get("NYLAS_API_KEY", ""),
    api_uri=os.environ.get("NYLAS_API_URI", ""),
)


# Models
class EmailRequest(BaseModel):
    subject: str
    body: str
    to_email: str


# Dependencies
async def get_grant_id(request: Request) -> str:
    # 1. Check for NYLAS_GRANT_ID in environment
    env_grant_id = os.environ.get("NYLAS_GRANT_ID")
    if env_grant_id:
        return env_grant_id
    # 2. Otherwise, use session
    grant_id = request.state.session.get("grant_id")
    if not grant_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return grant_id


@app.get("/oauth/exchange")
async def authorized(code: str, request: Request):
    exchange_request = CodeExchangeRequest(
        redirect_uri=f"http://localhost:{PORT}/oauth/exchange",
        code=code,
        client_id=os.environ.get("NYLAS_CLIENT_ID", ""),
    )
    exchange = nylas.auth.exchange_code_for_token(exchange_request)
    request.state.session["grant_id"] = exchange.grant_id
    return RedirectResponse(url="/nylas/auth")


@app.get("/nylas/auth")
async def login(request: Request):
    env_grant_id = os.environ.get("NYLAS_GRANT_ID")
    if env_grant_id:
        return {"grant_id": env_grant_id, "source": "env"}
    if not request.state.session.get("grant_id"):
        config = URLForAuthenticationConfig(
            client_id=os.environ.get("NYLAS_CLIENT_ID", ""),
            redirect_uri=f"http://localhost:{PORT}/oauth/exchange",
        )
        url = nylas.auth.url_for_oauth2(config)
        return RedirectResponse(url=url)
    return {"grant_id": request.state.session["grant_id"], "source": "session"}


@app.get("/nylas/recent-emails")
async def recent_emails(grant_id: str = Depends(get_grant_id)):
    try:
        response = nylas.messages.list(grant_id, None)
        messages = response[0]
        return [m.to_dict() for m in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.api_route("/nylas/send-email", methods=["GET"])
async def send_email(
    request: Request,
    email: EmailRequest = Body(None),
    grant_id: str = Depends(get_grant_id),
):
    try:
        body = SendMessageRequest(
            subject="Your Subject Here",
            body="Your Email Here",
            reply_to=[EmailName(name="Name", email=os.environ.get("EMAIL", ""))],
            to=[EmailName(name="Name", email=os.environ.get("EMAIL", ""))],
        )
        message = nylas.messages.send(grant_id, request_body=body).data
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5010)