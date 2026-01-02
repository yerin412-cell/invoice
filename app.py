import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [안전장치: 데이터 저장소 초기화] ---
# 가장 먼저 실행되어야 하며, 기존에 데이터가 있더라도 형식을 확실히 맞춥니다.
if 'items' not in st.session_state:
    st.session_state.items = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

# --- [자동 폰트 로드] ---
@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except:
        return None

# --- [1번 창: 정보 입력] ---
st.header("1. 정보 입력")
client = st.text_input("🏢 거래처명", placeholder="예: 가나다 상사", key="client_main")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_val")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_val")
    
    name = st.text_input("품목명", key="n_val")
    spec = st.text_input("규격", key="s_val")
    
    col3, col4 = st.columns(2)
    with col3: qty = st.selectbox("수량", [1.0, 0.5], key="q_val")
    with col4: price = st.number_input("금액", step=100, key="p_val")

# 추가 버튼 (작동 방식을 더 안전하게 변경)
if st.button("➕ 추가하기", use_container_width=True):
    if name:
        # 리스트가 어떤 이유로든 날아갔을 경우를 대비한 2중 체크
        if not isinstance(st.session_state.items, list):
            st.session_state.items = []
            
        new_row = {"m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price}
        st.session_state.items.append(new_row)
        st.toast(f"'{name}' 추가됨!")
        st.rerun()
    else:
        st.warning("품목명을 입력해주세요.")

st.divider()

# --- [2번 창: 거래 내역 리스트] ---
st.header("2. 거래 내역 리스트")

# 리스트 내용 출력
if st.session_state.items:
    for i, item in enumerate(st.session_state.items):
        st.markdown(f"✅ **{i+1}. {item['name']}** ({item['m']}/{item['d']}) - {item['price']:,}원")
    
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items = []
        st.rerun()
else:
    st.info("내역이 없습니다. 위에서 입력 후 [추가하기]를 누르세요.")

st.divider()

# --- [3번 창: 이미지 생성] ---
if st.button("🚀 거래명세서 사진 만들기", type="primary", use_container_width=True):
    if not client:
        st.warning("거래처명을 적어주세요!")
    elif not st.session_state.items:
        st.warning("내역을 먼저 추가하세요!")
    else:
        try:
            img = Image.open("template.png").convert("RGB")
            draw = ImageDraw.Draw(img)
            
            font_data = get_font()
            font = ImageFont.truetype(font_data, 25) if font_data else ImageFont.load_default()

            # (좌표는 예시입니다. 나중에 미세조정 필요)
            draw.text((120, 160), datetime.now().strftime("%Y  %m  %d"), font=font, fill="black")
            draw.text((120, 260), f"{client} 귀하", font=font, fill="black")
            
            y_start = 455
            total = 0
            for item in st.session_state.items:
                draw.text((55, y_start), item['m'], font=font, fill="black")
                draw.text((100, y_start), item['d'], font=font, fill="black")
                draw.text((160, y_start), item['name'], font=font, fill="black")
                draw.text((640, y_start), f"{item['price']:,}", font=font, fill="black")
                total += item['price']
                y_start += 38
            
            draw.text((640, 925), f"{total:,}", font=font, fill="black")

            st.image(img)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.download_button("📥 사진 저장", buf.getvalue(), f"명세서_{client}.png")
            
        except Exception as e:
            st
