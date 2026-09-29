# 마켓컬리 회사 다과 50만원 구매 목록 자동화

## 사용법
```bash
pip install requests openpyxl
python -m snack.run            # 컬리 검색 크롤링 -> 선정 -> 다과_구매목록.xlsx
python -m snack.run --offline  # 저장된 data/candidates.json 으로 재선정만
```
- `snack/config.py`: 예산, 인원, 필수품목(사브레, 모리나가 밀크 카라멜), 카테고리 비중/검색어 수정
- 엑셀: `구매목록`(금액·합계·잔액 수식, 필수품목 노란색), `카테고리요약`, `후보전체`(필터)

## 동작
1. 카테고리·필수품목 키워드로 컬리 검색 API 호출(1.2초 간격, `data/raw` 캐시)
2. 품절/과다·과소 가격/후기 부족 제외, 필수품목 우선 확정
3. 카테고리별 예산 비중 안에서 후기·할인율 점수로 브랜드 중복 없이 선정, 수량 조정으로 47만~50만원
4. 엑셀 출력. 필수품목이 없으면 경고 표시

## 주의
- 비공식 웹 API라 필드명이 바뀔 수 있음(방어적 파싱). 결과 없으면 `data/raw/*.json` 확인
- 배송비, 최종 재고/가격은 주문 전 컬리에서 재확인

## 서버에서 컬리 접속이 막힌 경우
kurly.com 을 연 브라우저 콘솔에 `snack/browser_collect.js` 를 붙여넣으면 `candidates.json` 이 내려받아집니다.
`data/candidates.json` 으로 저장 후 `python -m snack.run --offline`.
