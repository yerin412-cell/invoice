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

# --- [1. 정보 입력 영역] ---
st.header("1. 정보 입력 (v2.1)")
client = st.text_input("🏢 거래처명", key="client_v21")

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

st.divider()

# --- [2. 내역 리스트 확인] ---
st.header("2. 현재 입력된 내역")
if st.session_state.my_items:
    for i, item in enumerate(st.session_state.my_items):
        c_a, c_b = st.columns([4, 1])
        with c_a:
            st.write(f"✅ {i+1}. {item['name']} ({item['m']}/{item['d']}) - {item['price']:,}원")
        with c_b:
            if st.button("삭제", key=f"del_{i}"):
                st.session_state.my_items.pop(i)
                st.rerun()
    if st.button("🗑️ 전체 삭제"):
        st.session_state.my_items = []
        st.rerun()
else:
    st.info("아직 입력된 내역이 없습니다. 위에서 '추가하기'를 눌러주세요.")

st.divider()

# --- [3. 명세서 이미지 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not st.session_state.my_items: st.warning("내역을 먼저 추가해주세요!")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 부모님이 알려주신 좌표 기준 (에러 방지를 위해 끝값 조정)
            H_TOP = 345        
            H_ROW = 60         # 405 - 345 정도로 안전하게 설정
            
            # 1. 원본 조각 추출 (부모님이 주신 template.png의 실제 크기 안에서만 자름)
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 345, W, min(405, H)))   # 첫 줄 (회색)
            row_white = orig.crop((0, 405, W, min(465, H)))  # 둘째 줄 (흰색)
            
            # 푸터: '합계' 글자가 있는 아래쪽 영역 (전체 높이에서 밑부분 추출)
            footer_h = 100 # 하단 푸터 높이 임의 설정 (이미지에 따라 조절 가능)
            footer = orig.crop((0, H - footer_h, W, H))

            # 2. 이미지 조립
            count = len(st.session_state.my_items)
            new_h = H_TOP + (H_ROW * count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(header, (0, 0))
            for i in range(count):
                y_pos = H_TOP + (i * H_ROW)
                line_img = row_gray if i % 2 == 0 else row_white
                line_img = line_img.resize((W, H_ROW)) # 찌그러짐 방지
                res.paste(line_img, (0, y_pos))
            
            res.paste(footer, (0, H_TOP + (count * H_ROW)))

            # 3. 글자 채우기
            draw = ImageDraw.Draw(res)
            f_content = get_font(28)
            f_sum = get_font(35)

            # 상단 정보 기입
            draw.text((250, 60), datetime.now().strftime("%Y-%m-%d"), font=f_content, fill="black")
            draw.text((150, 160), f"{client} 귀하", font=f_content, fill="black")

            # 내역 입력 (중앙 정렬)
            total = 0
            for i, item in enumerate(st.session_state.my_items):
                curr_y = H_TOP + (i * H_ROW) + 12
                draw.text((30, curr_y), f"{item['m']}/{item['d']}", font=f_content, fill="black")
                draw.text((180, curr_y), item['name'], font=f_content, fill="black")
                draw.text((430, curr_y), item['spec'], font=f_content, fill="black")
                draw.text((550, curr_y), str(item['qty']), font=f_content, fill="black")
                draw.text((780, curr_y), f"{item['price']:,}", font=f_content, fill="black")
                total += item['price']

            # 합계 금액 (상단 회색 칸 위치로 추정)
            draw.text((450, 240), f"{total:,}", font=f_sum, fill="black")

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 완성된 명세서 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"이미지 생성 중 오류: {e}")
