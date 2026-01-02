import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v9] ---
if 'items_v9' not in st.session_state:
    st.session_state.items_v9 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except: return None

# --- [1. 정보 입력 (v0.9)] ---
st.header("1. 정보 입력 (v0.9)")
client = st.text_input("🏢 거래처명", key="c_v9")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v9")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v9")
    
    name = st.text_input("품목명", key="n_v9")
    spec = st.text_input("규격", key="s_v9")
    
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v9")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v9")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v9.append({
            "m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

st.divider()

# --- [2. 거래 내역 리스트] ---
st.header("2. 현재 입력된 내역")
if st.session_state.items_v9:
    for i, item in enumerate(st.session_state.items_v9):
        st.write(f"✅ {i+1}. {item['name']} - {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v9 = []
        st.rerun()

st.divider()

# --- [3. 동적 조립 명세서 생성] ---
if st.button("🚀 내역 수에 맞춰 이미지 생성", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 적어주세요!")
    elif not st.session_state.items_v9: st.warning("내역을 추가해주세요!")
    else:
        try:
            full_img = Image.open("template.png").convert("RGB")
            w, h = full_img.size

            # --- [정밀 좌표 수정] 보내주신 이미지 비율에 맞춤 ---
            # 1. 헤더: (0 ~ 390픽셀) - '월/일/품목' 헤더 직전까지
            header = full_img.crop((0, 0, w, 390))
            # 2. 줄(Row): (390 ~ 440픽셀) - 실제 데이터가 들어가는 빈 줄 한 칸 (약 50px 높이)
            row_unit = full_img.crop((0, 390, w, 440))
            # 3. 푸터: (원본 이미지의 맨 아래 합계 부분만 잘라옴)
            footer = full_img.crop((0
