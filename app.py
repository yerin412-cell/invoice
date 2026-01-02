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

# 오른쪽 정렬 함수 (글자 폭을 계산해서 위치 조절)
def draw_right(draw, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    draw.text((x_end - w, y), str(text), font=font, fill=fill)

# 중앙 정렬 함수
def draw_center(draw, x_start, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    center = x_start + (x_end - x_start) / 2
    draw.text((center - w / 2, y), str(text), font=font, fill=fill)

# --- [1. 정보 입력] ---
st.header("1. 명세서 작성 (v2.4)")
client = st.text_input("🏢 거래처명", key="client_v24")

with st.container():
    c1, c2 = st.columns(2)
    with c1: m = st.text_input("월", value=datetime.now().strftime("%m"))
    with c2: d = st.text_input("일", value=datetime.now().strftime("%d"))
    name = st.text_input("품목명")
    spec = st.text_input("규격")
    c3, c4 = st.columns(2)
    with c3: qty = st.number_input("수량", value=1.0, step=0.5)
    with c4: price = st.number_input("공급가액", value=0, step=1000)

if st.button("➕ 품목 추가하기", use_container_width=True):
    if name:
        st.session_state.my_items.append({"m":m, "d":d, "name":name, "spec":spec, "qty":qty, "price":price})
        st.rerun()

# --- [2. 리스트 확인] ---
if st.session_state.my_items:
    st.divider()
    for i, item in enumerate(st.session_state.my_items):
        cols = st.columns([4, 1])
        cols[0].write(f"{i+1}. {item['name']} - {item['price']:,}원")
        if cols[1].button("삭제", key=f"del_{i}"):
            st.session_state.my_items.pop(i)
            st.rerun()

st.divider()

# --- [3. 명세서 조립 및 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not st.session_state.my_items: st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 부모님이 알려주신 정밀 픽셀 (H_ROW2는 찌그러짐 방지를 위해 60으로 고정)
            H_TOP = 345        
            H_ROW1 = 62        # 첫 줄 (345~407)
            H_ROW2 = 60        # 둘째 줄 (407~467)
            
            # 푸터(합계 줄) 시작 위치: 원본에서 "합계"라고 써진 회색 줄을 가져옵니다.
            # 보통 부모님 양식에서 합계 줄은 표의 맨 마지막 줄입니다. 
            # 원본 template.png의 실제 끝에서 75픽셀 정도로 잡습니다.
            footer = orig.crop((0, H - 72, W, H)) 

            # 1. 조각 추출
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 345, W, 407))
            row_white = orig.crop((0, 407, W, 467))

            # 2. 이미지 조립 (흰색 틈새 방지)
            count = len(st.session_state.my_items)
            row_heights = [H_ROW1 if i % 2 == 0 else H_ROW2 for i in range(count)]
            new_h = H_TOP + sum(row_heights) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(header, (0, 0))
            curr_y = H_TOP
            for i in range(count):
                row_img = row_gray if i % 2 == 0 else row_white
                res.paste(row_img, (0, curr_y))
                curr_y += row_heights[i]
            res.paste(footer, (0, curr_y))

            # 3. 글자 채우기 (좌표 전면 재설정)
            draw = ImageDraw.Draw(res)
            f_mid = get_font(28)
            f_large = get_font(36)

            # [문제1 해결] 발행일자/거래처명 위치 수정 (오른쪽 박스 안으로)
            draw.text((150, 42), datetime.now().strftime("%Y-%m-%d"), font=f_mid, fill="black")
            draw.text((150, 98), f"{client} 귀하", font=f_mid, fill="black")

            # [문제2 해결] 상단 합계금액 오른쪽 정렬
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 630, 195, f"{total_sum:,}", f_large)

            # [문제4 해결] 내역 글씨 좌우 위치 정밀 조정
            curr_y = H_TOP
            for i, item in enumerate(st.session_state.my_items):
                ty = curr_y + (row_heights[i] // 2) - 15
                draw_center(draw, 0, 90, ty, f"{item['m']}/{item['d']}", f_mid) # 월일
                draw.text((110, ty), item['name'], font=f_mid, fill="black")    # 품목 (왼쪽정렬)
                draw_center(draw, 420, 520, ty, item['spec'], f_mid)           # 규격
                draw_center(draw, 520, 620, ty, str(item['qty']), f_mid)        # 수량
                draw_right(draw, 870, ty, f"{item['price']:,}", f_mid)         # 공급가액
                draw_right(draw, 1050, ty, "0", f_mid)                         # 세액
                curr_y += row_heights[i]

            # [문제3 해결] 제일 아래줄 합계 내역 기입
            foot_ty = curr_y + (footer.height // 2) - 15
            draw_right(draw, 870, foot_ty, f"{total_sum:,}", f_mid) # 공급가액 합계
            draw_right(draw, 1050, foot_ty, "0", f_mid)             # 세액 합계

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 수정된 명세서 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류: {e}")
