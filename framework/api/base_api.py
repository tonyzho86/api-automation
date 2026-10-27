"""接口层基类。

**为什么要单独一层?**
每个业务模块一个类,一个方法 = 一个接口。URL 和参数名只在这里出现一次,
用例里写的是可读的 `api.product.list(page=1, size=5)`。

好处:接口变了(比如 `/api/products` 升级成 `/v2/products`),只改这一处,
几十个用例一行都不用动 —— 这就是"分层"最实际的回报。
"""
from __future__ import annotations

from framework.core.http_client import ApiClient


class BaseApi:
    def __init__(self, client: ApiClient):
        self.client = client
