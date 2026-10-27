"""被测系统(SUT)的数据层 —— 纯内存,进程重启即重置。

注意:这是"被测试的系统"的一部分,不是你测试框架的一部分。
真实工作里服务端代码你通常拿不到;这里把它公开出来,是为了让你
能看懂每个接口背后的逻辑(以及那些故意留下的缺陷)。
"""
from __future__ import annotations

import itertools
import secrets

# ------------------------------------------------------------------ 用户
# 两个账号:普通用户 alice / 管理员 admin。
USERS: dict[str, dict] = {
    "alice": {"id": 1, "username": "alice", "password": "123456",
              "role": "user", "nickname": "爱丽丝"},
    "admin": {"id": 2, "username": "admin", "password": "admin123",
              "role": "admin", "nickname": "管理员"},
}


def public_user(user: dict) -> dict:
    """对外返回的用户信息:去掉密码。"""
    return {k: v for k, v in user.items() if k != "password"}


# ------------------------------------------------------------------ 商品
_PRODUCT_SEED = [
    ("机械键盘", 399.00), ("人体工学椅", 1299.00), ("显示器支架", 159.00),
    ("降噪耳机", 899.00), ("无线鼠标", 129.00), ("桌面台灯", 219.00),
    ("笔记本支架", 89.00), ("USB 扩展坞", 259.00), ("硬盘盒", 99.00),
    ("六类网线", 29.00), ("键帽套装", 149.00), ("超大鼠标垫", 39.00),
]

PRODUCTS: dict[int, dict] = {
    i + 1: {"id": i + 1, "name": name, "price": price, "stock": 20, "on_sale": True}
    for i, (name, price) in enumerate(_PRODUCT_SEED)
}

# ------------------------------------------------------------------ 会话
TOKENS: dict[str, str] = {}          # token -> username


def issue_token(username: str) -> str:
    token = secrets.token_hex(16)
    TOKENS[token] = username
    return token


def user_by_token(token: str) -> dict | None:
    username = TOKENS.get(token)
    return USERS.get(username) if username else None


# ------------------------------------------------------------------ 购物车
CARTS: dict[str, dict[int, int]] = {}   # username -> {product_id: qty}


def cart_of(username: str) -> dict[int, int]:
    return CARTS.setdefault(username, {})


# ------------------------------------------------------------------ 优惠券
COUPONS = {"SAVE20": {"threshold": 100.0, "amount": 20.0}}   # 满 100 减 20


# ------------------------------------------------------------------ 订单
ORDERS: dict[int, dict] = {}
_order_seq = itertools.count(1001)


def next_order_id() -> int:
    return next(_order_seq)


def order_amount(items: list[tuple[dict, int]],
                 coupon_code: str | None) -> tuple[float, float]:
    """算钱:返回 (商品总额, 应付金额)。

    items 是 [(商品 dict, 数量), ...]。
    """
    total = round(sum(product["price"] * qty for product, qty in items), 2)

    discount = 0.0
    coupon = COUPONS.get(coupon_code) if coupon_code else None
    if coupon:
        # ↓↓↓ BUG-5:优惠券应该是"订单级"只减一次,这里却对每个商品行都减了一次。
        #     买 2 种商品用 SAVE20,会被减 40 而不是 20。
        for _ in items:
            if total >= coupon["threshold"]:
                discount += coupon["amount"]

    payable = round(total - discount, 2)
    return total, payable


# ------------------------------------------------------------------ 重置
def reset() -> None:
    """把内存数据恢复成初始状态(测试用例之间做隔离用)。"""
    global PRODUCTS
    PRODUCTS = {
        i + 1: {"id": i + 1, "name": name, "price": price,
                "stock": 20, "on_sale": True}
        for i, (name, price) in enumerate(_PRODUCT_SEED)
    }
    TOKENS.clear()
    CARTS.clear()
    ORDERS.clear()
