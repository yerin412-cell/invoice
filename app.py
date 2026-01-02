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
def get_font(size=18):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [1. 정보 입력 영역] ---
st.header("1. 정보 입력 (v1.7)")
client = st.text_input("🏢 거래처명", key="client_name_v17")

with st.container():
    col1, col2 = st.columns(2)
    with col1: m = st.text_input("월", value=datetime.now().strftime("%m"))
    with col2: d = st.text_input("일", value=datetime.now().strftime("%d"))
    
    name = st.text_input("품목명")
    spec = st.text_input("규격")
    
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5)
    with c4: price = st.number_input("공급가액", value=0, step=1000)

if st.button("➕ 추가하기", use_container_width=True):
    if name:
        st.session_state.my_items.append({
            "m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

# --- [2. 내역 리스트 표시 및 삭제] ---
if st.session_state.my_items:
    st.divider()
    st.subheader("📋 입력된 내역")
    for i, item in enumerate(st.session_state.my_items):
        cols = st.columns([4, 1])
        cols[0].write(f"{i+1}. {item['name']} / {item['price']:,}원")
        if cols[1].button("삭제", key=f"del_{i}"):
            st.session_state.my_items.pop(i)
            st.rerun()
    if st.button("🗑️ 전체 삭제"):
        st.session_state.my_items = []
        st.rerun()

st.divider()

# --- [3. 정밀 조립 및 이미지 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 입력해주세요.")
    elif not st.session_state.my_items: st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 부모님이 알려주신 정밀 좌표
            H_TOP = 123        # 첫 줄 시작 (헤더 끝)
            H_ROW = 22         # 줄 높이 (145 - 123)
            H_FOOT_START = 330 # 원본에서 '합계'가 시작되는 대략적인 위치 (이미지 하단부)

            # 1. 원본에서 조각 추출
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 123, W, 145))  # 홀수줄 (회색)
            row_white = orig.crop((0, 145, W, 167)) # 짝수줄 (흰색) - 145+22=167
            footer = orig.crop((0, H_FOOT_START, W, H))

            # 2. 새 이미지 조립
            item_count = len(st.session_state.my_items)
            new_h = H_TOP + (H_ROW * item_count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(header, (0, 0))
            for i in range(item_count):
                y_pos = H_TOP + (i * H_ROW)
                # 홀수는 회색줄, 짝수는 흰색줄 사용
                row_img = row_gray if i % 2 == 0 else row_white
                res.paste(row_img, (0, y_pos))
            
            res.paste(footer, (0, H_TOP + (item_count * H_ROW)))

            # 3. 글자 채우기
            draw = ImageDraw.Draw(res)
            f = get_font(14) # 줄 높이가 22이므로 글자는 작게
            f_title = get_font(24)

            # 상단 정보 (위치는 이미지에 맞게 조정)
            draw.text((75, 45), datetime.now().strftime("%Y-%m-%d"), font=f, fill="black")
            draw.text((75, 75), f"{client} 귀하", font=f, fill="black")

            # 내역 채우기
            total = 0
            for i, item in enumerate(st.session_state.my_items):
                curr_y = H_TOP + (i * H_ROW) + 2
                draw.text((10, curr_y), f"{item['m']}/{item['d']}", font=f, fill="black")
                draw.text((85, curr_y), item['name'], font=f, fill="black")
                draw.text((320, curr_y), str(item['qty']), font=f, fill="black")
                draw.text((450, curr_y), f"{item['price']:,}", font=f, fill="black")
                total += item['price']

            # 합계 (상단 및 하단)
            draw.text((250, 45), f"{total:,}", font=f_title, fill="black")
            foot_y = H_TOP + (item_count * H_ROW) + 5
            draw.text((450, foot_y), f"{total:,}", font=f, fill="black")

            st.image(res)
            
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 이미지 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
