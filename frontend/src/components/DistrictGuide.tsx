import type { Decision } from '../lib/api'

/** 구·군 참고 안내(재활용 불가 품목). 부산시 공식 기준(배출 방법)과 분리해 보여준다. 배출 요일은 API가 내려주지 않는다. */
export function DistrictGuide({ info }: { info: Decision['district_info'] }) {
  if (!info || !info.prohibited_items) return null
  return (
    <aside className="district-guide">
      <h3>{info.gu} 안내</h3>
      {info.prohibited_items && <p><b>재활용 불가 품목</b>{info.prohibited_items}</p>}
      <small>
        {info.verified && info.source_url
          ? <a href={info.source_url} target="_blank" rel="noreferrer">{info.source_label} ↗</a>
          : info.source_label}
      </small>
    </aside>
  )
}
