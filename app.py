import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [자동 폰트 로드 함수] ---
@st.cache_resource
def get_font():
    # 구글 폰트 저장소에서 나눔고딕 폰트를 자동으로 가져옵니다.
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except:
        return None # 실패 시 기본 폰트 사용

st.set_page_config(page_title="간편 거래명세서", layout="centered")

# 데이터 저장소
if 'items' not in st.session_state:
    st.session_state.items = []

# --- 1번: 입력창 ---
st.header("1. 정보 입력")
client = st.text_input("🏢 거래처명", placeholder="예: 가나다 상사")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"))
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"))
    
    name = st.text_input("품목명")
    spec = st.text_input("규격")
    
    col3, col4 = st.columns(2)
    with col3: qty = st.selectbox("수량", [1.0, 0.5])
    with col4: price = st.number_input("금액", step=100)

if st.button("➕ 추가하기"):
    if name:
        st.session_state.items.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.toast("목록에 추가됐습니다!")

st.divider()

# --- 2번: 리스트 (스크롤) ---
st.header("2. 거래 내역 리스트")
if st.session_state.items:
    for i, item in enumerate(st.session_state.items):
        st.write(f"**{i+1}. {item['name']}** ({item['m']}/{item['d']}) - {item['price']:,}원")
    
    if st.button("🗑️ 리스트 비우기"):
        st.session_state.items = []
        st.rerun()

st.divider()

# --- 3번: 이미지 생성 ---
if st.button("🚀 거래명세서 사진 만들기", type="primary"):
    if not client:
        st.warning("거래처명을 써주세요!")
    elif not st.session_state.items:
        st.warning("내역을 추가해주세요!")
    else:
        try:
            img = Image.open("template.png").convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # 폰트 자동 로드 적용
            font_data = get_font()
            if font_data:
                font = ImageFont.truetype(font_data, 25)
            else:
                font = ImageFont.load_default() # 최악의 경우 기본폰트

            # 위치 입력 (좌표는 보내주신 이미지 기준 대략값입니다)
            draw.text((120, 160), datetime.now().strftime("%Y  %m  %d"), font=font, fill="black")
            draw.text((120, 260), f"{client} 귀하", font=font, fill="black")
            
            y = 455
            total = 0
            for item in st.session_state.items:
                draw.text((55, y), item['m'], font=font, fill="black")
                draw.text((100, y), item['d'], font=font, fill="black")
                draw.text((160, y), item['name'], font=font, fill="black")
                draw.text((640, y), f"{item['price']:,}", font=font, fill="black")
                total += item['price']
                y += 38
            
            draw.text((640, 925), f"{total:,}", font=font, fill="black")

            st.image(img)
            
            # 다운로드 버튼
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.download_button("📥 핸드폰에 사진 저장", buf.getvalue(), "invoice.png")
            
        except FileNotFoundError:
            st.error("template.png(엑셀 양식 이미지) 파일이 없습니다. 파일을 같이 올려주세요!")
