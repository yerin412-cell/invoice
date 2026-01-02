import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화] ---
if 'my_items' not in st.session_state:
    st.session_state.my_items = []

st.set_page_config(page_title="간편 거래명세서 최종본", layout="centered")

@st.cache_resource
def get_font(size=25):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# 우측 정렬 함수 (부모님이 지정한 X좌표가 글자의 '끝' 지점이 되도록 설정)
def draw_right(draw, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    draw.text((x_end - w, y), str(text), font=font, fill=fill)

# --- [1. 정보 입력창] ---
st.header("🧾 거래명세서 작성 (최종)")
client = st.text_input("🏢 거래처명", key="client_final")

with st.container():
    col_date, col_item, col_spec, col_qty, col_price = st.columns([1, 2, 1, 1, 2])
    with col_date: m = st.text_input("월", value=datetime.now().strftime("%m"))
    with col_item: name = st.text_input("품목명")
    with col_spec: spec = st.text_input("규격")
    with col_qty: qty = st.number_input("수량", value=1.0, step=0.5)
    with col_price: price = st.number_input("금액", value=0, step=1000)

if st.button("➕ 품목 추가하기 (아래 리스트 확인)", use_container_width=True):
    if name:
        st.session_state.my_items.append({
            "m": m, "d": datetime.now().strftime("%d"), 
            "name": name, "spec": spec, "qty": qty, "price": price
        })
        st.rerun()

# --- [2. 내역 리스트 및 수정(삭제) 기능] ---
if st.session_state.my_items:
    st.subheader("📝 추가된 내역 (실수하면 삭제하세요)")
    for i, item in enumerate(st.session_state.my_items):
        cols = st.columns([4, 1])
        cols[0].write(f"{i+1}. {item['name']} ({item['spec']}) - {item['price']:,}원")
        if cols[1].button("삭제", key=f"del_{i}"):
            st.session_state.my_items.pop(i)
            st.rerun()
    
    if st.button("🗑️ 전체 삭제", type="secondary"):
        st.session_state.my_items = []
        st.rerun()

st.divider()

# --- [3. 명세서 생성 (부모님 지정 수치 적용)] ---
if st.button("🚀 명세서 이미지 만들기", type="primary", use_container_width=True):
    if not st.session_state.my_items:
        st.warning("내역을 먼저 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size

            # 줄 자르기 및 조립
            H_TOP = 345
            row_gray = orig.crop((0, 346, W, 404))
            row_white = orig.crop((0, 406, W, 464))
            footer = orig.crop((0, H - 72, W, H))

            count = len(st.session_state.my_items)
            H_ROW = 58
            new_h = H_TOP + (H_ROW * count) + footer.height
            res = Image.new("RGB", (W, new_h), (255, 255, 255))
            res.paste(orig.crop((0, 0, W, H_TOP)), (0, 0))
            for i in range(count):
                res.paste(row_gray if i % 2 == 0 else row_white, (0, H_TOP + (i * H_ROW)))
            res.paste(footer, (0, H_TOP + (count * H_ROW)))

            draw = ImageDraw.Draw(res)
            f_mid = get_font(28)
            f_big = get_font(48)

            # [교정 1] 상단 날짜/거래처 - 부모님 수치(466, 67) 기반 우측 정렬
            draw_right(draw, 466, 67, datetime.now().strftime("%Y-%m-%d"), f_mid)
            draw_right(draw, 466, 67 + 55, f"{client}", f_mid)

            # [교정 2] 상단 합계금액 - 부모님 수치(1050, 201)
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 1050, 201, f"{total_sum:,}", f_big)

            # [교정 3] 내역 칸 - 부모님 수치 적용 및 우측 끝 보정
            for i, item in enumerate(st.session_state.my_items):
                ty = H_TOP + (i * H_ROW) + 12
                draw.text((20, ty), f"{item['m']}/{item['d']}", font=f_mid, fill="black") # 월일
                draw.text((348, ty), item['name'], font=f_mid, fill="black")            # 품목
                draw.text((800, ty), item['spec'], font=f_mid, fill="black")            # 규격
                draw.text((1050, ty), str(item['qty']), font=f_mid, fill="black")       # 수량
                # 공급가액/세액은 수량보다 더 오른쪽으로 (기존 수치 기반 보정)
                draw_right(draw, 1380, ty, f"{item['price']:,}", f_mid)                 # 공급가액
                draw_right(draw, 1580, ty, "0", f_mid)                                  # 세액

            # [교정 4] 하단 합계
            foot_ty = H_TOP + (count * H_ROW) + 18
            draw_right(draw, 1380, foot_ty, f"{total_sum:,}", f_mid)
            draw_right(draw, 1580, foot_ty, "0", f_mid)

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 최종 명세서 저장", buf.getvalue(), f"명세서_{client}.png")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
