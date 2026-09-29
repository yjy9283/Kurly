"""후보에서 예산 내 구매 목록을 선정한다."""
import math, re
from . import config as C


def grams(name):
    """상품명에서 총 중량(g) 추정. 못 구하면 None."""
    n = name.replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g)\s*[xX*×]\s*(\d+)", n)
    if m: return float(m[1]) * (1000 if m[2] == "kg" else 1) * int(m[3])
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g)\b", n)
    if m: return float(m[1]) * (1000 if m[2] == "kg" else 1)
    return None


def per100(p):
    if p.get("per100"): return p["per100"]
    g = grams(p["name"])
    return p["price"] / g * 100 if g else None


def fav(p):
    n = p["name"].replace(" ", "")
    return any(f in n for f in C.FAVORITES)


def in_cat(p, cfg):
    """검색어로 잡혔거나, 상품명에 검색어(공백 제거)가 들어 있으면 해당 카테고리 후보."""
    n = p["name"].replace(" ", "")
    return p["keyword"] in cfg["keywords"] or any(k.replace(" ", "") in n for k in cfg["keywords"])


def in_cat_name(p, cfg):
    n = p["name"].replace(" ", "")
    return any(k.replace(" ", "") in n for k in cfg["keywords"])


def _ok(p, check_value=True, check_cat=True):
    if p["sold_out"] or not (C.MIN_UNIT_PRICE <= p["price"] <= C.MAX_UNIT_PRICE): return False
    if any(w in p["name"] for w in C.EXCLUDE_WORDS): return False
    if fav(p):
        return True if not check_cat else bool(p.get("cat_names"))
    if any(w in p["name"] for w in C.BAG_SNACK_WORDS): return False
    if check_cat and (p.get("cat_names") or [None])[-1] not in C.ALLOWED_LEAF: return False
    if p["reviews"] is not None and p["reviews"] < C.MIN_REVIEWS: return False
    v = per100(p)
    if check_value and v is not None and v > C.MAX_PER100G: return False
    return True


def _pack_ok(p):
    """개별포장(번들/입/미니박스) 스낵·감자칩: 봉지/카테고리 필터를 건너뛰되 소포장 표기가 있어야 한다."""
    if p["sold_out"] or not (C.MIN_UNIT_PRICE <= p["price"] <= C.MAX_UNIT_PRICE): return False
    if any(w in p["name"] for w in C.EXCLUDE_WORDS): return False
    if p["reviews"] is not None and p["reviews"] < C.MIN_REVIEWS: return False
    return bool(re.search(r"\d+\s*(입|번들|개입|봉)|미니\s*박스|번들|소포장|예감", p["name"]))


def _score(p):
    r = p["reviews"] if p["reviews"] is not None else 50
    v = per100(p)
    value = 0 if v is None else -1.5 * math.log(max(v, 300) / 1500)  # 100g당 1,500원 기준
    wrapped = 1.0 if re.search(r"\d+\s*(입|봉|번들|개입|팩)|개별포장|낱개|번들", p["name"]) else 0  # 낱개 소포장 가점
    return math.log1p(r) + p["discount_rate"] / 20 + value + (2.5 if fav(p) else 0) + wrapped


def _match(p, m):
    n = p["name"].replace(" ", "")
    if not all(w.replace(" ", "") in n for w in m["name_must_include"]): return False
    any_ = m.get("name_any_include")
    return not any_ or any(w in n for w in any_)


def select(cands):
    all_ = cands
    cands = [p for p in cands if _ok(p)]
    picks, warnings, used = [], [], set()

    for m in C.MUST_HAVE:
        pool = sorted((p for p in all_ if _match(p, m) and not p["sold_out"]), key=lambda p: -_score(p))
        if not pool:
            warnings.append(f"필수품목 '{m['label']}' 검색 결과 없음/품절 - 수동 확인 필요"); continue
        p = pool[0]; used.add(p["no"])
        picks.append({**p, "category": "필수", "qty": m["qty"], "must": True, "label": m["label"]})

    for cat, cfg in C.CATEGORIES.items():
        src = [p for p in all_ if _pack_ok(p)] if cfg.get("pack") else cands
        pool = sorted((p for p in src if (in_cat_name(p, cfg) if (cfg.get("pack") or cfg.get("name_only")) else in_cat(p, cfg)) and p["price"] <= cfg.get("max_price", 10**9) and p["no"] not in used),
                      key=lambda p: -_score(p))
        chosen, seen_first = [], {}
        for p in pool:  # 같은 브랜드/첫 단어 중복 방지 -> 종류 다양화
            key = p["name"].replace("[", " ").replace("]", " ").split()[0]
            if seen_first.get(key, 0) >= C.BRAND_LIMIT.get(key, C.BRAND_DEFAULT): continue
            seen_first[key] = seen_first.get(key, 0) + 1; chosen.append(p); used.add(p["no"])
            if len(chosen) >= cfg["max_items"]: break
        if not chosen: warnings.append(f"카테고리 '{cat}' 후보 없음"); continue
        per = C.BUDGET * cfg["share"] / len(chosen)
        for p in chosen:
            picks.append({**p, "category": cat, "qty": max(cfg.get("min_qty", 1), min(C.MAX_QTY, round(per / p["price"]))), "minq": cfg.get("min_qty", 1),
                          "must": False, "label": ""})

    total = lambda: sum(p["price"] * p["qty"] for p in picks)
    # 초과 시 비필수 중 점수 낮은 것부터 감량
    while total() > C.BUDGET:
        opt = [p for p in picks if not p["must"] and p["qty"] > p.get("minq", 1)] or [p for p in picks if not p["must"] and p["qty"] > 1]
        if not opt: break
        w = min(opt, key=_score); w["qty"] -= 1
    # 부족 시 점수 높은 비필수부터 증량
    grew = True
    while total() < C.BUDGET_FLOOR and grew:
        grew = False
        for p in sorted((p for p in picks if not p["must"]), key=lambda p: -_score(p)):
            if p["qty"] < C.GROW_QTY and total() + p["price"] <= C.BUDGET:
                p["qty"] += 1; grew = True
                if total() >= C.BUDGET_FLOOR: break
    picks = [p for p in picks if p["qty"] > 0]
    if total() < C.BUDGET_FLOOR: warnings.append(f"합계 {total():,}원 - 목표 미달, 후보 확대 필요")
    return picks, warnings
