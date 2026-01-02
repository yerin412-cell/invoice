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

st.set_page_config(page_title="간편 명세서 (버튼 우측형)", layout="centered")

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

# --- [1. 상단 공통 정보] ---
st.header("🧾 명세서 작성")
client = st.text_input("🏢 거래처명", key="client_name")

# --- [2. 신규 품목 추가 칸] ---
if st.session_state.edit_index is None:
    with st.expander("➕ 새 품목 추가하기", expanded=True):
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            m_in = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)], index=int(datetime.now().strftime("%m"))-1, key="new_m")
        with d_col2:
            d_in = st.selectbox("일", [f"{i:02d}" for i in range(1, 32)], index=int(datetime.now().strftime("%d"))-1, key="new_d")
        
        name_in = st.text_input("📦 품목명", key="new_name")
        spec_in = st.text_input("📏 규격 (예: 25)", key="new_spec")
        qty_in = st.selectbox("🔢 수량", [0.5, 1.0], key="new_qty")
        price_man_in = st.number_input("💰 금액 (단위: 만원)", min_value=0, value=0, step=1, key="new_price")
        
        if st.button("➕ 리스트에 추가", use_container_width=True, type="primary"):
            if name_in:
                st.session_state.my_items.append({
                    "m": m_in, "d": d_in, "name": name_in, 
                    "spec": f"{spec_in}(t)", "qty": qty_in, "price": price_man_in * 10000
                })
                st.session_state.my_items.sort(key=lambda x: (x['m'], x['d']))
                st.rerun()

st.divider()

# --- [3. 내역 확인 (날짜/내역은 왼쪽, 버튼은 오른쪽)] ---
if st.session_state.my_items:
    st.subheader("📝 내역 확인 및 수정")
    for i, item in enumerate(st.session_state.my_items):
        
        # --- 수정 모드 ---
        if st.session_state.edit_index == i:
            with st.container(border=True):
                st.info(f"📍 {i+1}번 항목 수정")
                ed_c1, ed_c2 = st.columns(2)
                m_list = [f"{j:02d}" for j in range(1, 13)]
                d_list = [f"{j:02d}" for j in range(1, 32)]
                new_m = ed_c1.selectbox("월", m_list, index=m_list.index(item['m']), key=f"ed_m_{i}")
                new_d = ed_col2 = ed_c2.selectbox("일", d_list, index=d_list.index(item['d']), key=f"ed_d_{i}")
                
                new_name = st.text_input("품목명", value=item['name'], key=f"ed_na_{i}")
                new_spec = st.text_input("규격", value=item['spec'].replace("(t)", ""), key=f"ed_sp_{i}")
                new_qty = st.selectbox("수량", [0.5, 1.0], index=[0.5, 1.0].index(item['qty']), key=f"ed_qt_{i}")
                new_price = st.number_input("금액(만)", value=int(item['price']//10000), key=f"ed_pr_{i}")
                
                btn_c1, btn_c2 = st.columns(2)
                if btn_c1.button("✅ 완료", key=f"save_{i}", use_container_width=True):
                    st.session_state.my_items[i] = {
                        "m": new_m, "d": new_d, "name": new_name, 
                        "spec": f"{new_spec}(t)", "qty": new_qty, "price": new_price * 10000
                    }
                    st.session_state.my_items.sort(key=lambda x: (x['m'], x['d']))
                    st.session_state.edit_index = None
                    st.rerun()
                if btn_c2.button("❌ 취소", key=f"cancel_{i}", use_container_width=True):
                    st.session_state.edit_index = None
                    st.rerun()
        
        # --- 일반 표시 모드 (버튼 우측 배치) ---
        else:
            # 큰 칸을 나눠서 왼쪽엔 글씨, 오른쪽엔 버튼
            main_col, btn_col = st.columns([3, 1.2]) 
            
            with main_col:
                st.markdown(f"**📅 {item['m']}/{item['d']}** | {item['name']}")
                st.caption(f"{item['spec']} | {item['qty']}t | {item['price']:,}원")
            
            with btn_col:
                # 버튼을 위아래가 아닌 양옆으로 작게 배치
                b1, b2 = st.columns(2)
                if b1.button("✏️", key=f"ed_btn_{i}", help="수정"):
                    st.session_state.edit_index = i
                    st.rerun()
                if b2.button("🗑️", key=f"del_btn_{i}", help="삭제"):
                    st.session_state.my_items.pop(i)
                    st.rerun()
            st.divider()

# --- [4. 명세서 이미지 생성] ---
if st.button("🚀 명세서 이미지 만들기", use_container_width=True, type="primary"):
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

            draw_right(draw, 620, 67, datetime.now().strftime("%Y-%m-%d"), f_mid)
            draw_right(draw, 620, 122, f"{client}", f_mid)
            total_sum = sum(item['price'] for item in st.session_state.my_items)
            draw_right(draw, 1070, 201, f"{total_sum:,}", f_big)

            for i, item in enumerate(st.session_state.my_items):
                ty = H_TOP + (i * H_ROW) + 12
                draw.text((20, ty), f"{item['m']}/{item['d']}", font=f_mid, fill="black")
                draw.text((348, ty), item['name'], font=f_mid, fill="black")
                draw_right(draw, 850, ty, item['spec'], f_mid)          
                draw_right(draw, 1060, ty, f"{item['qty']}", f_mid)     
                draw_right(draw, 1510, ty, f"{item['price']:,}", f_mid) 
                draw_right(draw, 1700, ty, "0", f_mid)                  

            foot_ty = H_TOP + (count * H_ROW) + 18
            draw_right(draw, 1510, foot_ty, f"{total_sum:,}", f_mid)
            draw_right(draw, 1700, foot_ty, "0", f_mid)

            st.image(res)
            buf = io.BytesIO()
            res.save(buf, format="PNG")
            st.download_button("📥 최종 명세서 저장", buf.getvalue(), f"명세서_{client}.png", use_container_width=True)
        except Exception as e:
            st.error(f"이미지 생성 중 오류: {e}")
