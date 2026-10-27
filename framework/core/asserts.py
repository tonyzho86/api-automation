"""断言封装。

裸写 `assert resp.status_code == 200` 挂掉时,你只看到一行 `AssertionError`,
还得自己去翻日志找"到底返回了啥"。这里的断言失败会把 **期望值 / 实际值 /
请求地址 / 响应体** 一起打出来 —— 排查时间从几分钟压到几秒。
"""
from __future__ import annotations

import json

import jsonschema


def _body(resp, limit: int = 600) -> str:
    try:
        return json.dumps(resp.json(), ensure_ascii=False)[:limit]
    except Exception:
        return (resp.text or "")[:limit]


def assert_status(resp, expected: int) -> None:
    """断言 HTTP 状态码。"""
    assert resp.status_code == expected, (
        f"\n  状态码不符  期望={expected}  实际={resp.status_code}"
        f"\n  请求        {resp.request.method} {resp.request.url}"
        f"\n  响应体      {_body(resp)}"
    )


def dig(data, path: str):
    """按路径取值: `user.role`、`items.0.name`(列表用下标)。"""
    cur = data
    for part in path.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def assert_field(resp, path: str, expected) -> None:
    """断言响应 JSON 里某个字段的值,支持点号路径。"""
    actual = dig(resp.json(), path)
    assert actual == expected, (
        f"\n  字段 {path} 不符  期望={expected!r}  实际={actual!r}"
        f"\n  响应体  {_body(resp)}"
    )


def assert_schema(resp, schema: dict, name: str = "") -> None:
    """用 JSON Schema 断言响应结构(字段名/类型/必填)。"""
    try:
        jsonschema.validate(resp.json(), schema)
    except jsonschema.ValidationError as exc:
        raise AssertionError(
            f"\n  响应结构不符  {name}  {exc.message}"
            f"\n  出错位置  {'/'.join(str(p) for p in exc.absolute_path)}"
            f"\n  响应体    {_body(resp)}"
        ) from None


def assert_true(cond: bool, msg: str) -> None:
    """断言一个自定义条件,失败时把 msg 打出来。"""
    assert cond, msg
