"""
工具注册中心 - RAG 检索版（P0-1）
- @tool 强制要求 disambiguation 字段：何时选它、何时不选相邻工具
- 工具菜单改为按任务语义检索 top-K，不再全量注入
- 兼容旧接口：tool_menu_text() 无参数时退化为分类菜单
"""
import importlib
import inspect
import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger("tools")

_TOOLS: Dict[str, Dict] = {}
_TOOL_EMBEDDINGS: Optional[np.ndarray] = None  # shape: (n_tools, dim)
_TOOL_NAMES: List[str] = []
_EMBEDDING_MODEL = None  # lazy load


def _get_embedder():
    """懒加载 embedding 模型（优先用 sentence-transformers，回退 TF-IDF）"""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        logger.info("Embedding model loaded: paraphrase-multilingual-MiniLM-L12-v2")
        return _EMBEDDING_MODEL
    except Exception as e:
        logger.warning(f"sentence-transformers unavailable, falling back to TF-IDF: {e}")
        from sklearn.feature_extraction.text import TfidfVectorizer
        _EMBEDDING_MODEL = TfidfVectorizer(max_features=512, ngram_range=(1, 2))
        return _EMBEDDING_MODEL


def _rebuild_embeddings():
    """重建工具向量索引"""
    global _TOOL_EMBEDDINGS, _TOOL_NAMES
    if not _TOOLS:
        _TOOL_EMBEDDINGS = None
        _TOOL_NAMES = []
        return
    _TOOL_NAMES = list(_TOOLS.keys())
    texts = [_TOOLS[n].get("search_text", _TOOLS[n]["description"]) for n in _TOOL_NAMES]
    embedder = _get_embedder()
    if hasattr(embedder, "encode"):  # sentence-transformers
        _TOOL_EMBEDDINGS = embedder.encode(texts, normalize_embeddings=True)
    else:  # TF-IDF
        _TOOL_EMBEDDINGS = embedder.fit_transform(texts).toarray()
        # L2 normalize
        norms = np.linalg.norm(_TOOL_EMBEDDINGS, axis=1, keepdims=True)
        _TOOL_EMBEDDINGS = _TOOL_EMBEDDINGS / np.maximum(norms, 1e-10)
    logger.info(f"Tool embeddings rebuilt: {len(_TOOL_NAMES)} tools")


def tool(name: str = "", description: str = "", category: str = "general",
         when_not_to_use: str = "", disambiguation: str = ""):
    """
    装饰器：把一个函数注册为智能体可用工具。
    契约化要求（强制）：
    - name: 动词+对象（如 get_order / list_repos），禁止 tool 结尾
    - description: 一句话功能描述
    - when_not_to_use: 明确的负面边界（如"查询历史价格请用 get_price_history，本工具只返回实时快照"）
    - disambiguation: 与相邻工具的判别说明（必须填，否则报错）
    - params: 用 type/enum 约束，禁止自由文本（除非必要）
    """
    if not disambiguation.strip():
        raise ValueError(f"@tool {name or 'unknown'} 必须提供 disambiguation 字段（与相似工具的区分说明）")

    def decorator(fn: Callable):
        tool_name = name or fn.__name__
        sig = inspect.signature(fn)
        params = {}
        for pname, p in sig.parameters.items():
            params[pname] = {
                "type": "string" if p.annotation in (str, inspect.Parameter.empty) else "other",
                "required": p.default is inspect.Parameter.empty,
                "default": str(p.default) if p.default is not inspect.Parameter.empty else None,
            }
        desc = description or (fn.__doc__ or "").strip().split('\n')[0]
        # 组合搜索文本：description + when_not_to_use + disambiguation
        search_parts = [desc]
        if when_not_to_use:
            search_parts.append(f"何时不该用：{when_not_to_use}")
        search_parts.append(f"判别：{disambiguation}")
        search_text = " | ".join(search_parts)

        _TOOLS[tool_name] = {
            "name": tool_name,
            "description": desc,
            "when_not_to_use": when_not_to_use,
            "disambiguation": disambiguation,
            "search_text": search_text,
            "category": category,
            "func": fn,
            "params": params,
            "usage_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "origin": "builtin" if not getattr(fn, '_dynamic', False) else "generated",
        }
        fn._tool_name = tool_name
        _rebuild_embeddings()
        return fn
    return decorator


def list_tools(category: str = None) -> List[Dict]:
    """列出可用工具（给 LLM 的工具菜单，全量模式，兼容旧调用）"""
    out = []
    for t in _TOOLS.values():
        if category and t["category"] != category:
            continue
        out.append({
            "name": t["name"],
            "description": t["description"],
            "when_not_to_use": t.get("when_not_to_use", ""),
            "disambiguation": t.get("disambiguation", ""),
            "params": t["params"],
            "usage": t["usage_count"],
        })
    return out


def tool_menu_text(task: str = "", top_k: int = 5, max_per_category: int = 5) -> str:
    """
    生成给提示词用的工具清单文本。
    - task 不为空：语义检索 top_k 个最相关工具（RAG 模式）
    - task 为空：退化为分类菜单（兼容旧调用），每类最多 max_per_category 个
    """
    if not _TOOLS:
        return "【可用工具：无】"

    # RAG 检索模式
    if task.strip():
        embedder = _get_embedder()
        if _TOOL_EMBEDDINGS is None:
            _rebuild_embeddings()
        if _TOOL_EMBEDDINGS is not None:
            if hasattr(embedder, "encode"):
                q_vec = embedder.encode([task], normalize_embeddings=True)[0]
            else:
                q_vec = embedder.transform([task]).toarray()[0]
                q_vec = q_vec / max(np.linalg.norm(q_vec), 1e-10)
            sims = _TOOL_EMBEDDINGS @ q_vec
            top_idx = np.argsort(sims)[::-1][:top_k]
            selected = [_TOOL_NAMES[i] for i in top_idx if sims[i] > 0.05]
            if not selected:
                selected = [_TOOL_NAMES[i] for i in top_idx[:3]]  # 兜底取前3
            lines = ["【可用工具（按任务相关性检索）】"]
            for name in selected:
                t = _TOOLS[name]
                params = ", ".join(f"{k}{'?' if not v['required'] else ''}"
                                   for k, v in t["params"].items())
                lines.append(f"- {t['name']}({params}) — {t['description']}")
                if t.get("disambiguation"):
                    lines.append(f"    ↳ 判别：{t['disambiguation']}")
            return "\n".join(lines)

    # 兼容模式：分类菜单
    from collections import defaultdict
    by_cat = defaultdict(list)
    for t in _TOOLS.values():
        by_cat[t["category"]].append(t)
    lines = ["【可用工具（用 [TOOL_CALL] 工具名 参数=值 格式调用）】"]
    for cat in sorted(by_cat):
        tools = sorted(by_cat[cat],
                       key=lambda t: -(t["success_count"] / max(1, t["usage_count"])))
        lines.append(f"[{cat}]")
        for t in tools[:max_per_category]:
            params = ", ".join(f"{k}{'?' if not v['required'] else ''}"
                               for k, v in t["params"].items())
            lines.append(f"- {t['name']}({params}) — {t['description']}")
            if t.get("disambiguation"):
                lines.append(f"    ↳ 判别：{t['disambiguation']}")
    return "\n".join(lines)


def call_tool(name: str, args: Dict[str, Any], timeout: int = 120) -> Dict:
    """执行工具调用，返回 {ok, result, error}"""
    t = _TOOLS.get(name)
    if not t:
        return {"ok": False, "error": f"工具不存在: {name}", "available": list(_TOOLS.keys())}
    try:
        result = t["func"](**args)
        t["usage_count"] += 1
        t["success_count"] += 1
        return {"ok": True, "result": result}
    except Exception as e:
        t["usage_count"] += 1
        t["failure_count"] += 1
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def register_dynamic_tool(code: str) -> Dict:
    """
    动态工具生成：LLM 写一个 Python 工具代码 → 沙箱执行注册 → 立即可用。
    代码必须包含至少一个 @tool 装饰的函数。
    返回 {ok, registered: [...], error}
    """
    dangerous = ['subprocess', 'os.system', 'shutil', 'ctypes', 'socket', 'eval(', 'exec(']
    for d in dangerous:
        if d in code:
            return {"ok": False, "error": f"动态工具禁止使用: {d}"}

    before = set(_TOOLS.keys())
    namespace = {}
    exec(compile(code, "<dynamic_tool>", "exec"), namespace)
    after = set(_TOOLS.keys())
    registered = list(after - before)

    if not registered:
        return {"ok": False, "error": "代码中没有用 @tool 装饰任何函数"}
    for r in registered:
        _TOOLS[r]["origin"] = "generated"
    _rebuild_embeddings()
    return {"ok": True, "registered": registered}


def load_tools_module(path: Path):
    """从文件加载工具模块（tools/*.py 里的 @tool 函数）"""
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger.info(f"工具模块加载: {path.name}")
        return True
    except Exception as e:
        logger.error(f"工具模块加载失败 {path.name}: {e}")
        return False


def auto_discover_tools(tools_dir: Path):
    """扫描 tools/ 目录自动加载所有 @tool 模块"""
    for p in sorted(tools_dir.glob("*.py")):
        if p.name in ("__init__.py",):
            continue
        try:
            if "@tool(" in p.read_text(encoding='utf-8'):
                load_tools_module(p)
        except Exception:
            pass
    _rebuild_embeddings()


def parse_tool_calls(text: str) -> List[Dict]:
    """从 LLM 输出解析 [TOOL_CALL] name arg1=v1 arg2=v2"""
    calls = []
    for m in re.finditer(r'\[TOOL_CALL\]\s*(\w+)\s*(.*)', text):
        name, argstr = m.group(1), m.group(2)
        args = {}
        for pm in re.finditer(r'(\w+)=("[^"]*"|\S+)', argstr):
            k, v = pm.group(1), pm.group(2).strip('"')
            args[k] = v
        calls.append({"name": name, "args": args})
    return calls


def get_tool_schema(name: str) -> Optional[Dict]:
    """获取单个工具的完整 schema（供 ACT 阶段精准注入）"""
    return _TOOLS.get(name)