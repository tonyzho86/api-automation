"""商品接口。"""
from __future__ import annotations

from framework.api.base_api import BaseApi


class ProductApi(BaseApi):
    PREFIX = "/api/products"

    def list(self, page: int = 1, size: int = 5, keyword: str | None = None):
        params: dict = {"page": page, "size": size}
        if keyword is not None:
            params["keyword"] = keyword
        return self.client.get(self.PREFIX, params=params)

    def detail(self, product_id: int):
        return self.client.get(f"{self.PREFIX}/{product_id}")
