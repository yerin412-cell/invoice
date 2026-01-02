import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화 - 이름을 고정합니다] ---
if 'my_items' not in st.session_state:
    st.session_state.my_items = []

st.set_page_config(page_title="간편 거래명세서", layout="centered")

@st.cache_resource
def get_font(size=20):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [1. 정보 입력 영역] ---
st.header("1. 정보 입력 (v1.5)")
client = st.text_input("🏢 거래처명", key="client_name")

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
        # 입력한 내용을 바구니에 넣습니다.
        st.session_state.my_items.append({
            "m": m, "d": d, "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

st.divider()

# --- [2. 내역 리스트 확인 영역] ---
st.header("2. 현재 입력된 내역")
if st.session_state.my_items:
    # 이 부분이 있어야 화면에 리스트가 보입니다!
    for i, item in enumerate(st.session_state.my_items):
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.write(f"✅ {i+1}. {item['name']} ({item['m']}/{item['d']}) - {item['price']:,}원")
        with col_b:
            if st.button("삭제", key=f"del_{i}"):
                st.session_state.my_items.pop(i)
                st.rerun()
    
    if st.button("🗑️ 전체 삭제", type="secondary"):
        st.session_state.my_items = []
        st.rerun()
else:
    st.info("아직 입력된 내역이 없습니다. 위에서 품목을 입력하고 '추가하기'를 눌러주세요.")

st.divider()

# --- [3. 엑셀 양식 조립 및 생성 영역] ---
if st.button("🚀 엑셀 양식 그대로 늘리기", type="primary", use_container_width=True):
    if not client: st.warning("거래처명을 적어주세요!")
    elif not st.session_state.my_items: st.warning("내역을 먼저 추가해주세요!")
    else:
        try:
            # 1. 부모님이 주신 엑셀 이미지 로드
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 2. 이미지 정밀 절단 (좌표는 부모님 이미지에 맞춰 미세조정 필요)
            header = orig.crop((0, 0, W, 315))         # 머리: 제목부터 항목 이름까지
            row_unit = orig.crop((0, 315, W, 353))     # 몸통: 빈 줄 한 칸 (높이 약 38)
            footer = orig.crop((0, 910, W, H))         # 꼬리: 합계 부분

            # 3. 내역 개수에 맞춰 새 도화지 생성
            new_h = header.height + (row_unit.height * len(st.session_state.my_items)) + footer.height
            result_img = Image.new("RGB", (W, new_h), (255, 255, 255))

            # 4. 조립하기 (이어 붙이기)
            result_img.paste(header, (0, 0))
            for i in range(len(st.session_state.my_items)):
                y_pos = header.height + (i * row_unit.height)
                result_img.paste(row_unit, (0, y_pos))
            result_img.paste(footer, (0, header.height + (len(st.session_state.my_items) * row_unit.height)))

            # 5. 글자 채우기
            draw = ImageDraw.Draw(result_img)
            f = get_font(20)
            f_bold = get_font(28)

            # 상단 정보
            draw.text((220, 85), datetime.now().strftime("%Y-%m-%d"), font=f, fill="black")
            draw.text((125, 125), f"{client} 귀하", font=f, fill="black")

            # 내역 정보 채우기
            total_sum = 0
            for i, item in enumerate(st.session_state.my_items):
                curr_y = header.height + (i * row_unit.height) + 8
                draw.text((35, curr_y), f"{item['m']}/{item['d']}", font=f, fill="black")
                draw.text((140, curr_y), item['name'], font=f, fill="black")
                draw.text((400, curr_y), item['spec'], font=f, fill="black")
                draw.text((500, curr_y), str(item['qty']), font=f, fill="black")
                draw.text((630, curr_y), f"{item['price']:,}", font=f, fill="black")
                total_sum += item['price']

            # 합계 정보 (맨 아래 꼬리 부분)
            foot_y = header.height + (len(st.session_state.my_items) * row_unit.height) + 20
            draw.text((630, foot_y), f"{total_sum:,}", font=f, fill="black")
            # 상단 큰 합계 칸
            draw.text((300, 240), f"{total_sum:,}", font=f_bold, fill="black")

            # 결과물 보여주기
            st.image(result_img)
            
            buf = io.BytesIO()
            result_img.save(buf, format="PNG")
            st.download_button("📥 이미지 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"이미지 생성 중 오류가 발생했습니다: {e}")
