import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v1.0] ---
if 'items_v10' not in st.session_state:
    st.session_state.items_v10 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except: return None

# --- [1. 정보 입력 (v1.0)] ---
st.header("1. 정보 입력 (v1.0)")
client = st.text_input("🏢 거래처명", key="c_v10")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v10")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v10")
    
    name = st.text_input("품목명", key="n_v10")
    spec = st.text_input("규격", key="s_v10")
    
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v10")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v10")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v10.append({
            "m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

st.divider()

# --- [2. 거래 내역 리스트] ---
st.header("2. 현재 입력된 내역")
if st.session_state.items_v10:
    for i, item in enumerate(st.session_state.items_v10):
        st.write(f"✅ {i+1}. {item['name']} - {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v10 = []
        st.rerun()
else:
    st.info("내역이 없습니다.")

st.divider()

# --- [3. 동적 조립 명세서 생성] ---
if st.button("🚀 내역 수에 맞춰 이미지 생성", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 적어주세요!")
    elif not st.session_state.items_v10: st.warning("내역을 추가해주세요!")
    else:
        try:
            full_img = Image.open("template.png").convert("RGB")
            w, h = full_img.size

            # --- 정밀 좌표 조절 영역 ---
            # 헤더: 0부터 390까지
            header = full_img.crop((0, 0, w, 390))
            # 줄 한 칸: 390부터 440까지 (높이 50)
            row_unit = full_img.crop((0, 390, w, 440))
            # 푸터: 합계 부분 (이미지 끝에서 100픽셀 정도 자름)
            footer = full_img.crop((0, h-100, w, h))

            # 새 이미지 높이 계산 및 생성
            new_h = header.height + (row_unit.height * len(st.session_state.items_v10)) + footer.height
            result_img = Image.new("RGB", (w, new_h), (255, 255, 255))

            # 이미지 조각 붙이기
            result_img.paste(header, (0, 0))
            for i in range(len(st.session_state.items_v10)):
                y_pos = header.height + (i * row_unit.height)
                result_img.paste(row_unit, (0, y_pos))
            result_img.paste(footer, (0, header.height + (len(st.session_state.items_v10) * row_unit.height)))

            # 글자 쓰기 시작
            draw = ImageDraw.Draw(result_img)
            font_data = get_font()
            font = ImageFont.truetype(font_data, 24) if font_data else ImageFont.load_default()
            
            # 1. 상단 정보
            draw.text((250, 85), datetime.now().strftime("%Y  %m  %d"), font=font, fill="black")
            draw.text((150, 155), f"{client} 귀하", font=font, fill="black")

            # 2. 동적 줄 내용
            total_sum = 0
            for i, item in enumerate(st.session_state.items_v10):
                line_y = header.height + (i * row_unit.height) + 10
                draw.text((35, line_y), item['m'], font=font, fill="black")
                draw.text((80, line_y), item['d'], font=font, fill="black")
                draw.text((160, line_y), item['name'], font=font, fill="black")
                draw.text((650, line_y), f"{item['price']:,}", font=font, fill="black")
                total_sum += item['price']

            # 3. 하단 합계
            footer_text_y = header.height + (len(st.session_state.items_v10) * row_unit.height) + 30
            draw.text((650, footer_text_y), f"{total_sum:,}", font=font, fill="black")

            st.image(result_img)
            
            buf = io.BytesIO()
            result_img.save(buf, format="PNG")
            st.download_button("📥 최종 명세서 저장", buf.getvalue(), f"명세서_{client}.png")
            
        except Exception as e:
            st.error(f"이미지 생성 오류: {e}")
