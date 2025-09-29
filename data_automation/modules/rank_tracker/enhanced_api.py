# enhanced_api.py
from dataclasses import dataclass
from typing import Optional, List
import os, time, random, requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

BASE = "https://openapi.naver.com/v1/search/shop.json"

@dataclass
class SearchParams:
    query: str
    start: int = 1
    display: int = 100
    sort: str = "sim"                 # sim|date|asc|dsc
    filter: Optional[str] = None      # 'naverpay'만 허용
    exclude: Optional[List[str]] = None  # ['used','rental','cbshop'] 조합

    def validate(self):
        if not self.query or not self.query.strip():
            raise ValueError("query is required")
        if not (1 <= self.start <= 1000):
            raise ValueError("start must be 1..1000")
        if not (1 <= self.display <= 100):
            raise ValueError("display must be 1..100")
        if self.sort not in ("sim","date","asc","dsc"):
            raise ValueError("sort must be one of sim|date|asc|dsc")
        if self.filter not in (None, "naverpay"):
            raise ValueError("filter must be None or 'naverpay'")
        if self.exclude:
            allowed = {"used","rental","cbshop"}
            bad = set(self.exclude) - allowed
            if bad:
                raise ValueError(f"exclude supports only {allowed}: {bad}")

class NaverShopAPI:
    def __init__(self, client_id=None, client_secret=None, min_delay=0.2, max_delay=0.8, timeout=10, max_retries=5, backoff_factor=0.3):
        # 환경변수 또는 직접 전달된 값 사용
        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Set NAVER_CLIENT_ID / NAVER_CLIENT_SECRET in env or pass directly")

        self.s = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429,500,502,503,504],
            allowed_methods=frozenset(["GET"]),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retry))
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Accept": "application/json",
            "User-Agent": "RankWatch/1.0",
        }
        self.min_delay, self.max_delay, self.timeout = min_delay, max_delay, timeout

    def _jitter(self):
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def search(self, p: SearchParams) -> dict:
        p.validate()
        q = {
            "query": p.query,
            "start": p.start,
            "display": p.display,
            "sort": p.sort,
        }
        if p.filter:
            q["filter"] = p.filter
        if p.exclude:
            q["exclude"] = ":".join(p.exclude)
        self._jitter()
        r = self.s.get(BASE, headers=self.headers, params=q, timeout=self.timeout)
        r.raise_for_status()
        return r.json()