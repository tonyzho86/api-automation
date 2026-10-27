"""数据驱动用例 —— 逻辑写一遍,场景数据放 YAML。

加一个新场景,不用改一行 Python,只在 data/order_cases.yaml 里加一段。
"""
import yaml
import pytest

from framework.config import settings
from framework.core import asserts as A

with open(settings.DATA_DIR / "order_cases.yaml", encoding="utf-8") as f:
    ORDER_CASES = yaml.safe_load(f)


@pytest.mark.parametrize("case", ORDER_CASES, ids=[c["name"] for c in ORDER_CASES])
def test_order_amount(api, token, case):
    resp = api.order.create(case["items"], coupon_code=case["coupon_code"], token=token)
    A.assert_status(resp, 201)
    A.assert_field(resp, "total_amount", case["expected_total"])
    A.assert_field(resp, "discount", case["expected_discount"])
    A.assert_field(resp, "payable_amount", case["expected_payable"])
