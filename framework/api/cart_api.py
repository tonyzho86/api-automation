"""购物车接口。"""
from __future__ import annotations

from framework.api.base_api import BaseApi


class CartApi(BaseApi):
    PREFIX = "/api/cart"

    def add(self, product_id: int, quantity: int, token: str | None = None):
        return self.client.post(
            f"{self.PREFIX}/items",
            json={"product_id": product_id, "quantity": quantity},
            token=token,
        )

    def view(self, token: str | None = None):
        return self.client.get(self.PREFIX, token=token)

    def remove(self, product_id: int, token: str | None = None):
        return self.client.delete(f"{self.PREFIX}/items/{product_id}", token=token)
