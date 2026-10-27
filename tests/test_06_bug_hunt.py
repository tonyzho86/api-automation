"""追 bug 用例 —— 断言的都是"接口**应该**有的正确行为"。

靶场是**故意有缺陷**的,所以默认(不带 -m bug)不会跑这些用例。
主动运行看红灯:

    uv run pytest -m bug

红出来的每一条,就是一个真实缺陷。缺陷清单和根因在 sut/BUGS.md
(建议先自己跑、自己判断,再翻答案)。

把 sut/ 里的代码修好后再跑一遍,全绿 = 缺陷都修掉了 —— 这就是
接口测试的完整闭环:发现 → 定位 → 修复 → 回归。
"""
import pytest
import yaml

from framework.config import settings
from framework.core import asserts as A

with open(settings.DATA_DIR / "login_cases.yaml", encoding="utf-8") as f:
    LOGIN_CASES = yaml.safe_load(f)


@pytest.mark.bug
def test_bug1_pagination_rejects_size_zero(api):
    """BUG-1:size=0 是非法分页参数,应 400;实际服务端 500。"""
    resp = api.product.list(page=1, size=0)
    A.assert_status(resp, 400)


@pytest.mark.bug
def test_bug2_order_detail_requires_login(api, token):
    """BUG-2:读订单详情必须登录;实际不带 token 也能读到别人的订单。"""
    oid = api.order.create([{"product_id": 1, "quantity": 1}], token=token).json()["id"]
    resp = api.order.detail(oid)                 # 故意不带 token
    A.assert_status(resp, 401)


@pytest.mark.bug
def test_bug2_order_detail_denies_other_user(api, token, admin_token):
    """BUG-2:不该能读别人的订单,应 403;实际 admin 也能读到 alice 的订单。"""
    oid = api.order.create([{"product_id": 1, "quantity": 1}], token=token).json()["id"]
    resp = api.order.detail(oid, token=admin_token)
    A.assert_status(resp, 403)


@pytest.mark.bug
@pytest.mark.parametrize("case", LOGIN_CASES, ids=[c["name"] for c in LOGIN_CASES])
def test_bug3_login_status_code(api, case):
    """BUG-3:凭据错误应 401;实际返回 200 + token=null。"""
    resp = api.auth.login(case["username"], case["password"])
    A.assert_status(resp, case["expected_status"])


@pytest.mark.bug
def test_bug4_cart_rejects_negative_quantity(api, token):
    """BUG-4:数量必须为正整数,负数应 400;实际 200 且写进了购物车。"""
    resp = api.cart.add(1, -5, token=token)
    A.assert_status(resp, 400)


@pytest.mark.bug
def test_bug5_coupon_applied_once(api, token):
    """BUG-5:SAVE20 整单只应减 20;两种商品时实际被减了 40。"""
    resp = api.order.create(
        [{"product_id": 1, "quantity": 1}, {"product_id": 2, "quantity": 1}],
        coupon_code="SAVE20", token=token,
    )
    A.assert_status(resp, 201)
    A.assert_field(resp, "discount", 20.0)


@pytest.mark.bug
def test_bug6_order_creation_is_idempotent(api, token):
    """BUG-6:同一幂等键重复提交,只应产生一笔订单;实际产生两笔。"""
    items = [{"product_id": 1, "quantity": 1}]
    r1 = api.order.create(items, token=token, idempotency_key="key-abc-001")
    r2 = api.order.create(items, token=token, idempotency_key="key-abc-001")
    A.assert_true(r2.status_code in (200, 201),
                  f"重复提交的响应码不应是 {r2.status_code}")
    A.assert_true(r1.json()["id"] == r2.json()["id"],
                  f"同一幂等键应返回同一订单,实际得到 {r1.json()['id']} 与 {r2.json()['id']}")
    orders = api.order.my_list(token=token).json()["items"]
    A.assert_true(len(orders) == 1, f"应只创建 1 笔订单,实际 {len(orders)} 笔")
