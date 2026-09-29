"""다과 구매 설정. 여기만 고치면 됩니다."""
BUDGET = 500_000          # 총 예산(원)
BUDGET_FLOOR = 470_000    # 최소 이 금액 이상은 채운다
HEADCOUNT = 30            # 인원(수량 산정 기준, 1인당 약 2~3회분)

# 필수 품목: keyword로 검색해 name_must_include 를 모두 포함한 상품 중 1순위 선택
MUST_HAVE = [
    {"label": "사브레", "keyword": "사브레", "name_must_include": ["사브레"], "qty": 4},
    {"label": "밀크 카라멜(모리나가)", "keyword": "모리나가 밀크캬라멜",
     "alt_keywords": ["모리나가 밀크카라멜", "밀크 카라멜 일본"],
     "name_must_include": ["밀크"], "name_any_include": ["카라멜", "캬라멜", "캐러멜"], "qty": 4},
]

# 카테고리별 검색어, 카테고리당 목표 예산 비중, 최대 품목 수
CATEGORIES = {
    "쿠키/비스킷": {"keywords": ["쿠키", "비스킷", "버터쿠키"], "share": 0.20, "max_items": 4},
    "초콜릿/캔디": {"keywords": ["초콜릿", "일본 초콜릿", "젤리 캔디"], "share": 0.15, "max_items": 3},
    "스낵/과자":   {"keywords": ["스낵 과자", "일본 과자", "감자칩"], "share": 0.20, "max_items": 4},
    "견과/건과일": {"keywords": ["견과 소포장", "하루견과", "건망고"], "share": 0.15, "max_items": 3},
    "에너지바/단백질": {"keywords": ["에너지바", "그래놀라바", "프로틴바"], "share": 0.10, "max_items": 2},
    "빵/케이크류": {"keywords": ["마들렌", "파운드케이크", "휘낭시에"], "share": 0.12, "max_items": 2},
    "티/커피/음료": {"keywords": ["티백", "드립백 커피", "스틱커피"], "share": 0.08, "max_items": 2},
}

EXCLUDE_WORDS = ["냉동", "반려", "강아지", "고양이", "이유식", "유아", "쿠폰", "정기배송"]
MIN_REVIEWS = 30           # 후기 수 하한(필드가 있을 때만 적용)
MAX_UNIT_PRICE = 25_000    # 단품 가격 상한(다과로 과함 방지)
MIN_UNIT_PRICE = 1_500
