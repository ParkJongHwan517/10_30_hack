"""API 계약의 원본(SSOT). 프론트 타입(frontend/src/lib/api-types.ts)은 여기서 생성한다.

모델 변경은 A(통합)만 하고, 바꾸기 전에 팀 채팅에 먼저 공지한다. (PROJECT_SPEC §8.2, §9.2, §10)
"""

from typing import Literal

from pydantic import BaseModel, Field

# bool 대신 문자열 3값: Gemini 스키마 호환 + "모름"을 표현하기 위해
Tri = Literal["yes", "no", "unknown"]


# ---------- 관찰 (Gemini가 만든다, §8.2) ----------


class Contamination(BaseModel):
    level: Literal["none", "light", "heavy", "unknown"]
    type: Literal["food", "sauce", "oil", "dirt", "none", "unknown"]
    likely_removable_by_rinsing: Tri


class Attachments(BaseModel):
    label_present: Tri  # 라벨·스티커
    tape_present: Tri  # 테이프
    waybill_present: Tri  # 택배 송장
    lid_present: Tri  # 뚜껑


class Observation(BaseModel):
    # description은 Gemini response_schema에 그대로 실려 분류 기준으로 쓰인다(값 목록은 API 계약)
    item_type: Literal[
        "pet_bottle", "styrofoam_container", "plastic_container", "cardboard_box", "can",
        "vinyl", "glass_bottle", "small_plastic", "paper_pack", "receipt_coated_paper", "other", "unknown",
    ] = Field(description=(
        "이 항목(따로 버리는 물건·구성품 하나)의 종류. "
        "pet_bottle=음료·생수 페트병. "
        "styrofoam_container=발포 스티로폼(EPS)만: 표면에 작은 알갱이 무늬가 보이고 두껍고 가볍고 불투명하다. "
        "plastic_container=플라스틱 용기·트레이·컵·뚜껑: 얇고 매끈하거나 광택 있는 흰색 트레이도 여기에 넣는다. "
        "cardboard_box=상자 모양의 종이: 택배 골판지 상자와 과자·제품 상자(얇은 판지). 컵홀더·종이 용기·종이 봉투처럼 상자가 아닌 종이는 other로 하고 material_guess를 paper로 쓴다. "
        "can=알루미늄·철로 된 음료·식품 캔. "
        "vinyl=비닐류: 과자·라면 봉지, 비닐봉지, 뽁뽁이(에어캡), 랩. "
        "glass_bottle=유리병. "
        "small_plastic=빨대, 일회용 숟가락·포크·젓는 막대처럼 작은 플라스틱. "
        "paper_pack=우유팩·주스팩·두유 멸균팩처럼 안쪽이 코팅된 음료용 종이팩(종이 상자와 구분). "
        "receipt_coated_paper=영수증, 택배 전표, 라벨 스티커, 명함·사진, 금은박·비닐 코팅된 종이. "
        "other=위에 해당하지 않는 물체. unknown=무엇인지 판별할 수 없음."
    ))
    material_guess: Literal[
        "PET", "EPS", "PP", "PS", "paper", "metal", "vinyl", "glass", "mixed", "unknown"
    ] = Field(description=(
        "재질 추정. PET=투명 페트, EPS=발포 스티로폼(알갱이 무늬), PP·PS=일반 플라스틱, paper=종이·판지, "
        "metal=금속, vinyl=비닐·필름, glass=유리, mixed=여러 재질이 붙어 있음. "
        "item_type과 같은 판단이어야 한다(예: 종이 상자를 EPS로 쓰지 않는다)."
    ))
    is_transparent_colorless: Tri  # 페트병: 무색 투명 여부
    is_white: Tri  # 스티로폼: 흰색(유색 아님) 여부
    contents_present: Tri  # 병/캔/유리병/용기 안에 내용물이 남아 있는지
    contamination: Contamination
    attachments: Attachments
    damage: Literal["none", "broken", "crushed", "unknown"]
    coating_or_mixed_material: Tri  # 코팅·타 재질 혼합
    privacy_flag: bool  # 얼굴·송장 개인정보 노출 의심
    photo_quality: Literal["good", "blurry", "dark", "partial"]
    confidence: float  # 0.0~1.0, 내부 판단용(화면 표시 금지). 서버에서 0~1로 clamp
    notes_ko: str  # 관찰 한 문장(판단·배출 방법 언급 금지)
    label_ko: str = Field(
        default="",
        description="결과 카드 제목용 짧은 이름(예: '컵 뚜껑', '종이 컵홀더'). 브랜드·상표는 쓰지 않는다.",
    )


# ---------- 판단 (규칙 엔진이 만든다, §9.2) ----------

DecisionKind = Literal["ASK_QUESTION", "WASH_AND_RESHOOT", "FINAL", "RESHOOT_QUALITY", "UNKNOWN"]
ResultCode = Literal[
    "PET_CLEAR", "PLASTIC", "STYROFOAM", "PAPER", "PAPER_PACK", "CAN", "VINYL", "GLASS", "NONCOMBUSTIBLE", "GENERAL"
]


class QuestionOption(BaseModel):
    v: Tri
    l: str


class Question(BaseModel):
    text: str
    options: list[QuestionOption]


class Source(BaseModel):
    label: str
    url: str | None = None


class Decision(BaseModel):
    kind: DecisionKind
    result_code: ResultCode | None = None
    basis_label: str
    headline: str
    analysis_bullets: list[str] = []
    steps: list[str] = []
    question: Question | None = None
    wash_checklist: list[str] | None = None
    reshoot_reason: Literal["quality", "privacy"] | None = None
    source: Source
    rules_verified: bool
    terminal: bool


# ---------- 요청·응답 (§10) ----------

Gu = Literal[
    "강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구", "북구",
    "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구",
]


class ObserveResponse(BaseModel):
    observation: Observation  # 하위 호환: items[0]과 같은 값
    # default_factory: 스키마에 default가 안 실려서 api-types에서 선택 필드(items?)가 된다 → 기존 프론트 코드가 안 깨진다
    items: list[Observation] = Field(
        default_factory=list, description="사진 속 항목(따로 버리는 물건·구성품)들, 큰 것부터 최대 4개. 프론트는 항목마다 /api/decide를 호출한다."
    )
    ok: bool  # false = 사진 단위 게이트(개인정보·대표 항목 품질)에 걸림 — services.decide.photo_gate_reason
    reason: Literal["quality", "privacy"] | None = None
    demo_mode: bool


class Region(BaseModel):
    sido: Literal["부산광역시"] = "부산광역시"
    gu: Gu


class Answers(BaseModel):
    contamination_removable: Tri | None = None


class DecideRequest(BaseModel):
    region: Region
    observation: Observation
    answers: Answers | None = None
    attempt: Literal[1, 2] = 1
    demo_mode: bool = False


class HealthResponse(BaseModel):
    ok: bool


class ErrorResponse(BaseModel):
    code: str = Field(examples=["AI_BUSY"])
    message: str
