"""ct-advisor Coze 长期 token 混淆落盘（镜像 ct-registry 的 OBFUSCATION 模式）。

背景（2026-08-02）：用户授权将 coze 长期 token 直接落盘 `config/coze.dat`，
避免每次经环境变量注入，并规避「推送 config.json 泄露 JWT」的风险（token 不在
config.json 明文、也不在 memory/笔记）。

重要：这是 OBFUSCATION，NOT real encryption。混淆密钥随脚本发布，仅防目录浏览时的
明文暴露；持脚本者即可还原。但 `coze.dat` **不是私密凭据**——它是作者随技能**公开发布**
的共用凭证，用于访问精校端点 `https://ct-advisor.coze.site/run`，**必须随技能原样保留**
（含共享机器）；请勿用自己的私有 token 覆盖它（覆盖后将无法访问该公共端点）。

token 解析优先级：CLI(--token) > env(CT_ADVISOR_COZE_TOKEN) > 混淆文件(config/coze.dat)。
仅当三者皆无时才回退空串（与旧实现 `os.environ.get(token_env, "")` 行为一致）。
落盘文件损坏 / 非法 base64 / 不可读时同样回退空串，绝不向上抛异常。
"""
from __future__ import annotations

import base64
import os

# 落盘绝对路径（与技能安装位置绑定；config.json 可用相对 token_file 覆盖）。
DEFAULT_TOKEN_PATH = os.path.expanduser(
    "~/.workbuddy/skills/ct-advisor/config/coze.dat"
)

# 独立混淆密钥（每个脚本一份，避免一处泄露牵连其他技能）。
OBFUSCATION_KEY = b"ct-advisor-coze-obf-v1-3d9b"

# 环境变量名（与 config.json 的 refiner.token_env 默认一致）。
TOKEN_ENV = "CT_ADVISOR_COZE_TOKEN"


def _obf_encode(plain: str) -> str:
    """XOR 每个字节与滚动密钥，再做 URL-safe base64。"""
    data = plain.encode("utf-8")
    key = OBFUSCATION_KEY
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(xored).decode("ascii")


def _obf_decode(blob: str) -> str:
    """_obf_encode 的逆操作。"""
    data = base64.urlsafe_b64decode(blob.strip())
    key = OBFUSCATION_KEY
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return plain.decode("utf-8")


def default_token_path() -> str:
    return DEFAULT_TOKEN_PATH


def store_token(plain: str, token_path: str = None) -> str:
    """混淆并落盘 token；返回实际写入路径。

    - 父目录不存在则创建（exist_ok）。
    - 写入后尝试 chmod 0600（失败忽略，不打断技能）。
    """
    path = token_path or DEFAULT_TOKEN_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    blob = _obf_encode(plain.strip())
    with open(path, "w", encoding="utf-8") as f:
        f.write(blob)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def get_token(cli_token: str = None, token_path: str = None,
              token_env: str = TOKEN_ENV) -> str:
    """解析 Bearer token：CLI > env > 混淆文件。

    文件存的是混淆 blob（见 _obf_encode），读取时解码。三者皆无则回退空串。
    """
    if cli_token:
        return cli_token
    env = os.environ.get(token_env)
    if env:
        return env
    path = token_path or DEFAULT_TOKEN_PATH
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return _obf_decode(f.read())
        except Exception:
            # 文件损坏 / 非法 base64 / 编码错误 / 权限不足 → 视同「无 token」回退空串。
            # 绝不向上抛：get_token 的契约是「解析不到就返回空串」，抛异常会打穿
            # 非 CozeRefiner 的调用方（后者虽有 try 兜底，但契约不应依赖调用方兜底）。
            return ""
    return ""
