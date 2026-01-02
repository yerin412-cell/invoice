import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화] ---
if 'my_items' not in st.session_state:
    st.session_state.my_items = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font(size=25):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(io.BytesIO(urllib.request.urlopen(font_url).read()).getvalue()), size)
    except:
        return ImageFont.load_default()

# --- [1. 거래처 및 내역 입력] ---
st.header("1. 명세서 작성 (v2.3)")

# 거래처명은 상단에서 한 번만 입력
client = st.text_input("🏢 거래처명 (한 번만 입력하세요)", key="client_fixed")

st.subheader("📋 내역 입력")
with st.container():
    c_date1, c_date2 = st.columns(2)
    with c_date1: m = st.text_input("월", value=datetime.now().strftime("%m"))
    with c_date2: d = st.text_input("일", value=datetime.now().strftime("%d"))
    
    name = st.text_input("품목명")
    spec = st.text_input("규격")
    
    c_qty, c_price = st.columns(2)
    with c_qty: qty = st.number_input("수량", value=1.0, step=0.5)
    with c_price: price = st.number_input("공급가액", value=0, step=1000)

if st.button("➕ 품목 추가하기", use_container_width=True):
    if name:
        st.session_state.my_items.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.rerun()

# --- [2. 현재 리스트 확인 및 삭제] ---
if st.session_state.my_items:
    st.divider()
    for i, item in enumerate(st.session_state.my_items):
        cols = st.columns([4, 1])
        cols[0].write(f"{i+1}. {item['name']} ({item['m']}/{item['d']}) - {item['price']:,}원")
        if cols[1].button("삭제", key=f"del_{i}"):
            st.session_state.my_items.pop(i)
            st.rerun()
    if st.button("🗑️ 전체 내역 삭제"):
        st.session_state.my_items = []
        st.rerun()

st.divider()

# --- [3. 명세서 이미지 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 입력해주세요.")
    elif not st.session_state.my_items: st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 부모님이 알려주신 정밀 좌표 (줄 높이 불균형 해결)
            H_TOP = 345        
            H_ROW1 = 62        # 첫 줄 (345~407)
            H_ROW2 = 60        # 둘째 줄 (407~467)
            
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 345, W, 407))   # 홀수줄
            row_white = orig.crop((0, 407, W, 467))  # 짝수줄
            footer = orig.crop((0, H - 75, W, H))

            # 이미지 조립
            count = len(st.session_state.my_items)
            # 줄마다 높이가 다르므로 누적 계산
            new_h = H_TOP + sum(H_ROW1 if i % 2 == 0 else H_ROW2 for i in range(count)) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(header, (0, 0))
            current_y = H_TOP
            for i in range(count):
                row_img = row_gray if i % 2 == 0 else row_white
                res.paste(row_img, (0, current_y))
                current_y += (H_ROW1 if i % 2 == 0 else H_ROW2)
            
            res.paste(footer, (0, current_y))

            # 3. 글자 채우기 (이미지 기반 위치 재조정)
            draw = ImageDraw.Draw(res)
            f_small = get_font(24)
            f_mid = get_font(28)
            f_large = get_font(38)

            # 상단 정보 (박스 중앙에 오도록 조정)
            draw.text((160, 40), datetime.now().strftime("%Y-%m-%d"), font=f_mid, fill="black")
            draw.text((160, 100), f"{client} 귀하", font=f_mid, fill="black")

            # 내역 입력
            total = 0
            current_y = H_TOP
            for i, item in enumerate(st.session_state.my_items):
                row_h = H_ROW1 if i % 2 == 0 else H_ROW2
                text_y = current_y + (row_h // 2) - 15 # 칸 중앙 정렬
                
                draw.text((35, text_y), f"{item['m']}/{item['d']}", font=f_mid, fill="black")
                draw.text((180, text_y), item['name'], font=f_mid, fill="black")
                draw.text((430, text_y), item['spec'], font=f_mid, fill="black")
                draw.text((540, text_y), str(item['qty']), font=f_mid, fill="black")
                draw.text((720, text_y), f"{item['price']:,}", font=f_mid, fill="black")
                draw.text((910, text_y), "0", font=f_mid, fill="black") # 세액 0 고정
                
                total += item['price']
                current_y += row_h

            # 합계 금액 (상단 큰 회색 칸)
            draw.text((300, 195), f"{total:,}", font=f_large, fill="black")

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 명세서 이미지 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류: {e}")
