import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [0. 저장소 초기화] ---
if 'my_items' not in st.session_state:
    st.session_state.my_items = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.set_page_config(page_title="간편 명세서 (모바일형)", layout="centered")

@st.cache_resource
def get_font(size=25):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

def draw_right(draw, x_end, y, text, font, fill="black"):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    draw.text((x_end - w, y), str(text), font=font, fill=fill)

# --- [1. 정보 입력창 (모바일 세로 배치)] ---
st.header("🧾 명세서 작성 및 수정")
client = st.text_input("🏢 거래처명", key="client_name")

with st.container():
    # 월/일 같은 줄 배치
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        m_list = [f"{i:02d}" for i in range(1, 13)]
        m_str = st.selectbox("월 선택", m_list, index=int(datetime.now().strftime("%m"))-1)
    with d_col2:
        d_list = [f"{i:02d}" for i in range(1, 32)]
        d_str = st.selectbox("일 선택", d_list, index=int(datetime.now().strftime("%d"))-1)
    
    # 품목명/규격/수량/금액 세로 배치 (모바일 편의성)
    name = st.text_input("📦 품목명")
    spec = st.text_input("📏 규격 (예: 25)")
    qty = st.selectbox("🔢 수량", [0.5, 1.0])
    price_man = st.number_input("💰 금액 (단위: 만원 / 1=만원)", min_value=0, value=0, step=1)

# 추가 및 수정 버튼 로직
if st.session_state.edit_index is None:
    if st.button("➕ 이 내용으로 추가하기", use_container_width=True, type="primary"):
        if name:
            st.session_state.my_items.append({
                "m": m_str, "d": d_str, "name": name, 
                "spec": f"{spec}(t)", "qty": qty, "price": price_man * 10000
            })
            st.session_state.my_items.sort(key=lambda x: (x['m'], x['d']))
            st.rerun()
else:
    st.info("💡 현재 선택한 항목을 수정 중입니다.")
    col_edit1, col_edit2 = st.columns(2)
    # variant="primary" 오류 해결을 위해 속성 제거
    if col_edit1.button("✅ 수정 완료", use_container_width=True):
        st.session_state.my_items[st.session_state.edit_index] = {
            "m": m_str, "d": d_str, "name": name, 
            "spec": f"{spec}(t)", "qty": qty, "price": price_man * 10000
        }
        st.session_state.my_items.sort(key=lambda x: (x['m'], x['d']))
        st.session_state.edit_index = None
        st.rerun()
    if col_edit2.button("❌ 수정 취소", use_container_width=True):
        st.session_state.edit_index = None
        st.rerun()

# --- [2. 내역 리스트 (수정/삭제)] ---
if st.session_state.my_items:
    st.subheader("📝 내역 확인")
    for i, item in enumerate(st.session_state.my_items):
        with st.expander(f"[{item['m']}/{item['d']}] {item['name']} - {item['price']:,}원", expanded=True):
            st.write(f"규격: {item['spec']} / 수량: {item['qty']}")
            ex_c1, ex_c2 = st.columns(2)
            if ex_c1.button("✏️ 수정", key=f"edit_btn_{i}", use_container_width=True):
                st.session_state.edit_index = i
                st.rerun()
            if ex_c2.button("🗑️ 삭제", key=f"del_btn_{i}", use_container_width=True):
                st.session_state.my_items.pop(i)
                st.rerun()

st.divider()

# --- [3. 명세서 생성] ---
if st.button("🚀 명세서 이미지 만들기", use_container_width=True):
    if not st.session_state.my_items:
        st.warning("내역을 추가해주세요.")
    else:
        try:
            orig = Image.open("template.png").convert("RGB")
            W, H = orig.size
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

            # [조정] 발행일자, 거래처명 (더 오른쪽으로: 600px)
            draw_right(draw, 600, 67, datetime.now().strftime("%Y-%m-%d"), f_mid)
            draw_right(draw, 600, 122, f"{client}", f_mid)

            # [조정] 상단 합계 (1080px)
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 1080, 201, f"{total_sum:,}", f_big)

            # 내역 기록
            for i, item in enumerate(st.session_state.my_items):
                ty = H_TOP + (i * H_ROW) + 12
                # 월/일 (고정 위치)
                draw.text((20, ty), f"{item['m']}/{item['d']}", font=f_mid, fill="black")
                # 품목 (고정 위치)
                draw.text((348, ty), item['name'], font=f_mid, fill="black")
                
                # [조정] 규격, 수량, 공급가액, 세액 모두 오른쪽 정렬
                draw_right(draw, 880, ty, item['spec'], f_mid)          # 규격(t 포함됨)
                draw_right(draw, 1080, ty, f"{item['qty']}", f_mid)     # 수량 (t 제외)
                draw_right(draw, 1480, ty, f"{item['price']:,}", f_mid) # 공급가액 (더 우측)
                draw_right(draw, 1680, ty, "0", f_mid)                  # 세액 (더 우측)

            # [조정] 하단 합계 위치
            foot_ty = H_TOP + (count * H_ROW) + 18
            draw_right(draw, 1480, foot_ty, f"{total_sum:,}", f_mid)
            draw_right(draw, 1680, foot_ty, "0", f_mid)

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 최종 명세서 저장", buf.getvalue(), f"명세서_{client}.png", use_container_width=True)
        except Exception as e:
            st.error(f"이미지 생성 중 오류가 발생했습니다: {e}")
