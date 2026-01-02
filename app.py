import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화] ---
if 'my_items' not in st.session_state:
    st.session_state.my_items = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.set_page_config(page_title="간편 거래명세서 스마트형", layout="centered")

@st.cache_resource
def get_font(size=25):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

def draw_right(draw, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    draw.text((x_end - w, y), str(text), font=font, fill=fill)

# --- [1. 정보 입력창] ---
st.header("🧾 명세서 작성 및 수정")
client = st.text_input("🏢 거래처명", key="client_name")

with st.container():
    c1, c2, c3 = st.columns([1, 1, 2])
    # 월/일 입력 (자동 보정)
    with c1: 
        m_in = st.number_input("월", 1, 12, int(datetime.now().strftime("%m")))
        m_str = f"{min(max(m_in, 1), 12):02d}"
    with c2: 
        d_in = st.number_input("일", 1, 31, int(datetime.now().strftime("%d")))
        d_str = f"{min(max(d_in, 1), 31):02d}"
    with c3: name = st.text_input("품목명")

    c4, c5, c6 = st.columns([1, 1, 2])
    with c4: spec = st.text_input("규격")
    with c5: qty = st.selectbox("수량(t)", [0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    with c6: price_man = st.number_input("금액(단위: 만원)", 0, value=0)

# 추가 및 수정 버튼
if st.session_state.edit_index is None:
    if st.button("➕ 내역 추가하기", use_container_width=True):
        if name:
            st.session_state.my_items.append({
                "m": m_str, "d": d_str, "name": name, 
                "spec": spec, "qty": qty, "price": price_man * 10000
            })
            # 날짜순 정렬 (월, 일 순서)
            st.session_state.my_items.sort(key=lambda x: (x['m'], x['d']))
            st.rerun()
else:
    col_edit1, col_edit2 = st.columns(2)
    if col_edit1.button("✅ 수정 완료", variant="primary", use_container_width=True):
        st.session_state.my_items[st.session_state.edit_index] = {
            "m": m_str, "d": d_str, "name": name, 
            "spec": spec, "qty": qty, "price": price_man * 10000
        }
        st.session_state.my_items.sort(key=lambda x: (x['m'], x['d']))
        st.session_state.edit_index = None
        st.rerun()
    if col_edit2.button("❌ 취소", use_container_width=True):
        st.session_state.edit_index = None
        st.rerun()

# --- [2. 내역 리스트 (수정/삭제)] ---
if st.session_state.my_items:
    st.subheader("📝 내역 확인")
    for i, item in enumerate(st.session_state.my_items):
        cols = st.columns([3, 1, 1])
        cols[0].write(f"[{item['m']}/{item['d']}] {item['name']} ({item['spec']}) - {item['qty']}t / {item['price']:,}원")
        if cols[1].button("수정", key=f"edit_btn_{i}"):
            st.session_state.edit_index = i
            st.rerun()
        if cols[2].button("삭제", key=f"del_btn_{i}"):
            st.session_state.my_items.pop(i)
            st.rerun()

st.divider()

# --- [3. 명세서 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not st.session_state.my_items:
        st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size
            H_TOP = 345
            row_gray = orig.crop((0, 346, W, 404))
            row_white = orig.crop((0, 406, W, 464))
            footer = orig.crop((0, H - 72, W, H))

            count = len(st.session_state.my_items)
            H_ROW = 58
            new_h = H_TOP + (H_ROW * count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))
            res.paste(orig.crop((0, 0, W, H_TOP)), (0, 0))
            for i in range(count):
                res.paste(row_gray if i % 2 == 0 else row_white, (0, H_TOP + (i * H_ROW)))
            res.paste(footer, (0, H_TOP + (count * H_ROW)))

            draw = ImageDraw.Draw(res)
            f_mid = get_font(28)
            f_big = get_font(48)

            # 상단 정보 (더 오른쪽으로 조정)
            draw_right(draw, 550, 67, datetime.now().strftime("%Y-%m-%d"), f_mid)
            draw_right(draw, 550, 122, f"{client}", f_mid)

            # 상단 합계
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 1050, 201, f"{total_sum:,}", f_big)

            # 내역 기록
            for i, item in enumerate(st.session_state.my_items):
                ty = H_TOP + (i * H_ROW) + 12
                # 월/일
                draw.text((20, ty), f"{item['m']}/{item['d']}", font=f_mid, fill="black")
                # 품목
                draw.text((348, ty), item['name'], font=f_mid, fill="black")
                # 규격 (뒤에 (t) 추가)
                draw.text((800, ty), f"{item['spec']}(t)", font=f_mid, fill="black")
                # 수량 (살짝 왼쪽으로 이동 및 (t) 추가)
                draw_right(draw, 1020, ty, f"{item['qty']}(t)", f_mid)
                # 공급가액/세액 (더 오른쪽으로 이동)
                draw_right(draw, 1450, ty, f"{item['price']:,}", f_mid)
                draw_right(draw, 1650, ty, "0", f_mid)

            # 하단 합계
            foot_ty = H_TOP + (count * H_ROW) + 18
            draw_right(draw, 1450, foot_ty, f"{total_sum:,}", f_mid)
            draw_right(draw, 1650, foot_ty, "0", f_mid)

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 최종 명세서 저장", buf.getvalue(), f"명세서_{client}.png")
        except Exception as e:
            st.error(f"오류: {e}")
