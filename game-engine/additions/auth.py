import secrets
import base64
import binascii
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class BasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, username, password):
        super().__init__(app)
        self.username = username
        self.password = password

    async def dispatch(self, request: Request, call_next):
        # Skip auth for OPTIONS requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized()
        
        try:
            parts = auth_header.split(maxsplit=1)
            if len(parts) != 2:
                return self._unauthorized()

            scheme, credentials = parts
            if scheme.lower() != "basic":
                return self._unauthorized()
            
            decoded_bytes = base64.b64decode(credentials.encode("ascii"))
            decoded = decoded_bytes.decode("utf-8")
            if ":" not in decoded:
                return self._unauthorized()

            username, password = decoded.split(":", 1)
            
            if not (secrets.compare_digest(username, self.username) and 
                    secrets.compare_digest(password, self.password)):
                return self._unauthorized()
        except (binascii.Error, UnicodeDecodeError, ValueError, AttributeError, Exception):
            return self._unauthorized()

        return await call_next(request)

    def _unauthorized(self):
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": "Basic realm='Restricted'"}
        )
