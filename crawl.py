# 코스트코 코리아 매일 자동 크롤러 (GitHub Actions에서 실행)
# 결과물: data.json(상품 데이터), history.json(가격 기록), img/(상품 사진), index.html(화면)

import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from PIL import Image

# ===== 설정 =====
MAX_PAGES = 3  # 카테고리당 페이지 수 (1페이지 = 약 48개)
SOURCES = [
    ("할인상품", "https://www.costco.co.kr/Special-Price-Offers/c/SpecialPriceOffers"),
    ("신상품", "https://www.costco.co.kr/c/whatsnew"),
]
BASE = "https://www.costco.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}
PRICE_RE = re.compile(r"^[\d,]+원$")
HISTORY_DAYS = 30


def to_int(text):
    digits = re.sub(r"[^\d]", "", str(text))
    return int(digits) if digits else None


def is_product_img(img):
    src = img.get("src") or img.get("data-src") or ""
    a = img.find_parent("a", href=True)
    return "/medias/" in src and a is not None and "/p/" in a["href"]


def find_card(a):
    node = a
    for _ in range(8):
        node = node.parent
        if node is None:
            return None
        if sum(1 for i in node.find_all("img") if is_product_img(i)) > 1:
            return None
        if any(PRICE_RE.match(s) for s in node.stripped_strings):
            return node
    return None


def find_old_price(card, current):
    cands = card.find_all(["del", "s", "strike"])
    cands += card.find_all(class_=re.compile(r"original|before|strike|list-price", re.I))
    for c in cands:
        m = re.search(r"[\d,]{3,}원", c.get_text(strip=True))
        if m:
            old = to_int(m.group())
            if old and current and old > current:
                return old
    return None


def parse_page(html, category):
    soup = BeautifulSoup(html, "html.parser")
    items, seen = [], set()
    for img in soup.find_all("img"):
        if not is_product_img(img):
            continue
        a = img.find_parent("a", href=True)
        link = urljoin(BASE, a["href"])
        if link in seen:
            continue
        card = find_card(a)
        if card is None:
            continue
        price = next((to_int(s) for s in card.stripped_strings if PRICE_RE.match(s)), None)
        name = (img.get("alt") or img.get("title") or a.get("title") or "").strip()
        if not name or price is None:
            continue
        m = re.search(r"/p/(\d+)", link)
        if not m:
            continue
        seen.add(link)
        items.append(
            {
                "code": m.group(1),
                "name": name,
                "price": price,
                "old": find_old_price(card, price),
                "prev": False,
                "src": urljoin(BASE, img.get("src") or img.get("data-src")),
                "link": link,
                "cat": category,
            }
        )
    return items


session = requests.Session()
session.headers.update(HEADERS)
rows = []
for category, base in SOURCES:
    for page in range(MAX_PAGES):
        url = base if page == 0 else f"{base}?page={page}"
        try:
            r = session.get(url, timeout=30)
        except Exception as e:
            print(f"[{category}] {page + 1}페이지 오류: {e}")
            break
        print(f"[{category}] {page + 1}페이지 -> {r.status_code}")
        if r.status_code != 200:
            break
        found = parse_page(r.text, category)
        print(f"  상품 {len(found)}개")
        if not found:
            break
        rows += found
        time.sleep(1.5)

if not rows:
    raise SystemExit("수집된 상품이 없어서 기존 데이터를 그대로 둡니다.")

# ----- 사진 저장 (이미 있으면 건너뜀) -----
os.makedirs("img", exist_ok=True)


def save_img(item):
    path = f"img/{item['code']}.jpg"
    if os.path.exists(path):
        return
    try:
        r = session.get(item["src"], headers={"Referer": BASE + "/"}, timeout=20)
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        im.thumbnail((320, 320))
        im.save(path, "JPEG", quality=70)
    except Exception as e:
        print("사진 실패:", item["code"], e)


with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(save_img, rows))

keep = {f"{it['code']}.jpg" for it in rows}
for f in os.listdir("img"):
    if f not in keep:
        os.remove(os.path.join("img", f))

# ----- 가격 기록: 최근 30일 최고가보다 싸면 '이전 최고가'로 표시 -----
KST = ZoneInfo("Asia/Seoul")
now = datetime.now(KST)
today = now.strftime("%Y-%m-%d")
cutoff = (now - timedelta(days=HISTORY_DAYS)).strftime("%Y-%m-%d")
hist = {}
if os.path.exists("history.json"):
    with open("history.json", encoding="utf-8") as f:
        hist = json.load(f)

for it in rows:
    h = hist.setdefault(it["code"], {})
    h[today] = it["price"]
    for d in [d for d in h if d < cutoff]:
        del h[d]
    ref = max(h.values())
    if not it["old"] and ref > it["price"]:
        it["old"], it["prev"] = ref, True
    it["img"] = f"img/{it['code']}.jpg" if os.path.exists(f"img/{it['code']}.jpg") else ""

active = {it["code"] for it in rows}
hist = {c: h for c, h in hist.items() if c in active}

with open("history.json", "w", encoding="utf-8") as f:
    json.dump(hist, f, ensure_ascii=False)
out = [{k: v for k, v in it.items() if k != "src"} for it in rows]
with open("data.json", "w", encoding="utf-8") as f:
    json.dump({"updated": now.strftime("%Y-%m-%d %H:%M"), "items": out}, f, ensure_ascii=False)

PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="코스트코">
<title>코스트코 데일리 업데이트</title>
<style>
  :root { --red:#e31837; --blue:#005daa; --bg:#f5f5f7; --card:#fff; --text:#222; --sub:#888; --line:#e6e6e6; }
  @media (prefers-color-scheme: dark) { :root { --bg:#111; --card:#1c1c1e; --text:#f2f2f2; --sub:#999; --line:#333; } }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font-family:-apple-system,BlinkMacSystemFont,"Malgun Gothic","Apple SD Gothic Neo",sans-serif; }
  header { position:sticky; top:0; z-index:10; background:var(--bg); padding:calc(env(safe-area-inset-top,0px) + 10px) 12px 8px; border-bottom:1px solid var(--line); }
  h1 { font-size:1.15rem; margin:0 0 2px; }
  .updated { font-size:.78rem; color:var(--sub); margin-bottom:8px; }
  .tabs { display:flex; gap:6px; margin-bottom:8px; }
  .tab { flex:1; padding:8px 0; border:1px solid var(--line); background:var(--card); color:var(--text); border-radius:20px; font-size:.9rem; }
  .tab.active { background:var(--red); border-color:var(--red); color:#fff; font-weight:600; }
  input[type=search] { width:100%; padding:9px 12px; border:1px solid var(--line); border-radius:10px; background:var(--card); color:var(--text); font-size:1rem; }
  .count { font-size:.8rem; color:var(--sub); margin:8px 12px 0; }
  .grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; padding:10px 12px calc(24px + env(safe-area-inset-bottom,0px)); }
  @media (min-width:700px) { .grid { grid-template-columns:repeat(3,1fr); } }
  @media (min-width:1000px) { .grid { grid-template-columns:repeat(4,1fr); } }
  .card { background:var(--card); border-radius:12px; overflow:hidden; border:1px solid var(--line); }
  .card a { color:inherit; text-decoration:none; display:block; }
  .card img { width:100%; aspect-ratio:1/1; object-fit:contain; background:#fff; display:block; }
  .info { padding:8px 10px 12px; }
  .name { font-size:.88rem; font-weight:600; line-height:1.3; height:2.6em; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .old { font-size:.8rem; color:var(--sub); text-decoration:line-through; min-height:1.1em; margin-top:4px; }
  .price { font-size:1.1rem; font-weight:700; color:var(--red); }
  .badge { display:inline-block; background:var(--red); color:#fff; border-radius:6px; padding:0 6px; font-size:.72rem; margin-left:4px; vertical-align:middle; }
  .badge.new { background:var(--blue); }
  .empty { text-align:center; color:var(--sub); padding:48px 20px; grid-column:1/-1; }
</style>
</head>
<body>
<header>
  <h1>🛒 코스트코 데일리 업데이트</h1>
  <div class="updated" id="updated">🕒 마지막 업데이트: 불러오는 중...</div>
  <div class="tabs">
    <button class="tab active" data-f="전체">전체</button>
    <button class="tab" data-f="신상품">신상품</button>
    <button class="tab" data-f="할인상품">할인상품</button>
  </div>
  <input type="search" id="q" placeholder="🔍 상품명 검색">
</header>
<div class="count" id="count"></div>
<main class="grid" id="grid"></main>
<script>
let ITEMS = [], filter = "전체", keyword = "";
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const won = n => n == null ? "가격 정보 없음" : n.toLocaleString("ko-KR") + "원";
function card(it) {
  let oldLine = '<div class="old">&nbsp;</div>', badge = "";
  if (it.old && it.price && it.old > it.price) {
    oldLine = '<div class="old">' + (it.prev ? "최근 최고가 " : "") + won(it.old) + '</div>';
    badge = '<span class="badge">' + Math.round((it.old - it.price) / it.old * 100) + '%↓</span>';
  } else if (it.cat === "할인상품") badge = '<span class="badge">할인가</span>';
  else if (it.cat === "신상품") badge = '<span class="badge new">NEW</span>';
  return '<div class="card"><a href="' + esc(it.link) + '" target="_blank" rel="noopener">' +
    '<img src="' + esc(it.img) + '" loading="lazy" alt="">' +
    '<div class="info"><div class="name">' + esc(it.name) + '</div>' + oldLine +
    '<div class="price">' + won(it.price) + badge + '</div></div></a></div>';
}
function render() {
  const kw = keyword.trim().toLowerCase();
  const list = ITEMS.filter(it => (filter === "전체" || it.cat === filter) && (!kw || it.name.toLowerCase().includes(kw)));
  document.getElementById("count").textContent = "총 " + list.length + "개 상품";
  document.getElementById("grid").innerHTML = list.length ? list.map(card).join("") : '<div class="empty">조건에 맞는 상품이 없어요.</div>';
}
document.querySelectorAll(".tab").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); filter = b.dataset.f; render();
}));
document.getElementById("q").addEventListener("input", e => { keyword = e.target.value; render(); });
fetch("data.json?t=" + Date.now()).then(r => r.json()).then(d => {
  ITEMS = d.items;
  document.getElementById("updated").textContent = "🕒 마지막 업데이트: " + d.updated;
  render();
}).catch(() => { document.getElementById("updated").textContent = "데이터를 불러오지 못했어요"; });
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(PAGE)

print(f"완료! 상품 {len(rows)}개 저장 ({now.strftime('%Y-%m-%d %H:%M')})")
