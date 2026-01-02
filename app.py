import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [안전장치: 데이터 저장소 확인] ---
# 이 부분이 가장 위에 있어야 오류가 안 납니다.
if 'items' not in st.session_state or st.session_state.items is None:
    st.session_state.items = []

# --- [자동 폰트 로드] ---
@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except:
        return None

st.set_page_config(page_title="우리집 거래명세서", layout="centered")

# --- [1번 창: 입력 영역] ---
st.header("1. 정보 입력")
client = st.text_input("🏢 거래처명", placeholder="예: 가나다 상사", key="client_name")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="in_m")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="in_d")
    
    name = st.text_input("품목명", key="in_name")
    spec = st.text_input("규격", key="in_spec")
    
    col3, col4 = st.columns(2)
    with col3: qty = st.selectbox("수량", [1.0, 0.5], key="in_qty")
    with col4: price = st.number_input("금액", step=100, key="in_price")

# 추가 버튼
if st.button("➕ 추가하기", use_container_width=True):
    if name:
        new_item = {"m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price}
        st.session_state.items.append(new_item)
        st.rerun()
    else:
        st.warning("품목명을 입력해주세요.")

st.divider()

# --- [2번 창: 거래 내역 리스트] ---
st.header("2. 거래 내역 리스트")

# 리스트가 비어있지 않을 때만 화면에 그리기
if st.session_state.get('items'):
    for i, item in enumerate(st.session_state.items):
        st.markdown(f"✅ **{i+1}. {item['name']}** ({item['m']}/{item['d']}) - {item['price']:,}원")
    
    if st.button("🗑️ 리스트 비우기"):
        st.session_state.items = []
        st.rerun()
else:
    st.info("아직 추가된 내역이 없습니다. 위에서 입력 후
