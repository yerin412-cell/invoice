import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v6] ---
if 'items_v6' not in st.session_state:
    st.session_state.items_v6 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return io.BytesIO(font_data)
    except: return None

# --- [1. 정보 입력 (v0.6)] ---
st.header("1. 정보 입력 (v0.6)")
client = st.text_input("🏢 거래처명", key="c_v6")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v6")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v6")
    
    name = st.text_input("품목명", key="n_v6")
    spec = st.text_input("규격", key="s_v6")
    
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v6")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v6")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v6.append({
            "m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

st.divider()

# --- [2. 거래 내역 리스트] ---
st.header("2. 거래 내역 리스트")
if st.session_state.items_v6:
    for i, item in enumerate(st.session_state.items_v6):
        st.markdown(f"**{i+1}. {item['name']}** ({item['m']}/{item['d']}) - {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v6 = []
        st.rerun()

st.divider()

# --- [3. 동적 명세서 이미지 생성] ---
if st.button("🚀 내역 개수대로 명세서 만들기", type="primary", use_container_width=True):
    if not st.session_state.items_v6:
        st.warning("내역이 없습니다!")
    else:
        try:
            # 원본 양식 로드 (상단부만 사용)
            base_img = Image.open("template.png").convert("RGB")
            width, original_height = base_img.size
            
            # 설정값 (이미지에 맞춰 조정 가능)
            header_height = 350  # 표 시작 전까지의 높이
            row_height = 40      # 한 줄당 높이
            footer_height = 150  # 합계 칸 높이
            
            # 새 이미지 생성 (내역 개수에 따라 높이 결정)
            total_height = header_height + (row_height * len(st.session_state.items_v6)) + footer_height
            new_img = Image.new("RGB", (width, total_height), (255, 255, 255))
            
            # 원본의 상단 헤더 복사
            header_part = base_img.crop((0, 0, width, header_height))
            new_img.paste(header_part, (0, 0))
            
            draw = ImageDraw.Draw(new_img)
            font_data = get_font()
            font = ImageFont.truetype(font_data, 18) if font_data else ImageFont.load_default()
            
            # 표 선 그리기 및 데이터 채우기
            total_sum = 0
            for i, item in enumerate(st.session_state.items_v6):
                y = header_height + (i * row_height)
                
                # 가로줄 그리기
                draw.line([(0, y), (width, y)], fill=(0, 0, 0), width=1)
                
                # 데이터 쓰기 (가로 좌표는 양식에 맞춰 미세조정 필요)
                draw.text((20, y+10), f"{item['m']}/{item['d']}", font=font, fill="black")
                draw.text((100, y+10), item['name'], font=font, fill="black")
                draw.text((350, y+10), item['spec'], font=font, fill="black")
                draw.text((450, y+10), str(item['qty']), font=font, fill="black")
                draw.text((550, y+10), f"{item['price']:,}", font=font, fill="black")
                
                total_sum += item['price']
            
            # 푸터(합계) 그리기
            footer_y = header_height + (len(st.session_state.items_v6) * row_height)
            draw.line([(0, footer_y), (width, footer_y)], fill=(0, 0, 0), width=2)
            draw.text((450, footer_y + 20), "합 계", font=font, fill="black")
            draw.text((550, footer_y + 20), f"{total_sum:,}", font=font, fill="black")

            # 헤더 정보 기입
            draw.text((120, 120), f"{client} 귀하", font=font, fill="black")
            draw.text((120, 80), datetime.now().strftime("%Y-%m-%d"), font=font, fill="black")

            st.image(new_img)
            
            buf = io.BytesIO()
            new_img.save(buf, format="PNG")
            st.download_button("📥 이미지 저장", buf.getvalue(), "invoice_v0.6.png")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
