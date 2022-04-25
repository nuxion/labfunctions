from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from nb_workflows.types.security import JWTResponse


class AuthSpec(ABC):
    @abstractmethod
    def encode(self, payload: Dict[str, Any], exp=None, iss=None, aud=None):
        pass

    @abstractmethod
    def decode(
        self, encoded, verify_signature=True, verify_exp=True, iss=None, aud=None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate(
        self,
        token: str,
        required_scopes: Optional[List[str]],
        require_all=True,
        iss=None,
        aud=None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def refresh_token(self, redis, access_token, refresh_token) -> JWTResponse:
        pass

    @abstractmethod
    async def store_refresh_token(self, redis, username: str) -> str:
        pass
