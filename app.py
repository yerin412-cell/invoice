import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

# --- [0. 저장소 초기화 - v1.2] ---
if 'items_v12' not in st.session_state:
    st.session_state.items_v12 = []

st.set_page_config(page_title="우리집 거래명세서", layout="centered")

# --- [1. 폰트 로드 안전장치] ---
def get_safe_font(size):
    try:
        # 시스템 기본 폰트 사용 (파일 오픈 에러 방지)
        return ImageFont.load_default()
    except:
        return None

# --- [2. 정보 입력 (v1.2)] ---
st.header("1. 정보 입력 (v1.2)")
client = st.text_input("🏢 거래처명", key="c_v12")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v12")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v12")
    name = st.text_input("품목명", key="n_v12")
    spec = st.text_input("규격", key="s_v12")
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v12")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v12")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v12.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.rerun()

st.divider()

# --- [3. 거래 내역 리스트] ---
st.header("2. 현재 입력된 내역")
if st.session_state.items_v12:
    for i, item in enumerate(st.session_state.items_v12):
        st.write(f"✅ {i+1}. {item['name']} | {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v12 = []
        st.rerun()
else:
    st.info("내역이 없습니다. 위에서 입력 후 추가 버튼을 눌러주세요.")

st.divider()

# --- [4. 명세서 이미지 생성] ---
if st.button("🚀 내역 개수대로 명세서 만들기", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 적어주세요!")
    elif not st.session_state.items_v12: st.warning("내역을 추가해주세요!")
    else:
        try:
            # 설정값 (엑셀 느낌의 규격)
            W = 800
            H_HEADER = 250  # 상단 제목/거래처 영역
            H_ROW = 45     # 내역 한 줄 높이
            H_FOOTER = 80   # 합계 영역
            
            items = st.session_state.items_v12
            total_h = H_HEADER + (H_ROW * (len(items) + 1)) + H_FOOTER
            
            # 배경 생성 (흰색)
            img = Image.new("RGB", (W, total_h), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            font = get_safe_font(20)

            # --- [그리기 시작] ---
            # 1. 제목 및 테두리
            draw.rectangle([10, 10, W-10, total_h-10], outline="black", width=3)
            draw.text((W//2-50, 30), "[ 거 래 명 세 서 ]", fill="black")
            draw.text((30, 80), f"발행일자: {datetime.now().strftime('%Y-%m-%d')}", fill="black")
            draw.text((30, 120), f"거래처명: {client} 귀하", fill="black")

            # 2. 표 헤더 (회색 배경)
            y_table = 180
            draw.rectangle([20, y_table, W-20, y_table + H_ROW], fill=(220, 220, 220), outline="black")
            header_titles = ["월/일", "품목명", "규격", "수량", "공급가액"]
            header_xs = [40, 150, 400, 520, 650]
            for t, x in zip(header_titles, header_xs):
                draw.text((x, y_table + 12), t, fill
