import os
import secrets
import time

import jwt
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

JWT_SECRET = os.environ["JWT_SECRET"]
# ponytail: single fixed user via env vars, swap for a real user store/IdP if you need more than one account
AUTH_USER = os.environ.get("AUTH_USER", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "changeme")
TOKEN_TTL_SECONDS = 12 * 3600
COOKIE_NAME = "session"

app = FastAPI()

LOGIN_PAGE = """<!doctype html>
<html><body style="font-family:sans-serif;max-width:320px;margin:80px auto">
<h2>Sign in</h2>
<form method="post" action="/login">
<input name="username" placeholder="username" style="display:block;width:100%;margin:8px 0;padding:8px">
<input name="password" type="password" placeholder="password" style="display:block;width:100%;margin:8px 0;padding:8px">
<button type="submit" style="padding:8px 16px">Sign in</button>
{error}
</form></body></html>"""


def make_token(username: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return LOGIN_PAGE.format(error="")


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    valid = secrets.compare_digest(username, AUTH_USER) and secrets.compare_digest(password, AUTH_PASSWORD)
    if not valid:
        return HTMLResponse(
            LOGIN_PAGE.format(error="<p style='color:red'>Invalid credentials</p>"),
            status_code=401,
        )
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(
        COOKIE_NAME,
        make_token(username),
        httponly=True,
        samesite="lax",
        max_age=TOKEN_TTL_SECONDS,
    )
    return resp


@app.get("/verify")
def verify(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return Response(status_code=401)
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return Response(status_code=401)
    return Response(status_code=200)


@app.post("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp
