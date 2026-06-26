"""联网搜索 grounding(P2):与模型解耦的外部搜索基座。

Gemini 是「模型自己边搜边答」;别家没有这能力,改走「先搜→把结果喂给模型综述」。
本模块只负责「搜」这一步:GroundingProvider.search(query) -> [SearchResult]。
两步编排(提议查询→搜索→拼进 prompt→综述)在 OpenAICompatClient 里。

配置:LOEVENT_SEARCH_PROVIDER (bocha/tavily/none) + LOEVENT_SEARCH_API_KEY。
没配 → None;调用方据此显式降级到「无 grounding + 告警」,不静默编造。
"""
import os
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_TIMEOUT = 20.0


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    published_at: str = ""


class GroundingProvider:
    name = "base"

    async def search(self, query: str, top_k: int = 8) -> List[SearchResult]:
        raise NotImplementedError


class BochaSearch(GroundingProvider):
    """博查(国内默认):境内合规直连,返回带网页摘要,中文优。"""
    name = "bocha"
    endpoint = "https://api.bochaai.com/v1/web-search"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def _build_payload(self, query: str, top_k: int) -> Dict[str, Any]:
        return {"query": query, "freshness": "oneYear", "summary": True, "count": top_k}

    @staticmethod
    def _parse(data: Dict[str, Any]) -> List[SearchResult]:
        # 防御式取 data.webPages.value(Bing 同构);各层缺失都退化为空
        pages = (((data or {}).get("data") or {}).get("webPages") or {}).get("value")
        if not pages:
            pages = ((data or {}).get("webPages") or {}).get("value") or []
        results = []
        for page in pages:
            results.append(SearchResult(
                title=page.get("name", "") or page.get("title", ""),
                url=page.get("url", ""),
                snippet=page.get("summary") or page.get("snippet", ""),
                published_at=page.get("datePublished", "") or "",
            ))
        return results

    async def search(self, query: str, top_k: int = 8) -> List[SearchResult]:
        import httpx
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json=self._build_payload(query, top_k),
            )
            resp.raise_for_status()
            return self._parse(resp.json())


class TavilySearch(GroundingProvider):
    """Tavily(海外默认):专为 LLM,返回抽取后正文。"""
    name = "tavily"
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def _build_payload(self, query: str, top_k: int) -> Dict[str, Any]:
        return {"query": query, "max_results": top_k, "search_depth": "basic", "include_answer": False}

    @staticmethod
    def _parse(data: Dict[str, Any]) -> List[SearchResult]:
        results = []
        for item in (data or {}).get("results", []) or []:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                published_at=item.get("published_date", "") or "",
            ))
        return results

    async def search(self, query: str, top_k: int = 8) -> List[SearchResult]:
        import httpx
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json=self._build_payload(query, top_k),
            )
            resp.raise_for_status()
            return self._parse(resp.json())


_BUILDERS = {"bocha": BochaSearch, "tavily": TavilySearch}


def resolve_grounding_provider() -> Optional[GroundingProvider]:
    """读 LOEVENT_SEARCH_PROVIDER 决定外部搜索;没配 / none → None(调用方据此显式降级)。"""
    name = os.environ.get("LOEVENT_SEARCH_PROVIDER", "").strip().lower()
    api_key = os.environ.get("LOEVENT_SEARCH_API_KEY", "").strip()
    if not name or name == "none":
        return None
    builder = _BUILDERS.get(name)
    if builder is None:
        raise RuntimeError(f"未知搜索供应商 '{name}'。可选:{', '.join(sorted(_BUILDERS))} 或 none。")
    if not api_key:
        raise RuntimeError(f"搜索供应商 '{name}' 缺 key:请设 LOEVENT_SEARCH_API_KEY。")
    return builder(api_key)
