"""엑셀 생성: 구매목록 / 카테고리요약 / 후보전체.

금액은 수식(=단가*수량)으로 두되 계산된 값도 함께 저장한다(미리보기/모바일 뷰어에서 빈칸·0으로 보이는 문제 방지).
"""
import xlsxwriter
from . import config as C

PURPLE = "#5F0080"


def export(picks, cands, warnings, path):
    wb = xlsxwriter.Workbook(path)
    head = wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": PURPLE, "align": "center", "valign": "vcenter"})
    money = wb.add_format({"num_format": "#,##0"})
    money_b = wb.add_format({"num_format": "#,##0", "bold": True})
    must_txt = wb.add_format({"bg_color": "#FFF2CC"})
    must_money = wb.add_format({"bg_color": "#FFF2CC", "num_format": "#,##0"})
    pct = wb.add_format({"num_format": "0.0%"})
    link = wb.add_format({"font_color": "#0563C1", "underline": 1})
    must_link = wb.add_format({"font_color": "#0563C1", "underline": 1, "bg_color": "#FFF2CC"})

    ws = wb.add_worksheet("구매목록")
    ws.write("A1", "회사 다과 구매 목록 (마켓컬리)", wb.add_format({"bold": True, "font_size": 14}))
    picks = sorted(picks, key=lambda p: (not p["must"], p["category"]))
    first, last = 5, 4 + len(picks)                     # 엑셀 행 번호(1-base)
    total = sum(p["price"] * p["qty"] for p in picks)
    ws.write("A2", "예산"); ws.write("B2", C.BUDGET, money)
    ws.write("C2", "합계"); ws.write_formula("D2", f"=SUM(F{first}:F{last})", money_b, total)
    ws.write("E2", "잔액"); ws.write_formula("F2", "=B2-D2", money_b, C.BUDGET - total)
    for i, c in enumerate(["구분", "카테고리", "상품명", "단가(원)", "수량", "금액(원)", "할인율(%)", "후기수", "링크", "메모"]):
        ws.write(3, i, c, head)
    for r, p in enumerate(picks, first):
        m = p["must"]
        t, mo, lk = (must_txt, must_money, must_link) if m else (None, money, link)
        ws.write(r - 1, 0, "필수" if m else "추천", t)
        ws.write(r - 1, 1, p["category"], t)
        ws.write(r - 1, 2, p["name"], t)
        ws.write_number(r - 1, 3, p["price"], mo)
        ws.write_number(r - 1, 4, p["qty"], t)
        ws.write_formula(r - 1, 5, f"=D{r}*E{r}", mo, p["price"] * p["qty"])
        ws.write_number(r - 1, 6, p["discount_rate"], t)
        ws.write(r - 1, 7, p["reviews"] if p["reviews"] is not None else "", t)
        ws.write_url(r - 1, 8, p["url"], lk, p["url"])
        ws.write(r - 1, 9, "", t)
    for i, w in enumerate([7, 14, 52, 11, 7, 12, 10, 9, 36, 20]):
        ws.set_column(i, i, w)
    ws.freeze_panes(4, 0)
    if warnings:
        ws.write(last + 1, 0, "⚠ " + " / ".join(warnings), wb.add_format({"font_color": "#C00000", "bold": True}))

    s = wb.add_worksheet("카테고리요약")
    for i, c in enumerate(["카테고리", "품목수", "금액(원)", "비중"]):
        s.write(0, i, c, head)
    cats = ["필수"] + list(C.CATEGORIES)
    sums = {c: sum(p["price"] * p["qty"] for p in picks if p["category"] == c) for c in cats}
    cnts = {c: sum(1 for p in picks if p["category"] == c) for c in cats}
    n = len(cats) + 1
    for r, cat in enumerate(cats, 2):
        s.write(r - 1, 0, cat)
        s.write_formula(r - 1, 1, f"=COUNTIF(구매목록!B{first}:B{last},A{r})", None, cnts[cat])
        s.write_formula(r - 1, 2, f"=SUMIF(구매목록!B{first}:B{last},A{r},구매목록!F{first}:F{last})", money, sums[cat])
        s.write_formula(r - 1, 3, f"=C{r}/SUM($C$2:$C${n})", pct, sums[cat] / total if total else 0)
    for i, w in enumerate([30, 8, 14, 8]):
        s.set_column(i, i, w)

    a = wb.add_worksheet("후보전체")
    for i, c in enumerate(["상품번호", "상품명", "가격", "정가", "할인율", "후기수", "품절", "검색어", "링크"]):
        a.write(0, i, c, head)
    rows = sorted(cands, key=lambda p: p["keyword"])
    for r, p in enumerate(rows, 1):
        a.write_row(r, 0, [p["no"], p["name"], p["price"], p["list_price"], p["discount_rate"],
                           p["reviews"] if p["reviews"] is not None else "", "Y" if p["sold_out"] else "", p["keyword"], p["url"]])
    a.autofilter(0, 0, len(rows), 8)
    for i, w in enumerate([10, 60, 10, 10, 8, 8, 6, 16, 36]):
        a.set_column(i, i, w)
    wb.close()
