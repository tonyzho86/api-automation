"""被测系统(SUT)—— 一个有缺陷的电商 API。

启动:
    uv run uvicorn sut.app:app --port 18800 --reload

接口文档(FastAPI 自动生成,能直接在页面上点着调):
    http://127.0.0.1:18800/docs

⚠️ 这个服务里故意埋了若干缺陷,专门用来练习"接口测试怎么发现问题"。
   哪些接口、什么缺陷,答案在 sut/BUGS.md —— 建议先自己测,再对答案。
"""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from sut import store

app = FastAPI(
    title="Shop API(接口测试靶场)",
    version="1.0.0",
    description="接口测试实战用的被测系统。**故意含有缺陷**,请勿用于生产。",
)


# ============================================================ 请求体模型
class LoginIn(BaseModel):
    username: str
    password: str


class CartAddIn(BaseModel):
    product_id: int
    quantity: int


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int


class OrderIn(BaseModel):
    items: list[OrderItemIn]
    coupon_code: str | None = None


# ============================================================ 工具
def require_user(authorization: str | None) -> dict:
    """校验 Authorization: Bearer <token>,通过则返回用户,否则 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少或格式错误的 Authorization 头")
    user = store.user_by_token(authorization[7:])
    if user is None:
        raise HTTPException(status_code=401, detail="token 无效或已失效")
    return user


def cart_view(username: str) -> dict:
    cart = store.cart_of(username)
    items, total = [], 0.0
    for pid, qty in cart.items():
        product = store.PRODUCTS[pid]
        subtotal = round(product["price"] * qty, 2)
        total += subtotal
        items.append({
            "product_id": pid, "name": product["name"],
            "price": product["price"], "quantity": qty, "subtotal": subtotal,
        })
    return {"items": items, "total_amount": round(total, 2)}


# ============================================================ 健康检查
@app.get("/api/health", tags=["系统"])
def health():
    return {"status": "ok"}


@app.post("/api/_test/reset", tags=["系统"])
def reset_data():
    """测试专用:把内存数据恢复初始状态,方便用例之间互相隔离。

    真实项目里一般没有这个接口;这里加出来是为了让你写用例时不用手动清场。
    """
    store.reset()
    return {"ok": True}


# ============================================================ 登录
@app.post("/api/login", tags=["认证"])
def login(body: LoginIn):
    user = store.USERS.get(body.username)
    # ↓↓↓ BUG-3:用户名或密码错误时,应该返回 401,这里却返回 200 + token=null。
    #     调用方看着是"成功",只有解包 data["token"] 才发现是空的。
    if user is None or user["password"] != body.password:
        return {"token": None, "user": None}

    token = store.issue_token(body.username)
    return {"token": token, "user": store.public_user(user)}


# ============================================================ 商品
@app.get("/api/products", tags=["商品"])
def list_products(
    page: int = Query(1, description="页码,从 1 开始"),
    size: int = Query(5, description="每页数量"),
    keyword: str | None = Query(None, description="按名称模糊搜索"),
):
    items = [p for p in store.PRODUCTS.values() if p["on_sale"]]
    if keyword:
        items = [p for p in items if keyword in p["name"]]
    total = len(items)

    # ↓↓↓ BUG-1:size 没有做下限校验。传 size=0 时,下面这行会除零 —— 接口直接 500。
    #     正确做法是参数校验失败返回 400。
    total_pages = (total + size - 1) // size
    start = (page - 1) * size
    page_items = items[start:start + size]

    return {"total": total, "page": page, "size": size,
            "total_pages": total_pages, "items": page_items}


@app.get("/api/products/{product_id}", tags=["商品"])
def get_product(product_id: int):
    product = store.PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


# ============================================================ 购物车
@app.post("/api/cart/items", tags=["购物车"])
def add_to_cart(body: CartAddIn, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    if body.product_id not in store.PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")

    # ↓↓↓ BUG-4:没有校验 quantity 必须是正整数。传 0 或负数也会被写进购物车,
    #     导致金额变小甚至为负。正确做法是非法参数返回 400。
    cart = store.cart_of(user["username"])
    cart[body.product_id] = cart.get(body.product_id, 0) + body.quantity
    return cart_view(user["username"])


@app.get("/api/cart", tags=["购物车"])
def view_cart(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    return cart_view(user["username"])


@app.delete("/api/cart/items/{product_id}", tags=["购物车"])
def remove_from_cart(product_id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    cart = store.cart_of(user["username"])
    if product_id not in cart:
        raise HTTPException(status_code=404, detail="购物车里没有该商品")
    cart.pop(product_id)
    return cart_view(user["username"])


# ============================================================ 订单
@app.post("/api/orders", status_code=201, tags=["订单"])
def create_order(
    body: OrderIn,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    user = require_user(authorization)
    if not body.items:
        raise HTTPException(status_code=400, detail="订单商品不能为空")

    # ↓↓↓ BUG-6:idempotency_key 收下了却完全没用。带同一个幂等键重复提交,
    #     会生成两笔订单 —— 用户点两次"提交"就付两次钱。
    resolved: list[tuple[dict, int]] = []
    for item in body.items:
        product = store.PRODUCTS.get(item.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"商品 {item.product_id} 不存在")
        resolved.append((product, item.quantity))

    total, payable = store.order_amount(resolved, body.coupon_code)
    order_id = store.next_order_id()
    order = {
        "id": order_id,
        "owner": user["username"],
        "status": "created",
        "items": [
            {"product_id": p["id"], "name": p["name"],
             "price": p["price"], "quantity": q}
            for p, q in resolved
        ],
        "total_amount": total,
        "discount": round(total - payable, 2),
        "payable_amount": payable,
        "coupon_code": body.coupon_code,
    }
    store.ORDERS[order_id] = order
    return order


@app.get("/api/orders", tags=["订单"])
def list_my_orders(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    mine = [o for o in store.ORDERS.values() if o["owner"] == user["username"]]
    return {"items": mine}


@app.get("/api/orders/{order_id}", tags=["订单"])
def get_order(order_id: int):
    # ↓↓↓ BUG-2:既没校验登录态,也没校验订单归属。任何人凭一个订单号就能看到别人的订单。
    #     对比下面的 cancel_order —— 那个是校验了归属的,同一个资源两套标准。
    order = store.ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@app.delete("/api/orders/{order_id}", tags=["订单"])
def cancel_order(order_id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    order = store.ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order["owner"] != user["username"]:
        raise HTTPException(status_code=403, detail="无权操作他人订单")
    order["status"] = "cancelled"
    return {"id": order_id, "status": "cancelled"}
