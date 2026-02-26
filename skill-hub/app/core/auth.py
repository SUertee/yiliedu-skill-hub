from fastapi import Header, HTTPException, Depends
from .settings import settings

def require_api_key(x_api_key: str | None = Header(None)):
    # 不设置 API_KEY 就不启用鉴权
    if not settings.API_KEY:
        return True
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
