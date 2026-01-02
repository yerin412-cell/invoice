import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import urllib.request

# --- [초기 설정] ---
if 'my_items' not in st.session_state:
    st.session_state.my_items = []

st.set_page_config(page_title="명세서 위치 교정기", layout="wide")

@st.cache_resource
def get_font(size=25):
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        font_data = urllib.request.urlopen(font_url).read()
        return ImageFont.truetype(io.BytesIO(font_data), size)
    except:
        return ImageFont.load_default()

# --- [사이드바: 미세 조정 제어판] ---
st.sidebar.header("🎯 위치 미세 조정")
st.sidebar.info("글자가 칸에 안 맞으면 아래 숫자를 조절하세요.")

# 1. 상단 정보 위치
st.sidebar.subheader("📍 상단 (날짜/거래처)")
off_top_x = st.sidebar.slider("가로 위치 (오른쪽으로)", 0, 1000, 600)
off_top_y = st.sidebar.slider("세로 위치 (아래로)", 0, 200, 50)

# 2. 합계 금액 위치
st.sidebar.subheader("💰 상단 합계 금액")
off_total_x = st.sidebar.slider("합계 가로", 0, 1100, 1050)
off_total_y = st.sidebar.slider("합계 세로", 0, 300, 210)

# 3. 내역 칸 가로 위치 (품목별)
st.sidebar.subheader("📝 내역 칸별 가로 위치")
col_name = st.sidebar.slider("품목 위치", 0, 1000, 400)
col_spec = st.sidebar.slider("규격 위치", 0, 1000, 650)
col_qty = st.sidebar.slider("수량 위치", 0, 1000, 750)
col_price = st.sidebar.slider("공급가액 위치", 0, 1150, 1030)
col_tax = st.sidebar.slider("세액 위치", 0, 1150, 1130)

# --- [메인 화면: 입력창] ---
st.header("거래명세서 작성 v3.0")
client = st.text_input("🏢 거래처명 (입력 후 Enter)")

col1, col2, col3, col4, col5 = st.columns([1,2,1,1,2])
with col1: m = st.text_input("월", "01")
with col2: name = st.text_input("품목")
with col3: spec = st.text_input("규격")
with col4: qty = st.number_input("수량", 1.0)
with col5: price = st.number_input("금액", 0)

if st.button("➕ 추가"):
    st.session_state.my_items.append({"m":m, "d":datetime.now().strftime("%d"), "name":name, "spec":spec, "qty":qty, "price":price})
    st.rerun()

# --- [이미지 생성 로직] ---
if st.session_state.my_items:
    try:
        orig = Image.open("template.png").convert("RGB")
        W, H = orig.size
        
        # 줄 자르기 (정밀)
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
        f_big = get_font(45)

        # [상단 정보] 슬라이더 값 적용
        draw.text((off_top_x, off_top_y), datetime.now().strftime("%Y-%m-%d"), font=f_mid, fill="black")
        draw.text((off_top_x, off_top_y + 55), client, font=f_mid, fill="black")

        # [상단 합계] 슬라이더 값 적용 (우측 정렬)
        total_val = sum(item['price'] for item in st.session_state.my_items)
        txt = f"{total_val:,}"
        tw = f_big.getbbox(txt)[2] - f_big.getbbox(txt)[0]
        draw.text((off_total_x - tw, off_total_y), txt, font=f_big, fill="black")

        # [내역] 슬라이더 값 적용
        for i, item in enumerate(st.session_state.my_items):
            ty = H_TOP + (i * H_ROW) + 12
            draw.text((20, ty), f"{item['m']}/{item['d']}", font=f_mid, fill="black")
            draw.text((col_name, ty), item['name'], font=f_mid, fill="black")
            draw.text((col_spec, ty), item['spec'], font=f_mid, fill="black")
            draw.text((col_qty, ty), str(item['qty']), font=f_mid, fill="black")
            
            p_txt = f"{item['price']:,}"
            pw = f_mid.getbbox(p_txt)[2] - f_mid.getbbox(p_txt)[0]
            draw.text((col_price - pw, ty), p_txt, font=f_mid, fill="black")
            draw.text((col_tax - 20, ty), "0", font=f_mid, fill="black")

        # [하단 합계]
        fty = H_TOP + (count * H_ROW) + 18
        draw.text((col_price - pw, fty), f"{total_val:,}", font=f_mid, fill="black")
        draw.text((col_tax - 20, fty), "0", font=f_mid, fill="black")

        st.image(res, caption="미리보기 (조절바를 움직여보세요)")
        
        buf = io.BytesIO()
        res.save(buf, format="PNG")
        st.download_button("📥 완성된 이미지 저장", buf.getvalue(), "명세서.png")

    except Exception as e:
        st.error(f"파일을 찾을 수 없습니다. template.png가 같은 폴더에 있는지 확인해주세요.")
