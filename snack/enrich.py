"""상위 후보의 상세 정보(카테고리, 100g당 가격, 옵션)를 가져와 candidates에 합친다.
python -m snack.enrich   (data/detail/{no}.json 캐시, 0.7초 간격)"""
import json, os, re, time
import requests
from . import config as C, select as S
from .crawl import HEADERS

DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DETAIL = "https://api.kurly.com/showroom/v2/products/{}"
PER_CATEGORY = 90


def _detail(no):
    os.makedirs(os.path.join(DIR, "detail"), exist_ok=True)
    path = os.path.join(DIR, "detail", f"{no}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    r = requests.get(DETAIL.format(no), headers=HEADERS, timeout=20)
    r.raise_for_status()
    d = r.json().get("data") or {}
    keep = {k: d.get(k) for k in ["volume", "unit_price_text", "category_ids", "category_names",
                                  "deal_products", "is_sold_out", "review_count"]}
    json.dump(keep, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.7)
    return keep


def _per100(d):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g|ml|mL)\s*당\s*([\d,]+)원", d.get("unit_price_text") or "")
    if m:
        unit = float(m[1]) * (1000 if m[2] == "kg" else 1)
        return int(m[3].replace(",", "")) / unit * 100
    return None


def enrich(cands):
    targets = {}
    for cat, cfg in C.CATEGORIES.items():
        ps = [p for p in cands if S._ok(p, check_value=False, check_cat=False) and S.in_cat(p, cfg)]
        for p in sorted(ps, key=lambda p: -S._score(p))[:PER_CATEGORY]:
            targets[p["no"]] = p
    for m in C.MUST_HAVE:
        for p in cands:
            if S._match(p, m): targets[p["no"]] = p
    print(f"상세 조회 대상 {len(targets)}개")
    for i, p in enumerate(targets.values(), 1):
        try:
            d = _detail(p["no"])
        except Exception as e:
            print("실패", p["no"], e); continue
        p["cat_ids"] = d.get("category_ids") or []
        p["cat_names"] = d.get("category_names") or []
        p["per100"] = _per100(d)
        p["options"] = [(x.get("name"), x.get("base_price")) for x in d.get("deal_products") or []]
        p["volume"] = d.get("volume")
        if d.get("is_sold_out"): p["sold_out"] = True
        if i % 50 == 0: print(i)
    return cands


if __name__ == "__main__":
    path = os.path.join(DIR, "candidates.json")
    c = enrich(json.load(open(path, encoding="utf-8")))
    json.dump(c, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
