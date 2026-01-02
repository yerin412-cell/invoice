import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v5] ---
if 'items_v5' not in st.session_state:
    st.session_state.items_v5 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except: return None

# --- [1. 정보 입력 (v0.5)] ---
st.header("1. 정보 입력 (v0.5)")
client = st.text_input("🏢 거래처명", key="c_v5")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v5")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v5")
    name = st.text_input("품목명", key="n_v5")
    spec = st.text_input("규격", key="s_v5")
    c3, c4, c5 = st.columns(3)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v5")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v5")
    with c5: tax = st.number_input("세액", value=0, step=100, key="t_v5")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v5.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price, "tax":tax})
        st.rerun()

st.divider()

# --- [2. 거래 내역 리스트 (스크롤 확인용)] ---
st.header("2. 거래 내역 리스트")
if st.session_state.items_v5:
    for i, item in enumerate(st.session_state.items_v5):
        st.info(f"{i+1}. {item['name']} | {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v5 = []
        st.rerun()

st.divider()

# --- [3. 동적 명세서 이미지 생성] ---
if st.button("🚀 내역 개수대로 명세서 만들기", type="primary", use_container_width=True):
    if not st.session_state.items_v5:
        st.warning("내역이 없습니다!")
    else:
        try:
            # 원본 양식 로드
            full_img = Image.open("template.png").convert("RGB")
            
            # 1. 양식 자르기 (좌표는 예시이며, 실제 template.png에 맞춰 미세조정이 필요할 수 있습니다)
            # (상단 부분: 발행일자~제목~표 헤더까지)
            header_img = full_img.crop((0, 0, full_img.width, 390)) 
            # (중간 부분: 실제 내역이 들어가는 빈 줄 한 칸)
            row_template = full_img.crop((0, 390, full_img.width, 428)) 
            # (하단 부분: 합계 칸부터 끝까지)
            footer_img = full_img.crop((0, 910, full_img.width, full_img.height))

            # 2. 새로운 이미지 조립 (내역 개수에 맞게 높이 계산)
            new_height = header_img.height + (row_template.height * len(st.session_state.items_v5)) + footer_img.height
            result_img = Image.new("RGB", (full_img.width, new_height), (255, 255, 255))
            
            # 3. 조각 붙여넣기
            result_img.paste(header_img, (0, 0))
            for i in range(len(st.session_state.items_v5)):
                result_img.paste(row_template, (0, header_img.height + (i * row_template.height)))
            result_img.paste(footer_img, (0, header_img.height + (len(st.session_state.items_v5) * row_template.height)))

            # 4. 글자 쓰기
            draw = ImageDraw.Draw(result_img)
            font_data = get_font()
            font = ImageFont.truetype(font_data, 22) if font_data else ImageFont.load_default()

            # 헤더 정보
            draw.text((220, 85), datetime.now().strftime("%Y-%m-%d"), font=font, fill="black")
            draw.text((150, 125), f"{client} 귀하", font=font, fill="black")

            # 내역 정보
            total_p, total_t = 0, 0
            for i, item in enumerate(st.session_state.items_v5):
                curr_y = header_img.height + (i * row_template.height) + 5
                draw.text((30, curr_y), f"{item['m']}/{item['d']}", font=font, fill="black")
                draw.text((120, curr_y), item['name'], font=font, fill="black")
                draw.text((380, curr_y), item['spec'], font=font, fill="black")
                draw.text((630, curr_y), f"{item['price']:,}", font=font, fill="black")
                total_p += item['price']
                total_t += item['tax']

            # 푸터 합계 (상대 좌표 계산)
            footer_y = header_img.height + (len(st.session_state.items_v5) * row_template.height) + 20
            draw.text((630, footer_y), f"{total_p:,}", font=font, fill="black")

            st.image(result_img)
            buf = io.BytesIO()
            result_img.save(buf, format="PNG")
            st.download_button("📥 저장하기", buf.getvalue(), "invoice.png")
            
        except Exception as e:
            st.error(f"오류: {e}")
