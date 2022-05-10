from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from labfunctions.types.security import JWTResponse


class TokenStoreSpec(ABC):
    @abstractmethod
    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        pass

    @abstractmethod
    async def get(self, key: str) -> Union[str, None]:
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    # @abstractmethod
    # async def validate(self, token: str, user: str) -> bool:
    #     pass

    @staticmethod
    @abstractmethod
    def generate(sign: Optional[str] = None) -> str:
        pass


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
    async def refresh_token(self, access_token, refresh_token) -> JWTResponse:
        pass

    @abstractmethod
    async def store_refresh_token(self, username: str) -> str:
        pass
