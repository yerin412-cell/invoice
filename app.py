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

# 우측 정렬 함수 (금액 및 우측 정렬용)
def draw_right(draw, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    draw.text((x_end - w, y), str(text), font=font, fill=fill)

# 중앙 정렬 함수 (월일, 규격, 수량용)
def draw_center(draw, x_start, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    center = x_start + (x_end - x_start) / 2
    draw.text((center - w / 2, y), str(text), font=font, fill=fill)

# --- [1. 정보 입력] ---
st.header("1. 명세서 작성 (v2.7)")
client = st.text_input("🏢 거래처명")

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

# --- [3. 명세서 생성] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not st.session_state.my_items: st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # [수정] 줄 자르기: 선(테두리)을 포함하지 않도록 안쪽 픽셀만 정밀하게 컷팅
            H_TOP = 345        
            # 회색줄: 346~405 / 흰색줄: 408~467 (경계선 피하기)
            row_gray = orig.crop((0, 346, W, 405)) 
            row_white = orig.crop((0, 408, W, 467))
            footer = orig.crop((0, H - 72, W, H)) 

            # 이미지 조립
            count = len(st.session_state.my_items)
            H_ROW = 58 # 실제 출력될 높이
            new_h = H_TOP + (H_ROW * count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))

            res.paste(orig.crop((0, 0, W, H_TOP)), (0, 0))
            for i in range(count):
                row_img = row_gray if i % 2 == 0 else row_white
                res.paste(row_img, (0, H_TOP + (i * H_ROW)))
            res.paste(footer, (0, H_TOP + (count * H_ROW)))

            # 3. 글자 채우기 (이미지 분석 기반 정밀 좌표)
            draw = ImageDraw.Draw(res)
            f_mid = get_font(28)
            f_total_box = get_font(48)

            # [문제1 해결] 발행일자, 거래처명 우측 정렬 (박스 끝 385px)
            draw_right(draw, 385, 52, datetime.now().strftime("%Y-%m-%d"), f_mid)
            draw_right(draw, 385, 108, f"{client}", f_mid)

            # [문제2 해결] 상단 합계금액 우측 정렬 (박스 끝 635px)
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 635, 202, f"{total_sum:,}", f_total_box)

            # [문제3 해결] 내역 그리드 정렬 (각 칸의 중앙 또는 우측 끝)
            # 칸 구분: 월일(0-95), 품목(95-385), 규격(385-505), 수량(505-645), 공급가액(645-935), 세액(935-1150)
            for i, item in enumerate(st.session_state.my_items):
                ty = H_TOP + (i * H_ROW) + 12
                
                draw_center(draw, 0, 95, ty, f"{item['m']}/{item['d']}", f_mid)   # 월일 (중앙)
                draw.text((105, ty), item['name'], font=f_mid, fill="black")     # 품목 (왼쪽+여백)
                draw_center(draw, 385, 505, ty, item['spec'], f_mid)            # 규격 (중앙)
                draw_center(draw, 505, 645, ty, str(item['qty']), f_mid)         # 수량 (중앙)
                draw_right(draw, 925, ty, f"{item['price']:,}", f_mid)          # 공급가액 (우측)
                draw_right(draw, 1135, ty, "0", f_mid)                          # 세액 (우측)

            # [문제4 해결] 하단 합계 정렬 (공급가액/세액 칸과 일치)
            foot_ty = H_TOP + (count * H_ROW) + 18
            draw_right(draw, 925, foot_ty, f"{total_sum:,}", f_mid)
            draw_right(draw, 1135, foot_ty, "0", f_mid)

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 정밀 교정본 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류: {e}")
