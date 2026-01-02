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
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [1. 정보 입력] ---
st.header("1. 정보 입력 (v1.9)")
client = st.text_input("🏢 거래처명", key="client_v19")

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
        st.session_state.my_items.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.rerun()

# --- [2. 명세서 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not st.session_state.my_items: st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 부모님이 알려주신 새로운 정밀 좌표 (픽셀)
            H_TOP = 345        # 헤더 끝 (첫 줄 시작)
            H_ROW = 62         # 줄 높이 (407 - 345)
            # 합계(Footer)는 원본 이미지의 맨 아래 '합계' 글자가 있는 부분 (약 850 이후로 추정되나 동적 처리)
            H_FOOT_START = 850 

            # 1. 원본 조각 추출
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 345, W, 407))   # 홀수 (회색)
            row_white = orig.crop((0, 407, W, 467))  # 짝수 (흰색)
            footer = orig.crop((0, H_FOOT_START, W, H))

            # 2. 이미지 조립
            count = len(st.session_state.my_items)
            new_h = H_TOP + (H_ROW * count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(header, (0, 0))
            for i in range(count):
                y_pos = H_TOP + (i * H_ROW)
                line_img = row_gray if i % 2 == 0 else row_white
                # 줄 이미지를 칸 높이에 맞게 미세하게 리사이즈하여 찌그러짐 방지
                line_img = line_img.resize((W, H_ROW))
                res.paste(line_img, (0, y_pos))
            
            res.paste(footer, (0, H_TOP + (count * H_ROW)))

            # 3. 글자 채우기
            draw = ImageDraw.Draw(res)
            f_content = get_font(28) # 줄 높이가 60이므로 글자를 크게 키움
            f_sum = get_font(35)

            # 상단 정보 (발행일자, 거래처)
            draw.text((250, 60), datetime.now().strftime("%Y-%m-%d"), font=f_content, fill="black")
            draw.text((150, 160), f"{client} 귀하", font=f_content, fill="black")

            # 내역 입력 (중앙 정렬 조정)
            total = 0
            for i, item in enumerate(st.session_state.my_items):
                curr_y = H_TOP + (i * H_ROW) + 15 # 칸 중앙 위치
                draw.text((40, curr_y), f"{item['m']}/{item['d']}", font=f_content, fill="black")
                draw.text((200, curr_y), item['name'], font=f_content, fill="black")
                draw.text((550, curr_y), str(item['qty']), font=f_content, fill="black")
                draw.text((800, curr_y), f"{item['price']:,}", font=f_content, fill="black")
                total += item['price']

            # 합계 기입
            draw.text((450, 240), f"{total:,}", font=f_sum, fill="black") # 상단 합계
            
            # 결과 출력
            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 완성된 명세서 저장", buf.getvalue(), "invoice_final.png")

        except Exception as e:
            st.error(f"오류: {e}")
