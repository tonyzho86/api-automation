"""HTTP 客户端封装。

用例层**不直接调 requests**,统一走这里。好处:

- 换环境只改 `base_url` 一处
- 每个请求自动打日志 —— 用例挂了,看日志就知道发了什么、服务端回了什么状态
- 自动记录耗时,以后要做性能断言(比如"响应 < 500ms")直接可用
"""
from __future__ import annotations

import logging
import time

import requests

from framework.config import settings

log = logging.getLogger("api")


class ApiClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.BASE_URL).rstrip("/")
        self.timeout = timeout or settings.TIMEOUT
        self.session = requests.Session()

    def request(self, method: str, path: str, *,
                token: str | None = None,
                **kwargs) -> requests.Response:
        """发一个请求。

        token 传了就自动加 `Authorization: Bearer xxx` 头;
        其余 kwargs 原样透传给 requests(如 json= / params= / headers=)。
        """
        url = self.base_url + path
        headers = dict(kwargs.pop("headers", None) or {})
        if token:
            headers["Authorization"] = f"Bearer {token}"

        start = time.perf_counter()
        resp = self.session.request(method, url, headers=headers,
                                    timeout=self.timeout, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        resp.elapsed_ms = round(elapsed_ms, 1)          # 挂在响应对象上,断言时可用

        log.info("%-6s %-42s -> %s  %sms", method, path, resp.status_code, resp.elapsed_ms)
        return resp

    # 便捷方法
    def get(self, path: str, **kw) -> requests.Response:
        return self.request("GET", path, **kw)

    def post(self, path: str, **kw) -> requests.Response:
        return self.request("POST", path, **kw)

    def put(self, path: str, **kw) -> requests.Response:
        return self.request("PUT", path, **kw)

    def delete(self, path: str, **kw) -> requests.Response:
        return self.request("DELETE", path, **kw)
