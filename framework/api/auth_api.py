"""认证接口。"""
from __future__ import annotations

from framework.api.base_api import BaseApi


class AuthApi(BaseApi):

    def login(self, username: str, password: str):
        return self.client.post("/api/login",
                                json={"username": username, "password": password})

    def login_token(self, username: str, password: str) -> str:
        """登录并直接返回 token —— 给 fixture 用。"""
        return self.login(username, password).json()["token"]
