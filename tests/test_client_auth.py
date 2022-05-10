import httpx

from labfunctions.client.base import AuthFlow
from labfunctions.types.config import SecuritySettings

from .factories import token_generator

settings = SecuritySettings()


def test_client_auth_nbauth():
    tkn = token_generator(settings, username="test")
    a = AuthFlow(
        access_token=tkn,
        refresh_token="test-refresh",
        refresh_url="http://localhost:8000/v1/auth/refresh",
    )

    new_tkn = token_generator(settings, username="test")

    def handler(request):
        if (
            request.method == "POST"
            and request.url == "http://localhost:8000/v1/auth/refresh"
        ):
            return httpx.Response(200, json={"access_token": new_tkn})
        elif request.method == "GET" and request.url == "http://localhost:8000/":
            return httpx.Response(200, json={"text": "hello world"})

        return httpx.Response(404, json={"text": "Not found"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="http://localhost:8000", auth=a, transport=transport)
    r = client.get("/")
    assert r.status_code == 200
    assert client.auth.access_token
