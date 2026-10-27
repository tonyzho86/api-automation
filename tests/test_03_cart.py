"""购物车接口用例。"""
import pytest

from framework.core import asserts as A


@pytest.mark.smoke
def test_add_to_cart(api, token):
    resp = api.cart.add(1, 2, token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "total_amount", 798.0)
    A.assert_field(resp, "items.0.product_id", 1)
    A.assert_field(resp, "items.0.quantity", 2)
    A.assert_field(resp, "items.0.subtotal", 798.0)


def test_add_same_product_accumulates(api, token):
    api.cart.add(1, 1, token=token)
    resp = api.cart.add(1, 2, token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "items.0.quantity", 3)


def test_view_cart(api, token):
    api.cart.add(5, 1, token=token)
    resp = api.cart.view(token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "total_amount", 129.0)


def test_remove_from_cart(api, token):
    api.cart.add(1, 1, token=token)
    resp = api.cart.remove(1, token=token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "items", [])


def test_add_nonexistent_product(api, token):
    resp = api.cart.add(99999, 1, token=token)
    A.assert_status(resp, 404)


def test_cart_requires_login(api):
    resp = api.cart.add(1, 1)
    A.assert_status(resp, 401)


def test_cart_isolated_between_users(api, token, admin_token):
    """alice 加的东西,不该出现在 admin 的购物车里。"""
    api.cart.add(1, 1, token=token)
    resp = api.cart.view(token=admin_token)
    A.assert_status(resp, 200)
    A.assert_field(resp, "items", [])
