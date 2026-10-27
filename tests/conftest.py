"""pytest 全局配置与 fixture —— 用例的公共准备工作都放这里。

fixture 就是"用例运行前帮你准备好的东西",用例只管声明"我要什么",
不用关心它是怎么来的。
"""
from __future__ import annotations

import logging

import pytest

from framework.api.auth_api import AuthApi
from framework.api.cart_api import CartApi
from framework.api.order_api import OrderApi
from framework.api.product_api import ProductApi
from framework.config import settings
from framework.core.http_client import ApiClient


def pytest_configure(config):
    """打开请求日志 —— 用例挂了,日志里能看到每个请求的状态码和耗时。"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s",
                        datefmt="%H:%M:%S")


class ApiBundle:
    """把各业务的接口对象打包,用例里写 `api.product.list()` 这样调用。"""

    def __init__(self, client: ApiClient):
        self.auth = AuthApi(client)
        self.product = ProductApi(client)
        self.cart = CartApi(client)
        self.order = OrderApi(client)


@pytest.fixture(scope="session")
def client():
    """整个测试会话共用一个 HTTP 客户端(复用 TCP 连接,跑得快)。"""
    return ApiClient()


@pytest.fixture(autouse=True)
def _reset_sut(client):
    """每条用例开始前把靶场数据重置 —— 用例之间互不污染。"""
    client.post("/api/_test/reset")
    yield


@pytest.fixture
def api(client):
    """接口对象集合。"""
    return ApiBundle(client)


@pytest.fixture
def token(client, _reset_sut):
    """普通用户 alice 的登录 token。"""
    return AuthApi(client).login_token(settings.USER, settings.PASSWORD)


@pytest.fixture
def admin_token(client, _reset_sut):
    """管理员 admin 的登录 token。"""
    return AuthApi(client).login_token(settings.ADMIN, settings.ADMIN_PASSWORD)
