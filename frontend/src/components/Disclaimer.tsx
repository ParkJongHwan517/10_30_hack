// PROJECT_SPEC §12 고정 문구 — 모든 화면 하단에 그대로 보여준다(문구 변경 금지)
export function Disclaimer() {
  return (
    <div className="disclaimer" role="note">
      <span>⚠</span>
      <p>
        이 화면은 시연용 예시입니다. 실제 서비스에서는 부산시와 각 구·군의 최신 공식 공지사항을 기준으로 제공합니다.
        배출 요일과 장소는 지역별로 다를 수 있으므로 거주 지역의 최신 안내를 반드시 확인하세요.
      </p>
    </div>
  )
}
