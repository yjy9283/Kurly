"""컬리 검색 API 크롤러. 결과는 data/raw/*.json 캐시 + data/candidates.json.

사용: python -m snack.crawl
비공식 웹 API라 필드명이 바뀔 수 있어 방어적으로 파싱하고, 원본 응답을 저장한다.
요청 간 1초 이상 대기(서버 부담 최소화).
"""
import json, os, time, hashlib
import requests
from . import config

SEARCH = "https://api.kurly.com/search/v4/sites/market/normal-search"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
           "Accept": "application/json", "Referer": "https://www.kurly.com/"}
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def _get(keyword, page=1):
    os.makedirs(RAW, exist_ok=True)
    key = hashlib.md5(f"{keyword}|{page}".encode()).hexdigest()[:10]
    path = os.path.join(RAW, f"{key}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    r = requests.get(SEARCH, headers=HEADERS, timeout=20,
                     params={"keyword": keyword, "page": page, "sorted_type": 0})
    r.raise_for_status()
    data = r.json()
    json.dump({"keyword": keyword, "page": page, "resp": data}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(1.2)
    return json.load(open(path, encoding="utf-8"))


def _items(resp):
    """응답 구조가 달라져도 상품 리스트를 찾아낸다."""
    d = resp.get("data", resp)
    out = []
    def walk(o):
        if isinstance(o, dict):
            if "no" in o and "name" in o and ("salesPrice" in o or "sales_price" in o):
                out.append(o); return
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(d)
    return out


def _norm(it, keyword):
    sale = it.get("salesPrice") or it.get("sales_price") or 0
    price = it.get("discountedPrice") or it.get("discounted_price") or sale
    return {
        "no": it["no"], "name": it["name"], "short_desc": it.get("shortDescription", ""),
        "price": int(price), "list_price": int(sale),
        "discount_rate": it.get("discountRate") or it.get("discount_rate") or 0,
        "reviews": _num(it.get("reviewCount", it.get("review_count"))),
        "sold_out": bool(it.get("isSoldOut", it.get("is_sold_out"))) or it.get("isPurchaseStatus") is False,
        "url": f"https://www.kurly.com/goods/{it['no']}",
        "image": it.get("productVerticalMediumUrl") or it.get("listImageUrl", ""),
        "keyword": keyword,
    }


def _num(v):
    if v is None: return None
    if isinstance(v, (int, float)): return int(v)
    s = str(v).replace(",", "").replace("+", "").strip()
    if s.endswith("만"): return int(float(s[:-1]) * 10000)
    return int(s) if s.isdigit() else None


def crawl(pages=2):
    kws = {k for c in config.CATEGORIES.values() for k in c["keywords"]}
    for m in config.MUST_HAVE:
        kws.add(m["keyword"]); kws.update(m.get("alt_keywords", []))
    seen = {}
    for kw in sorted(kws):
        for p in range(1, pages + 1):
            try:
                items = _items(_get(kw, p)["resp"])
            except Exception as e:
                print(f"[실패] {kw} p{p}: {e}"); break
            print(f"{kw} p{p}: {len(items)}개")
            if not items: break
            for it in items:
                n = _norm(it, kw)
                seen.setdefault(n["no"], n)
    out = os.path.join(os.path.dirname(RAW), "candidates.json")
    json.dump(list(seen.values()), open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"후보 {len(seen)}개 -> {out}")
    return list(seen.values())


if __name__ == "__main__":
    crawl()
