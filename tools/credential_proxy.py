"""
凭证代理 (Credential Proxy) - P0 安全结构隔离
原则：Agent 拿到的不是凭证本身，而是只能用于特定白名单操作的受限工具。
- 凭证存储在 secrets/credentials.yaml（chmod 600，不在 Agent 可写目录树内被引用）
- 本模块加载凭证，仅通过 @tool 暴露白名单操作
- 任何工具返回中不得包含完整凭证（一律 mask）
- 网络出口仅限白名单域名
"""
import json
import logging
import re
from pathlib import Path

import httpx
import yaml

from tool_registry import tool

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent.parent
CREDS_FILE = BASE / "secrets" / "credentials.yaml"

# 允许的出口域名（最小权限）
ALLOWED_HOSTS = {
    "api.github.com", "github.com",
    "imap.gmail.com",
    "api-m.sandbox.paypal.com", "api-m.paypal.com",
}


def _creds() -> dict:
    if not CREDS_FILE.exists():
        return {}
    return yaml.safe_load(CREDS_FILE.read_text(encoding='utf-8'))


def _mask(s: str, keep: int = 4) -> str:
    if not s or len(s) <= keep:
        return "****"
    return s[:keep] + "****"


def _check_host(url: str) -> bool:
    m = re.match(r'https?://([^/]+)', url)
    if not m:
        return False
    host = m.group(1).split(":")[0]
    return host in ALLOWED_HOSTS or any(host.endswith("." + h) for h in ALLOWED_HOSTS)


# ---------------- GitHub ----------------
@tool(description="GitHub API 调用（token 由代理注入，你看不到也拿不到 token）。"
                  "只能访问 api.github.com。何时不该用：批量爬取全仓库、需要人工身份的操作（删除仓库/改密码）——那些必须 [ASK]。",
      category="github",
      when_not_to_use="批量爬取全仓库、需要人工身份的操作（删除仓库/改密码）——那些必须 [ASK]",
      disambiguation="只做只读/受限写入 GitHub API；如需完整 repo 操作用 github_tool.py 脚本，如需搜索 bounty 用 github_tool.py 的 search_bounties")
def github_api(method: str, endpoint: str) -> str:
    """
    调用 GitHub REST API。
    method: GET/POST/PATCH（PUT/DELETE 禁止，需 [ASK]）
    endpoint: 如 /repos/octocat/hello 或 /user
    """
    c = _creds().get("github", {})
    token = c.get("token")
    if not token:
        return json.dumps({"ok": False, "error": "github token 未配置"}, ensure_ascii=False)
    if method.upper() not in ("GET", "POST", "PATCH"):
        return json.dumps({"ok": False, "error": f"方法 {method} 不在白名单，写删操作需 [ASK]"},
                          ensure_ascii=False)
    url = f"https://api.github.com{endpoint if endpoint.startswith('/') else '/' + endpoint}"
    if not _check_host(url):
        return json.dumps({"ok": False, "error": "endpoint 不在允许域名内"}, ensure_ascii=False)
    try:
        r = httpx.request(method.upper(), url,
                          headers={"Authorization": f"token {token}",
                                   "Accept": "application/vnd.github+json"},
                          timeout=30)
        return json.dumps({"ok": r.status_code < 400, "status": r.status_code,
                           "body": r.text[:3000]}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


@tool(description="查看 GitHub 账号状态（用户名、剩余 API 配额）。何时不该用：需要 token 明文时——永远拿不到。",
      category="github",
      when_not_to_use="需要 token 明文时——永远拿不到",
      disambiguation="只查状态/配额；如需实际 API 调用用 github_api，如需搜索仓库/issue 用 github_tool.py")
def github_status() -> str:
    c = _creds().get("github", {})
    token = c.get("token", "")
    try:
        r = httpx.get("https://api.github.com/rate_limit",
                      headers={"Authorization": f"token {token}"}, timeout=15)
        remaining = r.json().get("resources", {}).get("core", {}).get("remaining", "?")
        return json.dumps({"ok": True, "username": c.get("username"),
                           "api_remaining": remaining}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


# ---------------- 邮箱 ----------------
@tool(description="读取 Gmail 收件箱最新邮件的验证码（IMAP 凭证由代理持有）。"
                  "何时不该用：发信、删除邮件、读非验证码内容——不在白名单。",
      category="email",
      when_not_to_use="发信、删除邮件、读非验证码内容——不在白名单",
      disambiguation="专用于读取验证码；如需发邮件/管理邮箱需单独配置 SMTP 工具")
def email_latest_code() -> str:
    import imaplib
    c = _creds().get("email", {})
    try:
        m = imaplib.IMAP4_SSL(c["imap_host"], c["imap_port"])
        m.login(c["username"], c["password"])
        m.select("INBOX")
        _, msg_ids = m.search(None, "ALL")
        ids = msg_ids[0].split()[-5:]
        codes = []
        for mid in ids:
            _, data = m.fetch(mid, "(RFC822)")
            raw = data[0][1].decode(errors="ignore")
            # 常见验证码格式：4-8位数字或字母数字
            for m2 in re.finditer(r'\b([0-9]{6,8}|[A-Za-z0-9]{6})\b', raw):
                codes.append({"code": m2.group(1), "snippet": raw[:200].replace("\n", " ")})
        m.logout()
        return json.dumps({"ok": True, "candidates": codes[:5]}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


# ---------------- PayPal ----------------
@tool(description="PayPal OAuth 状态检查（sandbox 或 live）。凭证由代理注入。"
                  "何时不该用：任何真实资金操作（创建收款/打款/提现）——live 环境一律必须 [ASK]，此工具只查状态。",
      category="paypal",
      when_not_to_use="任何真实资金操作（创建收款/打款/提现）——live 环境一律必须 [ASK]",
      disambiguation="只做 OAuth/配额状态检查；真实资金操作必须 [ASK] 主人，不提供任何转账/提现工具")
def paypal_status(env: str = "sandbox") -> str:
    """env: sandbox / live。live 仅允许 GET 状态类检查，不做资金操作。"""
    c = _creds().get("paypal", {})
    e = c.get("sandbox" if env == "sandbox" else "live", {})
    if not e:
        return json.dumps({"ok": False, "error": "该环境未配置"}, ensure_ascii=False)
    if not _check_host(e["base_url"]):
        return json.dumps({"ok": False, "error": "域名不在白名单"}, ensure_ascii=False)
    try:
        r = httpx.post(f"{e['base_url'].rstrip('/')}/v1/oauth2/token",
                       data={"grant_type": "client_credentials"},
                       headers={"Authorization": "Basic " +
                                __import__("base64").b64encode(
                                    f"{e['client_id']}:{e['secret']}".encode()).decode(),
                                "Content-Type": "application/x-www-form-urlencoded"},
                       timeout=20)
        ok = r.status_code == 200
        return json.dumps({"ok": ok, "env": env,
                           "client_id_masked": _mask(e["client_id"]),
                           "note": "live 资金操作必须 [ASK] 主人"}, ensure_ascii=False)
    except Exception as ex:
        return json.dumps({"ok": False, "error": str(ex)}, ensure_ascii=False)
