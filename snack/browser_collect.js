// 사용법: https://www.kurly.com 을 열고 F12 > Console 에 이 파일 전체를 붙여넣고 Enter.
// 끝나면 candidates.json 이 다운로드됩니다. 그 파일을 data/candidates.json 에 넣거나 채팅에 첨부하세요.
(async () => {
  const kws = ["사브레","모리나가 밀크캬라멜","모리나가 밀크카라멜","밀크 카라멜 일본",
    "쿠키","비스킷","버터쿠키","초콜릿","일본 초콜릿","젤리 캔디","스낵 과자","일본 과자","감자칩",
    "견과 소포장","하루견과","건망고","에너지바","그래놀라바","프로틴바","마들렌","파운드케이크","휘낭시에",
    "티백","드립백 커피","스틱커피"];
  const num = v => { if (v == null) return null; if (typeof v === "number") return v;
    const s = String(v).replace(/[,+]/g, ""); return s.endsWith("만") ? parseFloat(s) * 1e4 : (/^\d+$/.test(s) ? +s : null); };
  const out = {}, walk = (o, kw) => {
    if (Array.isArray(o)) return o.forEach(x => walk(x, kw));
    if (o && typeof o === "object") {
      if ("no" in o && "name" in o && ("sales_price" in o || "discounted_price" in o)) {
        const sale = o.sales_price || 0, price = o.discounted_price || sale;
        out[o.no] ??= { no: o.no, name: o.name, short_desc: o.short_description || "", price: +price, list_price: +sale,
          discount_rate: o.discount_rate || 0, reviews: num(o.review_count), sold_out: !!o.is_sold_out,
          url: "https://www.kurly.com/goods/" + o.no, image: o.product_vertical_medium_url || "", keyword: kw };
        return;
      }
      Object.values(o).forEach(v => walk(v, kw));
    }
  };
  for (const kw of kws) for (const p of [1, 2]) {
    try {
      const r = await fetch(`https://api.kurly.com/search/v4/sites/market/normal-search?keyword=${encodeURIComponent(kw)}&page=${p}&sorted_type=0`);
      walk(await r.json(), kw); console.log(kw, p, Object.keys(out).length);
    } catch (e) { console.warn("실패", kw, p, e); }
    await new Promise(r => setTimeout(r, 1200));
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(Object.values(out), null, 1)], { type: "application/json" }));
  a.download = "candidates.json"; a.click();
  console.log("완료:", Object.keys(out).length, "개");
})();
