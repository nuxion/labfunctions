import pytest
from sanic import Sanic, response

from nb_workflows.auth import NBAuthStandalone, ProjectClaim, scope_extender_sync
from nb_workflows.types.users import UserData

from .factories import create_user_model


@pytest.mark.asyncio
async def test_auth_authenticate(async_session, sanic_app):
    user_pass = {"username": "admin_test", "password": "meolvide"}
    req, res = await sanic_app.asgi_client.post("/auth", json=user_pass)

    assert res.status == 200
    assert res.json.get("access_token")


def test_auth_NBAuthStandalone():
    um = create_user_model()
    nb = NBAuthStandalone(
        secret="This is a secret test",
        custom_claims=[ProjectClaim()],
        add_scopes_to_payload=scope_extender_sync,
    )

    ud = UserData.from_model(um)
    p = nb.generate_access_token(ud)
    decoded = nb.decode(p)

    assert "projects" in decoded.keys()
