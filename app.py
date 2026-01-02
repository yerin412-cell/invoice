import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v1.1] ---
if 'items_v11' not in st.session_state:
    st.session_state.items_v11 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except: return None

# --- [1. 정보 입력 (v1.1)] ---
st.header("1. 정보 입력 (v1.1)")
client = st.text_input("🏢 거래처명", key="c_v11")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v11")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v11")
    name = st.text_input("품목명", key="n_v11")
    spec = st.text_input("규격", key="s_v11")
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v11")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v11")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v11.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.rerun()

st.divider()

# --- [2. 거래 내역 리스트] ---
st.header("2. 현재 입력된 내역")
if st.session_state.items_v11:
    for i, item in enumerate(st.session_state.items_v11):
        st.write(f"✅ {i+1}. {item['name']} - {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v11 = []
        st.rerun()

st.divider()

# --- [3. 동적 명세서 이미지 생성] ---
if st.button("🚀 내역 수에 딱 맞게 명세서 만들기", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 적어주세요!")
    elif not st.session_state.items_v11: st.warning("내역을 추가해주세요!")
    else:
        try:
            # 설정값
            W, H_UNIT = 800, 45 # 가로폭, 줄 높이
            items = st.session_state.items_v11
            count = len(items)
            
            # 전체 높이 계산 (헤더 4줄 + 내역 n줄 + 합계 1줄)
            total_h = H_UNIT * (4 + count + 1)
            img = Image.new("RGB", (W, total_h), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            font_data = get_font()
            font = ImageFont.truetype(font_data, 18) if font_data else ImageFont.load_default()
            title_font = ImageFont.truetype(font_data, 30) if font_data else font

            # 1. 헤더 그리기
            draw.rectangle([0, 0, W, H_UNIT*2], outline="black", width=2)
            draw.text((W//2-80, 20), "거 래 명 세 서", font=title_font, fill="black")
            
            # 2. 거래처 및 날짜 정보 줄
            draw.rectangle([0, H_UNIT*2, W, H_UNIT*3], outline="black", width=2)
            draw.text((20, H_UNIT*2+10), f"발행일자: {datetime.now().strftime('%Y-%m-%d')}", font=font, fill="black")
            draw.text((400, H_UNIT*2+10), f"거래처명: {client} 귀하", font=font, fill="black")

            # 3. 표 제목줄 (회색 배경)
            draw.rectangle([0, H_UNIT*3, W, H_UNIT*4], fill=(220, 220, 220), outline="black")
            headers = ["월/일", "품목", "규격", "수량", "금액"]
            xs = [10, 100, 400, 550, 650]
            for txt, x in zip(headers, xs):
                draw.text((x, H_UNIT*3+10), txt, font=font, fill="black")

            # 4. 내역 그리기 (내역 수만큼 반복)
            total_sum = 0
            for i, item in enumerate(items):
                curr_y = H_UNIT * (4 + i)
                # 배경색 교차 (흰색/연회색)
                bg_color = (255, 255, 255) if i % 2 == 0 else (240, 240, 240)
                draw.rectangle([0, curr_y, W, curr_y + H_UNIT], fill=bg_color, outline="black")
                
                draw.text((10, curr_y+10), f"{item['m']}/{item['d']}", font=font, fill="black")
                draw.text((100, curr_y+10), item['name'], font=font, fill="black")
                draw.text((400, curr_y+10), item['spec'], font=font, fill="black")
                draw.text((550, curr_y+10), str(item['qty']), font=font, fill="black")
                draw.text((650, curr_y+10), f"{item['price']:,}", font=font, fill="black")
                total_sum += item['price']

            # 5. 합계 줄 (마지막)
            footer_y = H_UNIT * (4 + count)
            draw.rectangle([0, footer_y, W, footer_y + H_UNIT], fill=(200, 200, 200), outline="black")
            draw.text((400, footer_y+10), "합 계 금 액 (VAT 포함)", font=font, fill="black")
            draw.text((650, footer_y+10), f"{total_sum:,}", font=font, fill="black")

            st.image(img)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.download_button("📥 이미지 저장하기", buf.getvalue(), "명세서_v1.1.png")
            
        except Exception as e:
            st.error(f"오류: {e}")
