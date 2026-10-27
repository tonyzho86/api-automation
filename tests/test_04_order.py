"""订单接口用例 —— 金额、状态、权限。"""
import pytest

from framework.core import asserts as A


@pytest.mark.smoke
def test_create_order_happy_path(api, token):
    resp = api.order.create([{"product_id": 1, "quantity": 1}], token=token)
    A.assert_status(resp, 201)
    A.assert_field(resp, "status", "created")
    A.assert_field(resp, "owner", "alice")
    A.assert_field(resp, "total_amount", 399.0)
    A.assert_field(resp, "discount", 0.0)
    A.assert_field(resp, "payable_amount", 399.0)


def test_order_requires_login(api):
    resp = api.order.create([{"product_id": 1, "quantity": 1}])
    A.assert_status(resp, 401)


def test_empty_order_rejected(api, token):
    resp = api.order.create([], token=token)
    A.assert_status(resp, 400)


def test_order_with_nonexistent_product(api, token):
    resp = api.order.create([{"product_id": 99999, "quantity": 1}], token=token)
    A.assert_status(resp, 404)


@pytest.mark.smoke
def test_my_order_list(api, token):
    api.order.create([{"product_id": 1, "quantity": 1}], token=token)
    resp = api.order.my_list(token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "items.0.owner", "alice")


def test_order_list_isolated_between_users(api, token, admin_token):
    api.order.create([{"product_id": 1, "quantity": 1}], token=token)
    resp = api.order.my_list(token=admin_token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "items", [])


def test_cancel_own_order(api, token):
    oid = api.order.create([{"product_id": 1, "quantity": 1}], token=token).json()["id"]
    resp = api.order.cancel(oid, token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "status", "cancelled")


def test_cannot_cancel_others_order(api, token, admin_token):
    oid = api.order.create([{"product_id": 1, "quantity": 1}], token=token).json()["id"]
    resp = api.order.cancel(oid, token=admin_token)
    A.assert_status(resp, 403)


def test_order_detail_with_token(api, token):
    oid = api.order.create([{"product_id": 1, "quantity": 1}], token=token).json()["id"]
    resp = api.order.detail(oid, token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "id", oid)
    A.assert_field(resp, "owner", "alice")
