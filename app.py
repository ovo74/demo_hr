import streamlit as st
import pandas as pd
import fitz  # PyMuPDF để xử lý PDF ảnh scan
import easyocr
import smtplib
import base64
import io
from PIL import Image
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from database import init_db, lay_hoac_tao_ung_vien, luu_ho_so, kiem_tra_email_da_nop, EmailDaTonTaiError

# Khởi tạo database ngay khi app chạy (tạo bảng nếu chưa có)
init_db()

# ─────────────────────────────────────────────────────────────────────
# CẤU HÌNH GIAO DIỆN CHUẨN WEB VIETCOMBANK
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Vietcombank Tuyển dụng", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp { background-color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; }

    label[data-testid="stWidgetLabel"] p, .stCaption p, p, span {
        color: #111111 !important;
    }
    .stTextInput input, .stSelectbox div, div[data-baseweb="select"] span {
        color: #111111 !important;
    }

    .vcb-navbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 8%; border-bottom: 2px solid #E0E0E0; margin-bottom: 20px; }
    .vcb-menu { display: flex; gap: 30px; font-size: 15px; font-weight: 500; }
    .vcb-menu span { cursor: pointer; color: #333333 !important; }
    .vcb-menu .active { color: #006A4E !important; border-bottom: 3px solid #006A4E; padding-bottom: 5px; font-weight: bold; }

    .vcb-page-title { color: #333333 !important; font-size: 24px; font-weight: bold; margin-bottom: 15px; padding-left: 8%; }

    .login-container { padding-left: 8%; max-width: 800px; color: #333333 !important; font-size: 14px;}
    .login-heading { font-size: 16px; font-weight: bold; margin-bottom: 5px; color: #111111 !important; }
    .login-sub { font-size: 13px; color: #555555 !important; margin-bottom: 20px; }

    .stButton>button { background-color: #29B6F6 !important; color: white !important; border: none !important; border-radius: 2px !important; padding: 8px 25px !important; font-size: 14px !important; font-weight: bold;}
    .stButton>button:hover { background-color: #0288D1 !important; }
    div[data-testid="stHorizontalBlock"] button { width: 100%; }

    .vcb-blue-bar { background-color: #29B6F6; color: white !important; padding: 10px 15px; font-size: 15px; font-weight: bold; border-radius: 2px; margin-top: 15px; margin-bottom: 10px; }
    .vcb-blue-bar p { color: white !important; margin: 0; }
    .vcb-upload-note { font-size: 13px; color: #333333 !important; margin-bottom: 15px; font-style: italic;}

    .status-box { padding: 15px; border-radius: 4px; margin-top: 10px; font-weight: bold; font-size: 15px; }
    .status-approve { background-color: #E8F5E9; border-left: 6px solid #2E7D32; color: #1B5E20 !important; }
    .status-deny { background-color: #FFEBEE; border-left: 6px solid #C62828; color: #B71C1C !important; }

    .stTextInput>div>div>input, .stSelectbox>div>div>div, div[data-baseweb="select"] {
        background-color: #F0F4FA !important;
        border: 1px solid #CFD8DC !important;
        border-left: 1px solid #CFD8DC !important;
    }
    div[data-baseweb="select"] > div { border-left: none !important; }

    div[data-testid="stExpander"] summary {
        background-color: #29B6F6 !important;
        border-radius: 2px !important;
        border: none !important;
        padding: 10px 15px !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary label { color: #ffffff !important; font-weight: bold !important; }
    div[data-testid="stExpander"] summary svg { color: #ffffff !important; fill: #ffffff !important; }
    div[data-testid="stExpander"] {
        border: 1px solid #29B6F6 !important;
        border-radius: 4px !important;
        background-color: #ffffff !important;
        margin-bottom: 10px;
    }

    div[data-testid="stFileUploader"] section {
        background-color: #29B6F6 !important;
        border: 2px dashed #0288D1 !important;
        border-radius: 4px !important;
        padding: 16px !important;
    }
    div[data-testid="stFileUploader"] section *,
    div[data-testid="stFileUploader"] section p,
    div[data-testid="stFileUploader"] section span,
    div[data-testid="stFileUploader"] section small { color: #ffffff !important; fill: #ffffff !important; }

    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #CFD8DC !important;
    }
    .remove-btn-container { display: flex; justify-content: flex-end; margin-top: 10px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# CACHE ENGINE OCR
# ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_ocr_engine():
    return easyocr.Reader(['vi', 'en'], gpu=False)


# ─────────────────────────────────────────────────────────────────────
# XỬ LÝ LOGO
# ─────────────────────────────────────────────────────────────────────
def get_base64_image(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")
        new_data = []
        for item in img.getdata():
            r, g, b, a = item
            if abs(r - g) < 15 and abs(g - b) < 15 and r > 180:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────
# QUY TẮC TUYỂN DỤNG
# ─────────────────────────────────────────────────────────────────────
def get_recruitment_rules():
    try:
        return pd.read_excel("rules.xlsx")
    except Exception:
        return pd.DataFrame({
            "Truong_Dai_Hoc": ["Ngoại thương", "FTU", "Kinh tế Quốc dân", "NEU", "Học viện Ngân hàng"],
            "Chuyen_Nganh":   ["Kinh tế đối ngoại", "Tài chính", "Ngân hàng", "Kế toán", "Tài chính Ngân hàng"]
        })


# ─────────────────────────────────────────────────────────────────────
# QUÉT OCR VĂN BẰNG
# ─────────────────────────────────────────────────────────────────────
def scan_scanned_pdf_ocr(file_bytes, df_rules):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    extracted_text = ""
    reader = load_ocr_engine()

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        results = reader.readtext(img_bytes, detail=0)
        extracted_text += " ".join(results) + "\n"

    text_lower = extracted_text.lower()
    matched_school, matched_major = None, None
    for _, row in df_rules.iterrows():
        school = str(row['Truong_Dai_Hoc']).lower()
        major  = str(row['Chuyen_Nganh']).lower()
        if school in text_lower and major in text_lower:
            matched_school = row['Truong_Dai_Hoc']
            matched_major  = row['Chuyen_Nganh']
            break

    with st.expander("🔍 Nhật ký hệ thống - Dữ liệu chữ trích xuất:"):
        st.text(extracted_text if extracted_text.strip() else "[Không tìm thấy ký tự]")

    if matched_school and matched_major:
        return True, matched_school, matched_major
    return False, None, None


# ─────────────────────────────────────────────────────────────────────
# MÔ PHỎNG EMAIL
# ─────────────────────────────────────────────────────────────────────
def get_demo_email_body(email_address, name):
    return f"""Kính gửi Ứng viên {name},

Hệ thống Tuyển dụng Trực tuyến Vietcombank thông báo đã tiếp nhận thành công hồ sơ đăng ký của bạn.
Hồ sơ thông tin cá nhân và tệp văn bằng của bạn đã vượt qua vòng đối chiếu tự động trên hệ thống.

Mã số hồ sơ ứng tuyển: VCB-2026-9482
Vị trí ứng tuyển: CV khách hàng (kinh nghiệm) - Chi nhánh Hà Nội.

Hội đồng tuyển dụng sẽ xem xét chi tiết và liên hệ lại với bạn qua số điện thoại đăng ký trong vòng 05 ngày làm việc.

Trân trọng,
Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)."""


# ─────────────────────────────────────────────────────────────────────
# QUẢN LÝ TRẠNG THÁI (SESSION STATE)
# ─────────────────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'ung_vien_id' not in st.session_state:
    st.session_state.ung_vien_id = None
if 'ocr_status' not in st.session_state:
    st.session_state.ocr_status = None
if 'ocr_school' not in st.session_state:
    st.session_state.ocr_school = ""
if 'ocr_major' not in st.session_state:
    st.session_state.ocr_major = ""
if 'cm_items' not in st.session_state:
    st.session_state.cm_items = [0]
if 'cm_counter' not in st.session_state:
    st.session_state.cm_counter = 1
if 'nn_items' not in st.session_state:
    st.session_state.nn_items = [0]
if 'nn_counter' not in st.session_state:
    st.session_state.nn_counter = 1


# ─────────────────────────────────────────────────────────────────────
# HEADER VIETCOMBANK
# ─────────────────────────────────────────────────────────────────────
logo_base64 = get_base64_image("vcblogo.png")
logo_src = f"data:image/png;base64,{logo_base64}" if logo_base64 else "https://www.vietcombank.com.vn/images/logo.png"

st.markdown(f"""
    <div class='vcb-navbar'>
        <img src='{logo_src}' width='160'>
        <div class='vcb-menu'>
            <span>Trang chủ</span>
            <span>Giới thiệu</span>
            <span class='active'>Cơ hội nghề nghiệp ▾</span>
        </div>
    </div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════
# MÀN HÌNH ĐĂNG NHẬP
# ═════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("<div class='vcb-page-title'>Cơ hội nghề nghiệp: Đăng nhập</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='login-container'>
            <div class='login-heading'>Bạn đã có tài khoản?</div>
            <div class='login-sub'>Nhập địa chỉ email và mật khẩu (Thông tin đăng nhập có phân biệt chữ hoa/chữ thường).</div>
            <p style='color:red; font-size:12px;'>*chỉ một trường bắt buộc.</p>
        </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1.5, 3])
    with col_l:
        st.markdown("<p style='text-align:right;margin-top:10px;font-size:14px;'><b>Địa chỉ Email:*</b></p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:right;margin-top:25px;font-size:14px;'><b>Mật khẩu:*</b></p>", unsafe_allow_html=True)
    with col_r:
        email_input = st.text_input("email", label_visibility="collapsed", placeholder="thaiq742@gmail.com")
        pass_input  = st.text_input("pass",  label_visibility="collapsed", type="password")

        if st.button("Đăng nhập"):
            if "@" in email_input and pass_input:
                # Lấy hoặc tạo ứng viên trong DB
                ung_vien_id = lay_hoac_tao_ung_vien(email_input, pass_input)
                st.session_state.logged_in    = True
                st.session_state.user_email   = email_input
                st.session_state.ung_vien_id  = ung_vien_id
                st.rerun()
            else:
                st.error("Vui lòng điền đúng định dạng Email và Mật khẩu!")


# ═════════════════════════════════════════════════════════════════════
# MÀN HÌNH ĐIỀN HỒ SƠ
# ═════════════════════════════════════════════════════════════════════
else:
    st.markdown("<div class='vcb-page-title'>[I.2026_Sở Giao dịch] CV khách hàng (kinh nghiệm) (6593)</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:right;padding-right:8%;font-size:13px;'>Xin chào: <b>{st.session_state.user_email}</b> | <span style='color:red;cursor:pointer;'>Đăng xuất</span></p>", unsafe_allow_html=True)
    st.markdown("<div class='login-container' style='max-width:92%;margin-bottom:15px;'>Xin chào anh/chị, Cảm ơn anh/chị đã quan tâm đến công tác tuyển dụng tại Vietcombank. Vui lòng hoàn tất mẫu thông tin cá nhân dưới đây và đính kèm bằng đại học (ảnh/pdf) để thực hiện đối soát điều kiện tự động.</div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    # KHỐI 1: TÀI LIỆU CỦA TÔI
    # ─────────────────────────────────────────────────────────────────
    st.markdown("<div class='vcb-blue-bar'>▼ Tài liệu của tôi</div>", unsafe_allow_html=True)
    st.markdown("<div class='vcb-upload-note'>Các loại tệp được chấp nhận: DOCX, PDF, Hình ảnh và Văn bản</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Sơ yếu lý lịch / Bằng đại học (Dạng PDF ảnh scan):",
        type=["pdf"]
    )

    if uploaded_file is not None:
        MAX_FILE_SIZE = 5 * 1024 * 1024
        if uploaded_file.size > MAX_FILE_SIZE:
            st.markdown(
                '<p style="color:#ff4b4b;font-weight:bold;margin-top:10px;font-size:14px;">'
                'File vượt quá dung lượng. Hãy nộp file trong ngưỡng 5MB.</p>',
                unsafe_allow_html=True
            )
            st.session_state.ocr_status = None
        else:
            file_bytes = uploaded_file.read()
            df_rules   = get_recruitment_rules()
            with st.spinner("⏳ Hệ thống đang quét tự động thông tin bề mặt văn bằng bằng công cụ OCR..."):
                success, school, major = scan_scanned_pdf_ocr(file_bytes, df_rules)
                if success:
                    st.session_state.ocr_status = "APPROVE"
                    st.session_state.ocr_school = school
                    st.session_state.ocr_major  = major
                else:
                    st.session_state.ocr_status = "DENY"

    if st.session_state.ocr_status is not None:
        st.markdown("""
            <div style='background:#E3F2FD;border-left:4px solid #29B6F6;padding:10px 15px;
                        border-radius:4px;margin-top:8px;font-size:13px;color:#0D47A1;'>
                ✅ Hệ thống đã tiếp nhận và xử lý tệp đính kèm thành công.
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    # KHỐI 2: THÔNG TIN HỒ SƠ
    # ─────────────────────────────────────────────────────────────────
    with st.expander("▼ Thông tin Hồ sơ", expanded=True):
        st.caption("Vui lòng điền thông tin cá nhân của bạn. Các trường dấu (*) là bắt buộc.")

        c1, c2, c3 = st.columns(3)
        with c1: name_ten = st.text_input("Tên:*", value="")
        with c2: name_ho  = st.text_input("Họ và tên đệm:*", value="")
        with c3: gender   = st.selectbox("Giới tính:*", ["Lựa chọn", "Nam", "Nữ", "Khác"])

        c1, c2, c3 = st.columns(3)
        with c1: dob     = st.text_input("Ngày sinh (DD/MM/YYYY):*", value="", placeholder="Ví dụ: 07/04/2002")
        with c2: pob     = st.text_input("Nơi sinh:*", value="")
        with c3: address = st.text_input("Địa chỉ hiện tại:*", value="")

        c1, c2, c3 = st.columns(3)
        with c1: district = st.text_input("Quận/Huyện:*", value="")
        with c2: city     = st.selectbox("Tỉnh / Thành phố:*", ["Lựa chọn", "Hà Nội", "TP. Hồ Chí Minh", "Thái Bình", "Đà Nẵng", "Khác"])
        with c3: country  = st.selectbox("Quốc gia:*", ["Lựa chọn", "Việt Nam", "Nước ngoài"])

        c1, c2, c3 = st.columns(3)
        with c1: zip_code  = st.text_input("Mã bưu điện:", value="")
        with c2: phone     = st.text_input("Số điện thoại:*", value="")
        with c3: alt_phone = st.text_input("Số điện thoại khác:", value="")

        c1, c2, c3 = st.columns(3)
        with c1: username  = st.text_input("Tài khoản/Username (Email):*", value=st.session_state.user_email)
        with c2: cccd      = st.text_input("CMND/CCCD/Hộ chiếu:*", value="")
        with c3: cccd_date = st.text_input("Ngày cấp (DD/MM/YYYY):*", value="")

        c1, c2, c3 = st.columns(3)
        with c1: height   = st.text_input("Chiều cao (cm):", value="")
        with c2: weight   = st.text_input("Cân nặng (kg):", value="")
        with c3: marriage = st.selectbox("Tình trạng hôn nhân:*", ["Lựa chọn", "Độc thân", "Đã kết hôn", "Khác"])

        achievements = st.text_area("Các thành tích nổi bật", value="", help="Kích cỡ câu trả lời phải là 1024 ký tự hoặc ít hơn.")

    with st.expander("▶ Kinh nghiệm làm việc"):
        st.write("Không có dữ liệu lịch sử")

    # ─────────────────────────────────────────────────────────────────
    # KHỐI TRÌNH ĐỘ CHUYÊN MÔN
    # ─────────────────────────────────────────────────────────────────
    with st.expander("▼ Trình độ chuyên môn", expanded=True):
        for i, idx in enumerate(st.session_state.cm_items):
            if i > 0:
                st.markdown("<hr style='border:1px dashed #29B6F6;'/>", unsafe_allow_html=True)

            cm_c1, cm_c2, cm_c3 = st.columns(3)
            with cm_c1: st.text_input("Ngày bắt đầu:*",  placeholder="DD/MM/YYYY", key=f"cm_start_{idx}")
            with cm_c2: st.text_input("Ngày kết thúc:*", placeholder="DD/MM/YYYY", key=f"cm_end_{idx}")
            with cm_c3: st.selectbox("Trình độ:*", ["Lựa chọn", "Đại học", "Cao đẳng", "Thạc sĩ", "Tiến sĩ"], key=f"cm_level_{idx}")

            cm_c1, cm_c2, cm_c3 = st.columns(3)
            with cm_c1:
                st.selectbox("Văn bằng:*", ["Lựa chọn", "Cử nhân", "Kỹ sư", "Khác"], key=f"cm_degree_{idx}")
            with cm_c2:
                selected_group = st.selectbox(
                    "Nhóm chuyên ngành:*",
                    ["Lựa chọn", "Khối ngành Kinh tế - Quản lý", "Khối ngành CNTT", "Khối ngành Luật", "Khối ngành Kỹ thuật", "Khác"],
                    key=f"cm_group_{idx}"
                )
            with cm_c3:
                if selected_group == "Khác":
                    st.text_input("Chuyên ngành:*", placeholder="Vui lòng nhập chuyên ngành cụ thể...", key=f"cm_major_text_{idx}")
                else:
                    if selected_group == "Khối ngành Kinh tế - Quản lý":
                        major_options = ["Lựa chọn", "Tài chính Ngân hàng", "Kế toán", "Quản trị Kinh doanh"]
                    elif selected_group == "Khối ngành CNTT":
                        major_options = ["Lựa chọn", "Trí tuệ nhân tạo", "Khoa học máy tính", "Kỹ thuật máy tính"]
                    elif selected_group == "Khối ngành Luật":
                        major_options = ["Lựa chọn", "Luật kinh tế", "Luật dân sự", "Luật quốc tế"]
                    elif selected_group == "Khối ngành Kỹ thuật":
                        major_options = ["Lựa chọn", "Kỹ thuật điện", "Kỹ thuật cơ khí", "Kỹ thuật xây dựng"]
                    else:
                        major_options = ["Lựa chọn"]
                    st.selectbox("Chuyên ngành:*", major_options, key=f"cm_major_select_{idx}")

            cm_c1, cm_c2, cm_c3 = st.columns(3)
            with cm_c1: st.selectbox("Quốc gia", ["Lựa chọn", "Việt Nam", "Nước ngoài"], key=f"cm_country_{idx}")
            with cm_c2:
                st.selectbox(
                    "Loại trường:*",
                    ["Lựa chọn", "Trường Công lập đào tạo trong nước", "Trường Dân lập đào tạo trong nước",
                     "Trường nước ngoài", "Trường liên kết với trường nước ngoài đào tạo trong nước"],
                    key=f"cm_school_type_{idx}"
                )
            with cm_c3: st.text_input("Tên trường:*", key=f"cm_school_name_{idx}")

            cm_c1, cm_c2, cm_c3 = st.columns(3)
            with cm_c1: st.text_input("Thời gian khóa học:*", key=f"cm_duration_{idx}")
            with cm_c2: st.selectbox("Đơn vị thời gian khóa học:*", ["Lựa chọn", "Năm", "Tháng"], key=f"cm_unit_{idx}")
            with cm_c3:
                st.markdown("<label style='color:#111111 !important;font-weight:bold;'>Điểm tổng kết:*</label>", unsafe_allow_html=True)
                sub_gpa_c1, sub_gpa_c2 = st.columns([1, 2])
                with sub_gpa_c1:
                    st.selectbox("Thang điểm", ["/10", "/4"], key=f"cm_gpa_scale_{idx}", label_visibility="collapsed")
                with sub_gpa_c2:
                    st.text_input("Điểm số", placeholder="Nhập điểm...", key=f"cm_gpa_{idx}", label_visibility="collapsed")

            cm_c1, cm_c2, cm_c3 = st.columns(3)
            with cm_c1: st.selectbox("Loại hình đào tạo:*", ["Lựa chọn", "Chính quy", "Tại chức", "Liên thông"], key=f"cm_train_type_{idx}")
            with cm_c2: st.selectbox("Xếp loại:*", ["Lựa chọn", "Xuất sắc", "Giỏi", "Khá", "Trung bình", "Yếu"], key=f"cm_rank_{idx}")
            with cm_c3: st.selectbox("Học hàm", ["Lựa chọn", "Không có", "Phó giáo sư", "Giáo sư"], key=f"cm_title_{idx}")

            col_space, col_btn = st.columns([5, 1])
            with col_btn:
                if st.button("🗑 Loại bỏ", key=f"cm_remove_{idx}"):
                    if len(st.session_state.cm_items) > 1:
                        st.session_state.cm_items.remove(idx)
                        st.rerun()
                    else:
                        st.warning("Hệ thống yêu cầu giữ lại ít nhất 1 mục Trình độ chuyên môn!")

        if st.button("⊕ Thêm", key="cm_add_new"):
            st.session_state.cm_items.append(st.session_state.cm_counter)
            st.session_state.cm_counter += 1
            st.rerun()

    with st.expander("▶ Học vấn THPT"):
        st.text_input("Trường THPT:", value="")

    # ─────────────────────────────────────────────────────────────────
    # KHỐI TRÌNH ĐỘ NGOẠI NGỮ
    # ─────────────────────────────────────────────────────────────────
    with st.expander("▼ Trình độ ngoại ngữ", expanded=True):
        for j, idx in enumerate(st.session_state.nn_items):
            if j > 0:
                st.markdown("<hr style='border:1px dashed #29B6F6;'/>", unsafe_allow_html=True)

            nn_c1, nn_c2, nn_c3 = st.columns(3)
            with nn_c1: st.selectbox("Ngôn ngữ:*",        ["Lựa chọn", "Tiếng Anh", "Tiếng Trung", "Tiếng Nhật", "Tiếng Hàn"], key=f"nn_lang_{idx}")
            with nn_c2: st.selectbox("Chứng chỉ ngoại ngữ:*", ["Lựa chọn", "IELTS", "TOEIC", "TOEFL", "Hsk", "JLPT"],           key=f"nn_cert_{idx}")
            with nn_c3: st.text_input("Điểm ngoại ngữ", key=f"nn_score_{idx}")

            col_space_nn, col_btn_nn = st.columns([5, 1])
            with col_btn_nn:
                if st.button("🗑 Loại bỏ", key=f"nn_remove_{idx}"):
                    if len(st.session_state.nn_items) > 1:
                        st.session_state.nn_items.remove(idx)
                        st.rerun()
                    else:
                        st.warning("Hệ thống yêu cầu giữ lại ít nhất 1 mục Trình độ ngoại ngữ!")

        if st.button("⊕ Thêm", key="nn_add_new"):
            st.session_state.nn_items.append(st.session_state.nn_counter)
            st.session_state.nn_counter += 1
            st.rerun()

    with st.expander("▶ Kỹ năng tin học"):
        st.checkbox("MOS / IC3 / Bằng Tin học văn phòng ứng dụng")
    with st.expander("▶ Nghiên cứu khoa học"):
        st.write("Không có tài liệu đính kèm")
    with st.expander("▶ Thông tin gia đình"):
        st.write("Khai báo thông tin người thân (nếu có)")

    # ─────────────────────────────────────────────────────────────────
    # KHỐI 3: NÚT BẤM ĐIỀU HƯỚNG
    # ─────────────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3, b_col4 = st.columns([1.5, 1.5, 1.5, 1.5])

    with b_col1:
        st.button("Xem Hồ sơ")

    with b_col2:
        if st.button("Lưu"):
            st.toast("💾 Đã lưu tạm các thông tin biểu mẫu vào phiên làm việc!", icon="ℹ️")

    with b_col4:
        if st.button("Nộp đơn"):
            required_fields = [
                name_ten, name_ho, gender, dob, pob,
                address, district, city, country, phone,
                username, cccd, cccd_date, marriage
            ]
            is_form_filled = all(
                str(f).strip() not in ("", "Lựa chọn") for f in required_fields
            )

            if not is_form_filled:
                st.error("❌ Không thể nộp đơn: Bạn bỏ sót một hoặc nhiều trường bắt buộc (*). Hãy điền đầy đủ.")
            elif kiem_tra_email_da_nop(username):
                st.error(
                    f"❌ Email **{username}** đã được sử dụng để nộp hồ sơ trước đó. "
                    "Mỗi địa chỉ email chỉ được đăng ký cho một ứng viên duy nhất. "
                    "Vui lòng kiểm tra lại hoặc liên hệ bộ phận tuyển dụng nếu cần hỗ trợ."
                )
            else:
                # ── Thu thập thông tin hồ sơ chính ──
                thong_tin = {
                    "ten":                  name_ten,
                    "ho_ten_dem":           name_ho,
                    "gioi_tinh":            gender,
                    "ngay_sinh":            dob,
                    "noi_sinh":             pob,
                    "dia_chi":              address,
                    "quan_huyen":           district,
                    "tinh_thanh_pho":       city,
                    "quoc_gia":             country,
                    "ma_buu_dien":          zip_code,
                    "so_dien_thoai":        phone,
                    "so_dien_thoai_khac":   alt_phone,
                    "cccd":                 cccd,
                    "ngay_cap_cccd":        cccd_date,
                    "chieu_cao":            height,
                    "can_nang":             weight,
                    "tinh_trang_hon_nhan":  marriage,
                    "thanh_tich_noi_bat":   achievements,
                    "ocr_status":           st.session_state.ocr_status,
                    "ocr_truong":           st.session_state.ocr_school,
                    "ocr_chuyen_nganh":     st.session_state.ocr_major,
                }

                # ── Thu thập trình độ chuyên môn (nhiều mục) ──
                ds_chuyen_mon = []
                for idx in st.session_state.cm_items:
                    nhom = st.session_state.get(f"cm_group_{idx}", "Lựa chọn")
                    if nhom == "Khác":
                        chuyen_nganh = st.session_state.get(f"cm_major_text_{idx}", "")
                    else:
                        chuyen_nganh = st.session_state.get(f"cm_major_select_{idx}", "")

                    ds_chuyen_mon.append({
                        "ngay_bat_dau":       st.session_state.get(f"cm_start_{idx}", ""),
                        "ngay_ket_thuc":      st.session_state.get(f"cm_end_{idx}", ""),
                        "trinh_do":           st.session_state.get(f"cm_level_{idx}", ""),
                        "van_bang":           st.session_state.get(f"cm_degree_{idx}", ""),
                        "nhom_chuyen_nganh":  nhom,
                        "chuyen_nganh":       chuyen_nganh,
                        "quoc_gia":           st.session_state.get(f"cm_country_{idx}", ""),
                        "loai_truong":        st.session_state.get(f"cm_school_type_{idx}", ""),
                        "ten_truong":         st.session_state.get(f"cm_school_name_{idx}", ""),
                        "thoi_gian_khoa_hoc": st.session_state.get(f"cm_duration_{idx}", ""),
                        "don_vi_thoi_gian":   st.session_state.get(f"cm_unit_{idx}", ""),
                        "thang_diem":         st.session_state.get(f"cm_gpa_scale_{idx}", ""),
                        "diem_tong_ket":      st.session_state.get(f"cm_gpa_{idx}", ""),
                        "loai_hinh_dao_tao":  st.session_state.get(f"cm_train_type_{idx}", ""),
                        "xep_loai":           st.session_state.get(f"cm_rank_{idx}", ""),
                        "hoc_ham":            st.session_state.get(f"cm_title_{idx}", ""),
                    })

                # ── Thu thập trình độ ngoại ngữ ──
                ds_ngoai_ngu = []
                for idx in st.session_state.nn_items:
                    ds_ngoai_ngu.append({
                        "ngon_ngu":  st.session_state.get(f"nn_lang_{idx}", ""),
                        "chung_chi": st.session_state.get(f"nn_cert_{idx}", ""),
                        "diem":      st.session_state.get(f"nn_score_{idx}", ""),
                    })

                # ── Ghi vào database ──
                try:
                    # Luôn đảm bảo ung_vien tồn tại trong DB hiện tại
                    # (phòng Streamlit Cloud reset filesystem hoặc session mất)
                    email_luu = st.session_state.user_email or username
                    st.session_state.ung_vien_id = lay_hoac_tao_ung_vien(email_luu)

                    ho_so_id = luu_ho_so(
                        ung_vien_id   = st.session_state.ung_vien_id,
                        thong_tin     = thong_tin,
                        ds_chuyen_mon = ds_chuyen_mon,
                        ds_ngoai_ngu  = ds_ngoai_ngu,
                    )

                    st.balloons()
                    st.success(
                        f"🎉 Chúc mừng ứng viên {name_ho} {name_ten}! "
                        f"Hồ sơ đã được ghi nhận thành công (Mã hồ sơ: #{ho_so_id})."
                    )

                    demo_email_body = get_demo_email_body(username, f"{name_ho} {name_ten}")
                    st.markdown(f"""
                        <div style='background-color:#E3F2FD;padding:20px;border-radius:4px;
                                    border-left:6px solid #1E88E5;color:#0D47A1;margin-top:15px;'>
                            <strong>📧 [DEMO HỆ THỐNG] MÔ PHỎNG THƯ GỬI VỀ EMAIL CỦA ỨNG VIÊN ({username}):</strong><br/><br/>
                            <pre style='background-color:#ffffff;padding:15px;color:#333;
                                        border:1px dashed #1E88E5;font-family:Consolas,monospace;'>{demo_email_body}</pre>
                        </div>
                    """, unsafe_allow_html=True)

                except EmailDaTonTaiError as e:
                    st.error(
                        f"❌ **Email đã được sử dụng!** {e} "
                        "Vui lòng kiểm tra lại hoặc liên hệ bộ phận tuyển dụng nếu cần hỗ trợ."
                    )
                except Exception as e:
                    st.error(f"❌ Lỗi khi lưu hồ sơ vào database: {e}")

    # Nút Đăng xuất sidebar
    if st.sidebar.button("Đăng xuất (Reset Test)"):
        for key in ["logged_in", "user_email", "ung_vien_id",
                    "ocr_status", "ocr_school", "ocr_major",
                    "cm_items", "nn_items", "cm_counter", "nn_counter"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()