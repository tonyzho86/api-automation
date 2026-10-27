"""商品接口用例 —— 重点练分页与查询参数。"""
import pytest

from framework.core import asserts as A

PRODUCT_LIST_SCHEMA = {
    "type": "object",
    "required": ["total", "page", "size", "items"],
    "properties": {
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "size": {"type": "integer"},
        "items": {"type": "array"},
    },
}


@pytest.mark.smoke
def test_list_default_page(api):
    resp = api.product.list()
    A.assert_status(resp, 200)
    A.assert_schema(resp, PRODUCT_LIST_SCHEMA, "商品列表结构")
    A.assert_field(resp, "total", 12)
    A.assert_field(resp, "page", 1)
    A.assert_field(resp, "size", 5)
    A.assert_true(len(resp.json()["items"]) == 5, "默认每页应返回 5 条")


def test_pagination_pages_do_not_overlap(api):
    ids1 = [p["id"] for p in api.product.list(page=1, size=5).json()["items"]]
    ids2 = [p["id"] for p in api.product.list(page=2, size=5).json()["items"]]
    A.assert_true(set(ids1).isdisjoint(ids2), "第 1、2 页的商品不应重复")
    A.assert_true(ids2[0] == 6, f"第 2 页第一条应该是 id=6,实际 {ids2[0]}")


def test_last_page_returns_remainder(api):
    # 12 条 / 每页 5 -> 第 3 页只剩 2 条
    resp = api.product.list(page=3, size=5)
    A.assert_status(resp, 200)
    A.assert_true(len(resp.json()["items"]) == 2, "最后一页应只有 2 条")


def test_page_beyond_range_is_empty(api):
    resp = api.product.list(page=99, size=5)
    A.assert_status(resp, 200)
    A.assert_field(resp, "items", [])


def test_keyword_filter(api):
    resp = api.product.list(keyword="鼠标", size=50)
    A.assert_status(resp, 200)
    names = [p["name"] for p in resp.json()["items"]]
    A.assert_true(len(names) >= 1, "搜索 '鼠标' 应至少命中 1 条")
    A.assert_true(all("鼠标" in n for n in names),
                  f"结果应都包含 '鼠标',实际 {names}")


@pytest.mark.smoke
def test_product_detail(api):
    resp = api.product.detail(1)
    A.assert_status(resp, 200)
    A.assert_field(resp, "id", 1)
    A.assert_field(resp, "price", 399.0)


def test_product_detail_not_found(api):
    resp = api.product.detail(99999)
    A.assert_status(resp, 404)
