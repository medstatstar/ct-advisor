# 公共凭据配置 —— 随技能包发布。
#
# SkillHub / ClawHub 等平台对打包文件有后缀白名单，.dat / .cfg / .key 等非白名单
# 后缀会被静默剥离，导致已安装技能读不到凭据。统一用 .py 后缀存放公共凭据，
# 不会被过滤删除。
#
# 适用场景：凭据本来就是公开的、随包发布给所有用户共用的（如访问公共精校端点的
# token），不存在"真实凭据不能上公开平台"的问题。
#
# 扩展方式：新增 key 直接在此文件追加一行常量即可（全大写 + 下划线命名）。

# ---------------------------------------------------------------------------
# 公共凭据常量
# ---------------------------------------------------------------------------

# Coze API token（公共凭据，非私有密钥，随包发布）
COZE_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6IjZjODY5MmZjLWZmM2YtNDlkOC05NDE4LTA2OThiNjE3NjRjYyJ9."
    "eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbIkxQQ05WUVpjUjZTSGFhVHdLSVNCYmFtN29lanJhbnhOIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzg1NzQzOTIwLCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjY5NDI5MzIyNTI4MDYzNTE0Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjY5NzExNzM4MzIwNzE1ODAyIn0."
    "aIIuQpDmoYU2mCY7l4_NR3JKOAQuuPGC4_7VGfUCx46y0hLbLTlCnh6c2tDHuafAfSCEAjMAq-54MXw17slB0dEF0rMHe2kVGovX2a3vzA2DqOFx5Wip0zaaKOANpqd-BceWL-I7G3nop_hUPZghhBxbWqiWGfM90dX8-s_pw4xk6RZKI70HjAc6qF_XKvd4imv2_cpwzcPLPLK1U29z-CGHhSxCfQ0YBVwKrtcdUB9HHTrh1vGUgbT2tMZXRoDThO8SGo6ObeUICYqiDNdUBx51sDDhFqDzrV4lOZ_6GIYRurpQDBMYFCYQ5S8TyAf6At33A9ql5zjSfccYCM8WIQ"
)

# 后续新增 key 直接在此追加一行常量即可，例如：
# NEW_SERVICE_KEY = "your-public-key-here"

# ---------------------------------------------------------------------------
# 向后兼容函数（保持旧引用链可用）
# ---------------------------------------------------------------------------

def get_token() -> str:
    """返回 Coze token（明文公共凭据，等价于 COZE_TOKEN 常量）。"""
    return COZE_TOKEN


def default_token_path() -> str:
    """返回 token 落盘路径（向后兼容占位）。"""
    import os
    return os.path.expanduser("~/.workbuddy/skills/ct-advisor/config/coze.dat")


def get_secret(name: str, fallback: str = "") -> str:
    """按名字取公共凭据。目前仅支持 COZE_TOKEN。"""
    return {
        "COZE_TOKEN": COZE_TOKEN,
    }.get(name, fallback)


def store_token(plain: str, token_path: str = None) -> str:
    """混淆并落盘 token（可选覆盖文件）；返回实际写入路径。

    保留此函数仅为向后兼容；实际 token 建议直接内嵌到本文件顶部常量区。
    """
    import base64, os
    OBFUSCATION_KEY = b"ct-advisor-coze-obf-v1-3d9b"
    data = plain.encode("utf-8")
    xored = bytes(b ^ OBFUSCATION_KEY[i % len(OBFUSCATION_KEY)] for i, b in enumerate(data))
    blob = base64.urlsafe_b64encode(xored).decode("ascii")

    path = token_path or default_token_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(blob)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path
