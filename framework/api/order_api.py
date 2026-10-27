"""订单接口。"""
from __future__ import annotations

from framework.api.base_api import BaseApi


class OrderApi(BaseApi):
    PREFIX = "/api/orders"

    def create(self, items: list[dict], coupon_code: str | None = None,
               token: str | None = None, idempotency_key: str | None = None):
        """items 形如 [{"product_id": 1, "quantity": 2}]。"""
        body: dict = {"items": items}
        if coupon_code is not None:
            body["coupon_code"] = coupon_code
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self.client.post(self.PREFIX, json=body, token=token, headers=headers)

    def detail(self, order_id: int, token: str | None = None):
        return self.client.get(f"{self.PREFIX}/{order_id}", token=token)

    def my_list(self, token: str | None = None):
        return self.client.get(self.PREFIX, token=token)

    def cancel(self, order_id: int, token: str | None = None):
        return self.client.delete(f"{self.PREFIX}/{order_id}", token=token)
