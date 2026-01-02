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

# 오른쪽 정렬 함수
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
st.header("1. 명세서 작성 (v2.5)")
client = st.text_input("🏢 거래처명", key="client_v25")

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

            # [수정 3] 줄 자를 때 픽셀 2개씩 줄여서 겹침 방지 (62->60, 60->58)
            H_TOP = 345        
            H_ROW1 = 60        # 회색 줄 (345~405)
            H_ROW2 = 58        # 흰색 줄 (405~463)
            
            # 1. 조각 추출
            header = orig.crop((0, 0, W, H_TOP))
            row_gray = orig.crop((0, 345, W, 405))
            row_white = orig.crop((0, 405, W, 463))
            footer = orig.crop((0, H - 72, W, H)) 

            # 2. 이미지 조립
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

            # 3. 글자 채우기 (요청하신 좌표 대이동 적용)
            draw = ImageDraw.Draw(res)
            f_mid = get_font(28)
            f_large = get_font(42) # [수정 2] 합계금액 폰트 키움

            # [수정 1] 발행일자/거래처명 (10px 아래로, 500px 오른쪽으로, '귀하' 삭제)
            draw.text((150 + 500, 42 + 10), datetime.now().strftime("%Y-%m-%d"), font=f_mid, fill="black")
            draw.text((150 + 500, 98 + 10), f"{client}", font=f_mid, fill="black")

            # [수정 2] 상단 합계금액 (500px 오른쪽으로)
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 630 + 500, 195, f"{total_sum:,}", f_large)

            # [수정 4~7] 내역 글씨 위치 조정
            curr_y = H_TOP
            for i, item in enumerate(st.session_state.my_items):
                ty = curr_y + (row_heights[i] // 2) - 15
                draw_center(draw, 0, 90, ty, f"{item['m']}/{item['d']}", f_mid) # 월일
                draw.text((110 + 300, ty), item['name'], font=f_mid, fill="black") # [수정 4] 품목 +300
                draw_center(draw, 420 + 500, 520 + 500, ty, item['spec'], f_mid)  # [수정 5] 규격 +500
                draw_center(draw, 520 + 500, 620 + 500, ty, str(item['qty']), f_mid) # [수정 6] 수량 +500
                draw_right(draw, 870 + 260, ty, f"{item['price']:,}", f_mid) # [수정 7] 공급가액 (W=1150에 맞춤)
                draw_right(draw, 1050 + 80, ty, "0", f_mid) # 세액
                curr_y += row_heights[i]

            # [수정 8] 제일 아래줄 합계 (800px 이동 효과 적용)
            foot_ty = curr_y + (footer.height // 2) - 15
            draw_right(draw, 870 + 260, foot_ty, f"{total_sum:,}", f_mid) 
            draw_right(draw, 1050 + 80, foot_ty, "0", f_mid)

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 최종 수정본 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류: {e}")
