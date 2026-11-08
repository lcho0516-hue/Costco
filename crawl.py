# 코스트코 코리아 매일 자동 크롤러 (GitHub Actions에서 실행)
# 결과물: data.json(상품 데이터), history.json(가격 기록), img/(상품 사진), index.html(화면)

수입 IO
json 가져오기
os 가져오기
가져오기 re
가져오기 시간
동시에.선물 가져오기 ThreadPoolExecutor
datetime 가져오기 datetime, timelta
urllib.parse 가져오기 urljoin에서
zoneinfo에서 ZoneInfo 가져오기

가져오기 요청
bs4에서 BeautifulSoup 가져오기
PIL 가져오기 이미지에서

# ===== 설정 =====
MAX_PAGES = 3 # 카테고리당 페이지 수 (1페이지 = 약 48개)
출처 = [
 ("할인상품", "https://www.costco.co.kr/Special-Price-Offers/c/SpecialPriceOffers "),
 ("신상품", "https://www.costco.co.kr/c/whatsnew "),
]
BASE = "https://www.costco.co.kr "
헤더 = {
 "사용자 에이전트": (
        "모질라/5.0(Windows NT 10.0, Win64, x64) AppleWebKit/537.36"
        "(KHTML, 게코처럼) 크롬/124.0 사파리/537.36"
 ),
 "언어 수락": "ko-KR,ko;q=0.9",
}
PRICE_RE = re.compile(r"^[\\d,]+원$)
역사_일수 = 30


def to_int(텍스트):
 숫자 = re.sub(r "[^\\d], ", str(텍스트)
 숫자가 없으면 int(자리 수) 반환 없음


def is_product_img(img):
 src = img.get("src") or img.get("data-src") or ""
 = img.find_parent ("a", href=True)
 src에서 "/medias/"를 반환하고 a는 없음이 아니며 a["href"]에서 "/p/"를 반환합니다


def find_card(a):
 노드 = a
 _ 범위 (8)에서:
 노드 = node.parent
 노드가 없음인 경우:
 돌아가다 없음.
 만약 합(i에 대한 i)이라면.find_all ("img")가 _product_img(i) > 1인 경우:
 없음을 반환합니다.
 만약 (node.stripped_strings에서 s에 대한 PRICE_RE.match(들):
 반환 노드
 돌아가다 없음.


def find_old_price(카드, 현재):
 cands = card.find_all(["del", "s", "strike"])
 cands += card.find_all(class_=re.compile(r"오리지널|비포|스트라이크|리스트 가격"), re.I))
 캔드 단위로 c:
 m = re.search(r "[\\d, [{3,}원", c.get_text(strip=True))
 만약 m:
 이전 = to_int(m.group ())
 오래된 경우와 현재의 경우, 그리고 오래된 경우 > 현재:
 오래된 것으로 돌아가기
 발견 = parse_page(r.text, 카테고리)


def parse_page(html, 카테고리):
 수프 = 뷰티풀 수프(html, "html.파서")
 항목, 보기 = [], 설정 ()
 수프에 넣어 주세요.find_all ("img"):
 그렇지 않은 경우 _product_img(img):
 계속하다.
 = img.find_parent ("a", href=True)
 링크 = urljoin(BASE, a["href"])
 링크가 표시되는 경우:
 계속하다.
 카드 = find_card(a)
 카드가 없는 경우:
 계속하다.
 가격 = next((카드에서 s의 경우_int(s)), PRICE_RE.match(s)인 경우_stripped_strings, 없음)
 이름 = (img.get ("alt") 또는 img.get ("title") 또는 a.get ("title") 또는 ".strip ()"
 이름이나 가격이 없으면 없음:
 계속하다.
 m = re.search(r"/p/(\d+)", link)
 그렇지 않은 경우 m:
 계속하다.
 see.add(링크)
 항목.append(
 인쇄 ("사진 실패:", 항목["코드"], e)
 "코드": m.group(1),
 "이름": 이름,
 "가격": 가격,
 "오래된": find_old_price(카드, 가격),
 "prev": 거짓,
 "src": urljoin(BASE, img.get("src") or img.get("data-src")),
 "링크": 링크,
 "고양이": 카테고리,
 }
 )
 반품 항목


세션 = 요청.세션()
세션.headers.update(HEADERS)
행 = []
카테고리의 경우, 출처:
 범위 내 페이지(MAX_PAGS):
 URL = base if page == 0 else f"{base}?page={page}"
 시도:
 r = session.get(url, 타임아웃=30)
 예외: e:
 인쇄(f "[{category}] {페이지 + 1}페이지 오류: {e}})"
 브레이크.
 인쇄(f "[{category}] {페이지 + 1}페이지 -> {r.status_code})"
 만약 r.status_code!= 200:
 브레이크.
 발견 = parse_page(r.text, 카테고리)
 인쇄(f" 상품 {len(발견됨)}개")
 발견되지 않은 경우:
 브레이크.
 행 += 발견
 시간.수면(1.5)

행이 아니라면:
 raise SystemExit("수집된 상품이 없어서 기존 데이터를 그대로 둡니다.")

# ----- 사진 저장 (이미 있으면 건너뜀) -----
os.makedirs ("img", exist_ok=True)


def save_img(항목):
 path = f"img/{item['code']}.jpg"
 if os.path.exists(경로):
 돌아가다
 시도:
 r = session.get(아이템["src"), 헤더={"참조자": BASE + "/", 타임아웃=20)
 im = Image.open(io).BytesIO(r.content).convert("RGB")
 im.thumbnail((320, 320))
 im.save(경로, "JPEG", 품질=70)
 예외: e:
 인쇄 ("사진 실패:", 항목["코드"], e)


ThreadPoolExecutor(max_works=8)를 ex로 사용합니다:
 list(ex.map(save_img, 행))

행에 = {f"{it['code']}.jpg"를 유지합니다
for f in os.listdir("img"):
 f가 유지되지 않으면:
 os.remove(os.path.join("img, f))

# ----- 가격 기록: 최근 30일 최고가보다 싸면 '이전 최고가'로 표시 -----
KST = ZoneInfo("아시아/서울")
지금 = datetime.now(KST)
today = now.strftime("%Y-%m-%d")
컷오프 = (현재 - 시간 델타(일)=역사_DAYS).strftime("%Y-%m-%d")
hist = {}
if os.path.exists("history.json"):
 open ("history.json, 인코딩="utf-8")을 f로 사용합니다:
 hist = json.load(f)

일렬로 배열되어 있습니다:
 h = hist.setdefault(it["코드"], {})
 h[오늘] = it["가격"]
 d의 경우 [d의 경우 d의 경우 h의 경우]:
 델 h[d]
 참조 = max(h.values ())
 그렇지 않다면 ["오래된"] 및 참조 > ["가격"]:
 it["오래된"], it["prev"] = ref, True
 it["img"] = f"img/{it['code']}.jpg" if os.path.exists(f"img/{it['code']}.jpg") else ""

행에 있는 활성 = {it["code"]
hist = {c: h for c, h in hist. items() in active}

open (" history.json", "w", 인코딩="utf-8")을 f로 사용합니다:
 json.dump(히스트, f, secure_ascii=false)
출력 = [{k: v for k, v in it. k!= "src"}일 경우 items()]
open ("data.json", "w", 인코딩="utf-8")을 f로 사용합니다:
 json.dump({ "updated": now.strftime("%Y-%m-%d %H:%M"), "items": out, f, secure_ascii=false)

페이지 = @media (최소 너비:700 px) { .grid { 그리드-template-columns:repeat(3,1fr); }
<html lang="ko">
<머리>
<meta charset="utf-8">
<meta 이름="viewport" 콘텐츠="width=장치 너비, 초기 스케일=1, viewport-fit=cover">
<meta 이름="애플-모바일 웹 앱 지원" 콘텐츠="예">
<meta 이름="모바일 웹 앱 지원" 콘텐츠="예">
<meta 이름="애플-모바일-웹앱-title" 콘텐츠="코스트코">
<title>코스트코 데일리 업데이트</title>
<스타일>
 :root { --red:#e31837; --blue:#005daa; --bg:#f5f5f7; --card:#fff; --text:#222; --sub:#888; --line:#e6e6e6; }
 @media (prefers-색-scheme: 어두운) { :root { --bg:#111; --card:#1c1c1e; --text:#f2f2f2; --sub:#999; --line:#333; } }
 * { 상자-sizing:경계 상자;}
 본문 { 여백:0; 배경:var(--bg); 색상:var(--text);
 폰트 패밀리:-애플 시스템, 블링크맥시스템폰트, "말건 고딕", "애플 SD 고딕 네오", sans-serif; }
 헤더 {위치:sticky; 상단:0; z-인덱스:10; 배경:var(--bg); 패딩:calc(env(안전 영역-삽입 상단,0 px) + 10 px) 12 px 8 px; 경계 하단:1 px 솔리드 var(--선); }
 h1 { 글꼴 크기:1.15rem; 여백:0 0 2 px; }
 .updated { 글꼴 크기:.78rem; 색상:var(--서브); 여백 하단:8 px; }
 .tabs {디스플레이:플렉스; 간격:6 px; 여백 하단:8 px; }
 .탭 {플렉스:1; 패딩:8 px 0; 테두리:1 px 솔리드 var(--line); 배경:var(--카드); 색상:var(--텍스트); 테두리-radius:20 px; 글꼴 크기:.9rem; }
 .tab.active {background:var(--red); 테두리 색상:var(--red); 색상:#ffff; 글꼴 무게:600; }
 입력 [유형=검색] {폭:100%; 패딩:9 px 12 px; 테두리:1 px 솔리드 var(--line); 테두리:10 px; 배경:var(--카드); 색상:var(--텍스트); 글꼴 크기:1rem; }
 .count { 글꼴 크기:.8rem; 색상:var(--sub); 여백:8 px 12 px 0; }
 .grid { 디스플레이:grid; 그리드-template-columns:repeat(2,1fr); 갭:10 px; 패딩:10 px 12 px 계산(24 px + 환경(안전 영역 삽입 하단, 0 px)); }
 @media (최소 너비:700 px) { .grid { 그리드-template-columns:repeat(3,1fr); } }
 @media (최소 너비:1000 px) { .grid { 그리드-template-columns:repeat(4,1fr); } }
 .card {background:var(--card); 경계-radius:12 px; 오버플로:숨김; 경계:1 px 솔리드 var(--line); }
 .카드 a {색상:inherit; 텍스트 장식:none; 디스플레이:블록; }
 .card img {폭:100%; 측면 ratio:1/1; 객체 맞춤:포함; 배경:#fff; 디스플레이:블록; }
 .info { 패딩}:8 px 10 px 12 px; }
 .이름 { 글꼴 크기:}.88rem; 글꼴 무게:600; 줄 높이:1.3; 높이:2.6em; 오버플로우:숨김; 디스플레이:-웹킷 상자; -웹킷 줄 clamp:2; -웹킷 상자 방향:vertical; }
 .old { 글꼴 크기:.8rem; 색상:var(--서브); 텍스트 장식:선 통과;최소 높이:1.1em; 여백 상단:4 px; }
 .가격 { 글꼴 크기:1.1rem; 글꼴 무게:700; 색상:var(--red); }
 .badge {디스플레이: inline 블록; 배경:var(--red); 색상:#fff; 테두리-radius:6 px; 패딩:0 6 px; 글꼴 크기:.72rem; 여백-왼쪽:4 px; 세로-align:중간; }
 .badge.새 {배경:var(--파란색); }
 .비어 {텍스트 align:센터; 색상:var(--sub); 패딩:48 px 20 px; 그리드 열:1/-1; }
</스타일>
</머리>
<바디>
<header>
 <h1>🛒 코스트코 데일리 업데이트</h1>
 <div class="updated" ID="updated">🕒 마지막 업데이트: 불러오는 중...</div>
 <div class="tabs">
 <버튼 class="탭 활성화" data-f="전체">전체</버튼>
 <버튼 class="탭" data-f="신상품">신상품</버튼>
 <버튼 class="탭" data-f="할인상품">할인상품</버튼>
 </div>
 <입력 유형="검색" ID="q" 자리 표시자="🔍"상품명 검색">
</header>
<div class="count" id="count"></div>
<main class="grid" id="grid"></main>
<스크립트>
항목 = [], 필터링 = "전체", 키워드 = "";
const esc = s => 문자열(s == null ? "" : s.replace(/[&<>)]/g, c => ({"&:"&"),<:"<"<"",">"">"""""""""""""""""""""""""""""""")"""""""""""""""""""""""")"}[c];"
const가 승리했습니다 = n => n == null ? "가격 정보 없음" : n.toLocaleString("ko-KR") + "원";
함수 카드(it) {
 oldLine = '<div class="old"> </div>, 배지 = "";
 만약 (그것.old & it.price & it.old > it.price) {
 oldLine = '<div class="old"> + (it.prev ? "최근 최고가 ": "") + won(it.old) + '/div>';
 배지 = '<span class="badge">' + Math.round((((it.old - it.price)) / it.old * 100) + '%↓</span>';
 } 그렇지 않으면 (it.cat === "할인상품" 배지 = '<span class="badge">할인가</span>';
 그렇지 않으면 (it.cat === "신상품" 배지 = '<span class="badge new">NEW</span>;
 '<div class="card"><a href=' + esc(it.link) + '"target="_blank" rel="noopen">을 반환합니다. +
 '<img src=' + esc(it.img) + '"로딩="lazy" alt=""> +
 '<div class="info"><div class="name">' + esc(it.name ) + '</div>' + oldLine +
 '<div class="price">' + 원화(it.price) + 배지 + '</div></div></a></div>;
}
함수 렌더링 () {
 const kw = 키워드.trim(.toLowerCase());
 const list = ITMS.filter (필터 === > (필터 = "전체" || it.cat === 필터) & & (!kw || it.name .toLowerCase(.includs(kw)));
 document.getElementById("count").텍스트 내용 = "총" + list.length + "개 상품";
 document.getElementById("grid").innerHTML = list.length ? list.map(카드).join ("): '<div class="empty">조건에 맞는 상품이 없어요.</div>';
}
문서.쿼리SelectorAll(.tab").각 항목(b => b.addEventListener("클릭", () => {
 문서.쿼리SelectorAll(.tab").각각에 대해 (x => x.classList.remove("활성");
 b.classList.add("활성"); 필터 = b. dataset.f; () 렌더링;
}));
document.getElementById("q").addEventListener("입력", e => {키워드 = e.target.value; 렌더 (); });
("data.json?t 가져오기=" + 날짜.나우()).then(r => r.json()).then(d => {
 항목 = d. items;
 document.getElementById("업데이트됨").텍스트 내용 = "🕒 마지막 업데이트: " + d. updated;
 ()를 렌더링합니다;
}). catch((() => {document.getElementById("업데이트됨").textContent = "데이터를 불러오지 못했어요"; });
</script>
</body>
</html>
"""

open ("index.html", "w", 인코딩="utf-8")을 f로 사용합니다:
 f.write(PAGE)

print(f"완료! 상품 {len(rows)}개 저장 ({now.strftime('%Y-%m-%d %H:%M')})")
