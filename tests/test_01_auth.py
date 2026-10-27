"""认证接口用例。

正向场景:能登录、能拿到 token、token 能用于受保护接口。
失败场景(密码错误返回什么)属于缺陷排查,放在 test_06_bug_hunt.py。
"""
import pytest

from framework.config import settings
from framework.core import asserts as A

LOGIN_SCHEMA = {
    "type": "object",
    "required": ["token", "user"],
    "properties": {
        "token": {"type": "string"},
        "user": {
            "type": "object",
            "required": ["id", "username", "role"],
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "role": {"type": "string"},
            },
        },
    },
}


@pytest.mark.smoke
def test_login_success(api):
    resp = api.auth.login(settings.USER, settings.PASSWORD)
    A.assert_status(resp, 200)
    A.assert_schema(resp, LOGIN_SCHEMA, "登录响应结构")
    A.assert_field(resp, "user.username", settings.USER)
    A.assert_field(resp, "user.role", "user")
    A.assert_true(bool(resp.json()["token"]), "登录成功应返回非空 token")


def test_login_response_hides_password(api):
    """安全:响应里绝不能带密码字段。"""
    resp = api.auth.login(settings.USER, settings.PASSWORD)
    A.assert_status(resp, 200)
    A.assert_true("password" not in resp.json()["user"],
                  "登录响应里不应包含 password 字段")


@pytest.mark.smoke
def test_token_works_on_protected_endpoint(api, token):
    resp = api.cart.view(token=token)
    A.assert_status(resp, 200)


def test_missing_token_is_rejected(api):
    resp = api.cart.view()
    A.assert_status(resp, 401)


def test_invalid_token_is_rejected(api):
    resp = api.cart.view(token="this-is-not-a-real-token")
    A.assert_status(resp, 401)
