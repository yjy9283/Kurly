"""python -m snack.run [--offline]  ->  다과_구매목록.xlsx"""
import json, os, sys
from . import crawl, select as sel, export

def main():
    cache = os.path.join(os.path.dirname(__file__), "..", "data", "candidates.json")
    if "--offline" in sys.argv and os.path.exists(cache):
        cands = json.load(open(cache, encoding="utf-8"))
    else:
        cands = crawl.crawl()
    if not cands:
        sys.exit("후보가 0개입니다. 네트워크(api.kurly.com) 접근 또는 data/raw 응답 구조를 확인하세요.")
    picks, warnings = sel.select(cands)
    out = "다과_구매목록.xlsx"
    export.export(picks, cands, warnings, out)
    with open("구매링크.md", "w", encoding="utf-8") as f:
        f.write("# 마켓컬리 구매 링크\n\n")
        for p in sorted(picks, key=lambda p: (not p["must"], p["category"])):
            f.write(f"- [{p['name']}]({p['url']}) — {p['price']:,}원 × {p['qty']}개 = {p['price']*p['qty']:,}원\n")
        f.write(f"\n**합계 {sum(p['price']*p['qty'] for p in picks):,}원**\n")
    print(f"{out} 생성: {len(picks)}품목, 합계 {sum(p['price']*p['qty'] for p in picks):,}원")
    for w in warnings: print("경고:", w)

if __name__ == "__main__":
    main()
