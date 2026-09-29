"""후보에서 예산 내 구매 목록을 선정한다."""
import math
from . import config as C


def _ok(p):
    if p["sold_out"] or not (C.MIN_UNIT_PRICE <= p["price"] <= C.MAX_UNIT_PRICE): return False
    if any(w in p["name"] for w in C.EXCLUDE_WORDS): return False
    if p["reviews"] is not None and p["reviews"] < C.MIN_REVIEWS: return False
    return True


def _score(p):
    r = p["reviews"] if p["reviews"] is not None else 50
    return math.log1p(r) + p["discount_rate"] / 20


def _match(p, m):
    n = p["name"].replace(" ", "")
    if not all(w.replace(" ", "") in n for w in m["name_must_include"]): return False
    any_ = m.get("name_any_include")
    return not any_ or any(w in n for w in any_)


def select(cands):
    cands = [p for p in cands if _ok(p)]
    picks, warnings, used = [], [], set()

    for m in C.MUST_HAVE:
        pool = sorted((p for p in cands if _match(p, m)), key=lambda p: -_score(p))
        if not pool:
            warnings.append(f"필수품목 '{m['label']}' 검색 결과 없음/품절 - 수동 확인 필요"); continue
        p = pool[0]; used.add(p["no"])
        picks.append({**p, "category": "필수", "qty": m["qty"], "must": True, "label": m["label"]})

    for cat, cfg in C.CATEGORIES.items():
        pool = sorted((p for p in cands if p["keyword"] in cfg["keywords"] and p["no"] not in used),
                      key=lambda p: -_score(p))
        chosen, seen_first = [], set()
        for p in pool:  # 같은 브랜드/첫 단어 중복 방지 -> 종류 다양화
            key = p["name"].replace("[", " ").replace("]", " ").split()[0]
            if key in seen_first: continue
            seen_first.add(key); chosen.append(p); used.add(p["no"])
            if len(chosen) >= cfg["max_items"]: break
        if not chosen: warnings.append(f"카테고리 '{cat}' 후보 없음"); continue
        per = C.BUDGET * cfg["share"] / len(chosen)
        for p in chosen:
            picks.append({**p, "category": cat, "qty": max(1, min(6, round(per / p["price"]))),
                          "must": False, "label": ""})

    total = lambda: sum(p["price"] * p["qty"] for p in picks)
    # 초과 시 비필수 중 점수 낮은 것부터 감량
    while total() > C.BUDGET:
        opt = [p for p in picks if not p["must"] and p["qty"] > 0]
        if not opt: break
        w = min(opt, key=_score); w["qty"] -= 1
    # 부족 시 점수 높은 비필수부터 증량(최대 8개)
    grew = True
    while total() < C.BUDGET_FLOOR and grew:
        grew = False
        for p in sorted((p for p in picks if not p["must"]), key=lambda p: -_score(p)):
            if p["qty"] < 8 and total() + p["price"] <= C.BUDGET:
                p["qty"] += 1; grew = True
                if total() >= C.BUDGET_FLOOR: break
    picks = [p for p in picks if p["qty"] > 0]
    if total() < C.BUDGET_FLOOR: warnings.append(f"합계 {total():,}원 - 목표 미달, 후보 확대 필요")
    return picks, warnings
