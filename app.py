import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - v1.3] ---
if 'items_v13' not in st.session_state:
    st.session_state.items_v13 = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

# --- [1. 폰트 로드: 한글 깨짐 방지] ---
@st.cache_resource
def get_font(size=20):
    # 나눔고딕 폰트를 인터넷에서 직접 가져와 사용합니다.
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [2. 정보 입력 (v1.3)] ---
st.header("1. 정보 입력 (v1.3)")
client = st.text_input("🏢 거래처명", key="c_v13")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"), key="m_v13")
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"), key="d_v13")
    
    name = st.text_input("품목명", key="n_v13")
    spec = st.text_input("규격", key="s_v13")
    
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5, key="q_v13")
    with c4: price = st.number_input("공급가액", value=0, step=1000, key="p_v13")

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.items_v13.append({
            "m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

st.divider()

# --- [3. 거래 내역 리스트] ---
st.header("2. 현재 입력된 내역")
if st.session_state.items_v13:
    for i, item in enumerate(st.session_state.items_v13):
        st.write(f"✅ {i+1}. {item['name']} | {item['price']:,}원")
    if st.button("🗑️ 전체 삭제"):
        st.session_state.items_v13 = []
        st.rerun()
else:
    st.info("내역이 없습니다.")

st.divider()

# --- [4. 명세서 이미지 생성] ---
if st.button("🚀 내역 수에 맞춰 명세서 생성", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 적어주세요!")
    elif not st.session_state.items_v13: st.warning("내역을 추가해주세요!")
    else:
        try:
            # 설정값
            W = 800
            H_HEADER = 200  # 상단 높이
            H_ROW = 50     # 내역 한 줄 높이
            H_FOOTER = 100  # 합계 높이
            
            items = st.session_state.items_v13
            total_h = H_HEADER + (H_ROW * (len(items) + 1)) + H_FOOTER
            
            # 새 이미지 생성 (흰색 배경)
            img = Image.new("RGB", (W, total_h), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # 폰트 가져오기
            f_normal = get_font(20)
            f_big = get_font(35)

            # 1. 상단 테두리 및 제목
            draw.rectangle([10, 10, W-10, total_h-10], outline="black", width=2)
            draw.text((W//2-100, 30), "거 래 명 세 서", font=f_big, fill="black")
            draw.text((30, 100), f"발행일자: {datetime.now().strftime('%Y-%m-%d')}", font=f_normal, fill="black")
            draw.text((30, 140), f"거래처명: {client} 귀하", font=f_normal, fill="black")

            # 2. 표 헤더 (회색 배경)
            y_tab = 180
            draw.rectangle([20, y_tab, W-20, y_tab + H_ROW], fill=(220, 220, 220), outline="black")
            h_titles = ["월/일", "품목명", "규격", "수량", "공급가액"]
            h_xs = [40, 150, 400, 520, 650]
            for txt, x in zip(h_titles, h_xs):
                draw.text((x, y_tab + 12), txt, font=f_normal, fill="black")

            # 3. 내역 줄 (데이터 수만큼 반복 생성)
            total_sum = 0
            for i, item in enumerate(items):
                curr_y = y_tab + H_ROW + (i * H_ROW)
                # 회색/흰색 번갈아 색칠
                bg = (245, 245, 245) if i % 2 == 0 else (255, 255, 255)
                draw.rectangle([20, curr_y, W-20, curr_y + H_ROW], fill=bg, outline="black")
                
                # 데이터 쓰기
                draw.text((40, curr_y + 12), f"{item['m']}/{item['d']}", font=f_normal, fill="black")
                draw.text((150, curr_y + 12), item['name'], font=f_normal, fill="black")
                draw.text((400, curr_y + 12), item['spec'], font=f_normal, fill="black")
                draw.text((530, curr_y + 12), str(item['qty']), font=f_normal, fill="black")
                draw.text((650, curr_y + 12), f"{item['price']:,}", font=f_normal, fill="black")
                total_sum += item['price']

            # 4. 하단 합계 영역
            y_foot = y_tab + H_ROW + (len(items) * H_ROW)
            draw.rectangle([20, y_foot, W-20, y_foot + H_FOOTER], fill=(200, 200, 200), outline="black")
            draw.text((400, y_foot + 35), "합 계 금 액 (원)", font=f_normal, fill="black")
            draw.text((650, y_foot + 35), f"{total_sum:,}", font=f_normal, fill="black")

            # 결과물 출력
            st.image(img)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.download_button("📥 이미지 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"생성 중 오류: {e}")
