import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [1. 자동 폰트 로드] ---
@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except:
        return None

st.set_page_config(page_title="간편 거래명세서", layout="centered")

# 데이터 저장소 초기화 (오류 방지용)
if 'items' not in st.session_state:
    st.session_state.items = []

# --- [2. 1번 창: 입력 영역] ---
st.header("1. 정보 입력")
client = st.text_input("🏢 거래처명", placeholder="예: 가나다 상사")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="input_m")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="input_d")
    
    name = st.text_input("품목명", key="input_name")
    spec = st.text_input("규격", key="input_spec")
    
    col3, col4 = st.columns(2)
    with col3: qty = st.selectbox("수량", [1.0, 0.5], key="input_qty")
    with col4: price = st.number_input("금액", step=100, key="input_price")

# 추가 버튼 클릭 시 동작
if st.button("➕ 추가하기"):
    if name:
        # 새로운 아이템 생성
        new_item = {
            "m": m, 
            "d": d, 
            "name": name, 
            "spec": spec, 
            "qty": qty, 
            "price": price
        }
        # 목록에 추가
        st.session_state.items.append(new_item)
        st.toast(f"'{name}' 추가 완료!")
        st.rerun() # 화면을 즉시 새로고침해서 리스트에 반영
    else:
        st.warning("품목명을 입력해주세요.")

st.divider()

# --- [3. 2번 창: 거래 내역 리스트] ---
st.header("2. 거래 내역 리스트")
if st.session_state.items:
    for i, item in enumerate(st.session_state.items):
        st.markdown(f"**{i+1}. {item['name']}** ({item['m']}/{item['d']}) - {item['price']:,}원")
    
    if st.button("🗑️ 리스트 비우기"):
        st.session_state.items = []
        st.rerun()
else:
    st.info("추가된 내역이 없습니다.")

st.divider()

# --- [4. 3번 창: 이미지 생성] ---
if st.button("🚀 거래명세서 사진 만들기", type="primary"):
    if not client:
        st.warning("거래처명을 입력해주세요!")
    elif not st.session_state.items:
        st.warning("내역을 먼저 추가해주세요!")
    else:
        try:
            img = Image.open("template.png").convert("RGB")
            draw = ImageDraw.Draw(img)
            
            font_data = get_font()
            font = ImageFont.truetype(font_data, 25) if font_data else ImageFont.load_default()

            # 날짜와 거래처 (좌표는 예시)
            draw.text((120, 160), datetime.now().strftime("%Y  %m  %d"), font=font, fill="black")
            draw.text((120, 260), f"{client} 귀하", font=font, fill="black")
            
            y_pos = 455
            total_sum = 0
            for item in st.session_state.items:
                draw.text((55, y_pos), item['m'], font=font, fill="black")
                draw.text((100, y_pos), item['d'], font=font, fill="black")
                draw.text((160, y_pos), item['name'], font=font, fill="black")
                draw.text((640, y_pos), f"{item['price']:,}", font=font, fill="black")
                total_sum += item['price']
                y_pos += 38 # 줄 간격
            
            # 합계
            draw.text((640, 925), f"{total_sum:,}", font=font, fill="black")

            st.image(img)
            
            # 이미지 저장용 버튼
            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG")
            st.download_button("📥 핸드폰에 사진 저장", img_buf.getvalue(), f"명세서_{client}.png")
            
        except Exception as e:
            st.error(f"이미지 생성 중 오류: {e}")
