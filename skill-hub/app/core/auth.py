from fastapi import Header, HTTPException
from .settings import settings

def require_api_key(
    x_api_key: str | None = Header(None),
    authorization: str | None = Header(None),
):
    # 不设置 API_KEY 就不启用鉴权
    if not settings.API_KEY:
        return True

    token = x_api_key.strip() if x_api_key else None
    if not token and authorization:
        auth = authorization.strip()
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()

    if token != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
