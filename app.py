import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v1.4] ---
if 'items_v14' not in st.session_state:
    st.session_state.items_v14 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font(size=20):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [1. 정보 입력] ---
st.header("1. 정보 입력 (v1.4)")
client = st.text_input("🏢 거래처명", key="c_v14")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v14")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v14")
    name = st.text_input("품목명", key="n_v14")
    spec = st.text_input("규격", key="s_v14")
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v14")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v14")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v14.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.rerun()

st.divider()

# --- [2. 명세서 이미지 생성] ---
if st.button("🚀 엑셀 양식 그대로 늘리기", type="primary", use_container_width=True):
    if not st.session_state.items_v14:
        st.warning("내역을 추가해주세요!")
    else:
        try:
            # 1. 원본 이미지 로드
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 2. 이미지 정밀 절단 (부모님 양식 기준)
            # 헤더: 맨 위부터 '월일/품목' 글자 있는 곳까지
            header = orig.crop((0, 0, W, 315)) 
            # 몸통: 데이터가 들어갈 빈 줄 딱 한 칸 (높이 약 38픽셀)
            row_unit = orig.crop((0, 315, W, 353))
            # 꼬리: 맨 아래 '합계' 칸 부분 (이미지 하단부)
            footer = orig.crop((0, 910, W, H))

            # 3. 새로운 도화지 만들기 (헤더 + 내역수*줄 + 꼬리)
            new_h = header.height + (row_unit.height * len(st.session_state.items_v14)) + footer.height
            result_img = Image.new("RGB", (W, new_h), (255, 255, 255))

            # 4. 조립 (이어 붙이기)
            result_img.paste(header, (0, 0))
            for i in range(len(st.session_state.items_v14)):
                y_pos = header.height + (i * row_unit.height)
                result_img.paste(row_unit, (0, y_pos))
            result_img.paste(footer, (0, header.height + (len(st.session_state.items_v14) * row_unit.height)))

            # 5. 글자 쓰기
            draw = ImageDraw.Draw(result_img)
            f = get_font(20)

            # 상단 거래처 등 기입
            draw.text((220, 85), datetime.now().strftime("%Y-%m-%d"), font=f, fill="black")
            draw.text((125, 125), f"{client} 귀하", font=f, fill="black")

            # 내역 기입
            total = 0
            for i, item in enumerate(st.session_state.items_v14):
                curr_y = header.height + (i * row_unit.height) + 8
                draw.text((35, curr_y), f"{item['m']}/{item['d']}", font=f, fill="black")
                draw.text((140, curr_y), item['name'], font=f, fill="black")
                draw.text((630, curr_y), f"{item['price']:,}", font=f, fill="black")
                total += item['price']

            # 합계 기입 (꼬리 부분)
            foot_y = header.height + (len(st.session_state.items_v14) * row_unit.height) + 20
            draw.text((630, foot_y), f"{total:,}", font=f, fill="black")

            st.image(result_img)
            
            buf = io.BytesIO()
            result_img.save(buf, format="PNG")
            st.download_button("📥 이미지 저장", buf.getvalue(), "invoice.png")

        except Exception as e:
            st.error(f"오류: {e}")
