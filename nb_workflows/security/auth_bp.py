from sanic import Blueprint, Request
from sanic.response import empty, json, stream
from sanic_ext import openapi

from nb_workflows.errors.security import (
    AuthValidationFailed,
    MissingAuthorizationHeader,
    WebAuthFailed,
)
from nb_workflows.security import get_auth, get_authenticate, protected
from nb_workflows.types.security import JWTResponse, UserLogin

auth_bp = Blueprint("auth_api", url_prefix="auth", version="v1")


@auth_bp.post("/login")
@openapi.response(200, {"application/json": JWTResponse})
@openapi.response(403, dict(msg=str), "Not Found")
@openapi.body(UserLogin)
async def login_handler(request):
    auth = get_auth()
    authenticate = get_authenticate()
    try:
        user = await authenticate(request)
    except AuthValidationFailed:
        raise WebAuthFailed()
    encoded = auth.encode({"usr": user.username, "scopes": user.scopes.split(",")})

    rtkn = await auth.store_refresh_token(request.ctx.web_redis, user.username)
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
    if not request.app.config.ALLOW_REFRESH:
        return json(dict(msg="Not found"), 404)

    old_token = JWTResponse(**request.json)
    redis = request.ctx.web_redis
    auth = get_auth()
    try:
        jwt_res = await auth.refresh_token(
            redis, old_token.access_token, old_token.refresh_token
        )
        return json(jwt_res.dict(), 200)
    except AuthValidationFailed():
        raise WebAuthFailed()
