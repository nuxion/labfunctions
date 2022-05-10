from sanic import Blueprint, Request
from sanic.response import empty, json, stream
from sanic_ext import openapi

from labfunctions.security import get_auth, get_authenticate, protected
from labfunctions.types.security import JWTResponse, UserLogin

from .errors import AuthValidationFailed, MissingAuthorizationHeader, WebAuthFailed

auth_bp = Blueprint("auth_api", url_prefix="auth", version="v1")


@auth_bp.post("/login")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.response(403, dict(msg=str), "Not Found")
@openapi.body(UserLogin)
async def login_handler(request):
    auth = get_auth(request)
    authenticate = get_authenticate(request)
    try:
        user = await authenticate(request)
    except AuthValidationFailed:
        raise WebAuthFailed()
    encoded = auth.encode({"usr": user.username, "scopes": user.scopes.split(",")})

    rtkn = await auth.store_refresh_token(user.username)
    return json(JWTResponse(access_token=encoded, refresh_token=rtkn).dict(), 200)


@auth_bp.get("/verify")
@openapi.response(200, {"application/json": JWTResponse})
@protected()
async def verify_handler(request):
    return json(request.ctx.token_data, 200)


@auth_bp.post("/refresh_token")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.body(JWTResponse)
async def refresh_handler(request):
    if not request.app.config.AUTH_ALLOW_REFRESH:
        return json(dict(msg="Not found"), 404)

    at = request.token
    rftkn = request.json.get("refresh_token")
    if not rftkn:
        raise WebAuthFailed()

    old_token = JWTResponse(access_token=at, refresh_token=rftkn)
    # redis = request.ctx.web_redis
    auth = get_auth(request)
    try:
        jwt_res = await auth.refresh_token(
            old_token.access_token, old_token.refresh_token
        )
        return json(jwt_res.dict(), 200)
    except AuthValidationFailed as e:
        print(e)
        raise WebAuthFailed()
