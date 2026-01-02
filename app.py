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
def get_font(size=14):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [1. 정보 입력 영역] ---
st.header("1. 정보 입력 (v1.8)")
client = st.text_input("🏢 거래처명", key="client_v18")

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

# --- [2. 내역 리스트 표시] ---
if st.session_state.my_items:
    st.divider()
    for i, item in enumerate(st.session_state.my_items):
        cols = st.columns([4, 1])
        cols[0].write(f"{i+1}. {item['name']} / {item['price']:,}원")
        if cols[1].button("삭제", key=f"del_{i}"):
            st.session_state.my_items.pop(i)
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

            # 부모님이 알려주신 정밀 좌표 (줄 높이 22픽셀 고정)
            H_TOP = 123        # 첫 줄 시작 (헤더 끝)
            H_ROW = 22         # 줄 높이
            H_FOOT_START = 165 # 원본에서 합계 부분이 시작되는 위치 (알려주신 165 이후)

            # 1. 원본 이미지 조각내기
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 123, W, 145))   # 회색 배경 줄
            row_white = orig.crop((0, 145, W, 167))  # 흰색 배경 줄
            footer = orig.crop((0, H_FOOT_START, W, H))

            # 2. 새 이미지 조립 (찌그러짐 방지를 위해 정확한 배수 계산)
            item_count = len(st.session_state.my_items)
            new_h = H_TOP + (H_ROW * item_count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(header, (0, 0))
            for i in range(item_count):
                y_pos = H_TOP + (i * H_ROW)
                # 홀수(0, 2, 4...)는 회색, 짝수(1, 3, 5...)는 흰색 배경 사용
                line_img = row_gray if i % 2 == 0 else row_white
                res.paste(line_img, (0, y_pos))
            
            # 푸터(합계 부분) 붙이기
            res.paste(footer, (0, H_TOP + (item_count * H_ROW)))

            # 3. 글자 채우기 (숫자 위치 정밀 조정)
            draw = ImageDraw.Draw(res)
            f = get_font(12)      # 칸이 좁으므로 글자 크기를 살짝 줄임
            f_bold = get_font(18) # 합계용 큰 글씨

            # 상단 발행일자 및 거래처 (사진 위치에 맞게 수정)
            draw.text((150, 45), datetime.now().strftime("%Y-%m-%d"), font=f, fill="black")
            draw.text((70, 75), f"{client} 귀하", font=f, fill="black")

            # 내역 채우기 (y축 중앙 정렬 +2 픽셀 조정)
            total = 0
            for i, item in enumerate(st.session_state.my_items):
                curr_y = H_TOP + (i * H_ROW) + 4 # 찌그러짐 방지를 위해 중앙 위치 조정
                draw.text((15, curr_y), f"{item['m']}/{item['d']}", font=f, fill="black")
                draw.text((85, curr_y), item['name'], font=f, fill="black")
                draw.text((250, curr_y), item['spec'], font=f, fill="black")
                draw.text((320, curr_y), str(item['qty']), font=f, fill="black")
                draw.text((430, curr_y), f"{item['price']:,}", font=f, fill="black")
                total += item['price']

            # 상단 및 하단 합계 금액 기입
            draw.text((280, 40), f"{total:,}", font=f_bold, fill="black")
            
            foot_y = H_TOP + (item_count * H_ROW) + 5
            draw.text((430, foot_y), f"{total:,}", font=f, fill="black")

            st.image(res)
            
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 수정된 명세서 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류 발생: {e}")
