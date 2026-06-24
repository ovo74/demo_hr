import streamlit as st
import pandas as pd
import fitz  # PyMuPDF để xử lý PDF ảnh scan
import easyocr
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN CHUẨN WEB VIETCOMBANK ---
st.set_page_config(page_title="Vietcombank Tuyển dụng", layout="wide")

# Ép giao diện CSS theo các layout xanh dương thanh nhã của cổng thông tin VCB
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ép nền trắng toàn app */
    .stApp { background-color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* SỬA LỖI MÀU CHỮ: Ép tất cả nhãn chữ, text mô tả trong form thành MÀU ĐEN */
    label[data-testid="stWidgetLabel"] p, .stCaption p, p, span {
        color: #111111 !important;
    }
    
    /* Ép chữ bên trong các ô nhập liệu thành màu đen */
    .stTextInput input, .stSelectbox div, div[data-baseweb="select"] span {
        color: #111111 !important;
    }
    
    /* Thanh Header Vietcombank */
    .vcb-navbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 8%; border-bottom: 2px solid #E0E0E0; margin-bottom: 20px; }
    .vcb-menu { display: flex; gap: 30px; font-size: 15px; font-weight: 500; }
    .vcb-menu span { cursor: pointer; color: #333333 !important; }
    .vcb-menu .active { color: #006A4E !important; border-bottom: 3px solid #006A4E; padding-bottom: 5px; font-weight: bold; }
    
    /* Tiêu đề trang */
    .vcb-page-title { color: #333333 !important; font-size: 24px; font-weight: bold; margin-bottom: 15px; padding-left: 8%; }
    
    /* Khung form đăng nhập */
    .login-container { padding-left: 8%; max-width: 800px; color: #333333 !important; font-size: 14px;}
    .login-heading { font-size: 16px; font-weight: bold; margin-bottom: 5px; color: #111111 !important; }
    .login-sub { font-size: 13px; color: #555555 !important; margin-bottom: 20px; }
    
    /* Custom nút bấm phong cách VCB */
    .stButton>button { background-color: #29B6F6 !important; color: white !important; border: none !important; border-radius: 2px !important; padding: 8px 25px !important; font-size: 14px !important; font-weight: bold;}
    .stButton>button:hover { background-color: #0288D1 !important; }
    
    div[data-testid="stHorizontalBlock"] button { width: 100%; }
    
    /* Thanh màu xanh dương "Tài liệu của tôi" */
    .vcb-blue-bar { background-color: #29B6F6; color: white !important; padding: 10px 15px; font-size: 15px; font-weight: bold; border-radius: 2px; margin-top: 15px; margin-bottom: 10px; }
    .vcb-blue-bar p { color: white !important; margin: 0; }
    .vcb-upload-note { font-size: 13px; color: #333333 !important; margin-bottom: 15px; font-style: italic;}
    
    /* Hộp kết quả hồ sơ */
    .status-box { padding: 15px; border-radius: 4px; margin-top: 10px; font-weight: bold; font-size: 15px; }
    .status-approve { background-color: #E8F5E9; border-left: 6px solid #2E7D32; color: #1B5E20 !important; }
    .status-deny { background-color: #FFEBEE; border-left: 6px solid #C62828; color: #B71C1C !important; }
    
    /* XÓA VẠCH ĐEN Ở CÁC Ô CHỌN */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, div[data-baseweb="select"] {
        background-color: #F0F4FA !important;
        border: 1px solid #CFD8DC !important;
        border-left: 1px solid #CFD8DC !important;
    }
    div[data-baseweb="select"] > div {
        border-left: none !important;
    }

    /* THAY ĐỔI MÀU CÁC MỤC ĐÓNG/MỞ (EXPANDER) THÀNH XANH DƯƠNG */
    div[data-testid="stExpander"] summary {
        background-color: #29B6F6 !important;
        border-radius: 2px !important;
        border: none !important;
        padding: 10px 15px !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary label {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    div[data-testid="stExpander"] summary svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #29B6F6 !important;
        border-radius: 4px !important;
        background-color: #ffffff !important;
        margin-bottom: 10px;
    }

    /* ================= FIX MÀU Ô UPLOAD FILE SANG XANH DƯƠNG ĐỒNG BỘ ================= */
    div[data-testid="stFileUploader"] section {
        background-color: #29B6F6 !important;
        border: 2px dashed #0288D1 !important;
        border-radius: 4px !important;
        padding: 16px !important;
    }
    
    div[data-testid="stFileUploader"] section *,
    div[data-testid="stFileUploader"] section p,
    div[data-testid="stFileUploader"] section span,
    div[data-testid="stFileUploader"] section small {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
            
    /* ================= FIX Ô THÀNH TÍCH NỔI BẬT (TEXT AREA) ================= */
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #CFD8DC !important;
    }
                   
    </style>
""", unsafe_allow_html=True)

# --- KHỞI TẠO CACHE ENGINE OCR ---
@st.cache_resource
def load_ocr_engine():
    return easyocr.Reader(['vi', 'en'], gpu=False)

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return None

def get_recruitment_rules():
    try:
        return pd.read_excel("rules.xlsx")
    except Exception:
        return pd.DataFrame({
            "Truong_Dai_Hoc": ["Ngoại thương", "FTU", "Kinh tế Quốc dân", "NEU", "Học viện Ngân hàng"],
            "Chuyen_Nganh": ["Kinh tế đối ngoại", "Tài chính", "Ngân hàng", "Kế toán", "Tài chính Ngân hàng"]
        })

# --- HÀM QUÉT OCR VĂN BẰNG ---
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
    for idx, row in df_rules.iterrows():
        school = str(row['Truong_Dai_Hoc']).lower()
        major = str(row['Chuyen_Nganh']).lower()
        if school in text_lower and major in text_lower:
            matched_school = row['Truong_Dai_Hoc']
            matched_major = row['Chuyen_Nganh']
            break
            
    with st.expander("🔍 Nhật ký hệ thống - Dữ liệu chữ trích xuất:"):
        st.text(extracted_text if extracted_text.strip() else "[Không tìm thấy ký tự]")
        
    if matched_school and matched_major:
        return True, matched_school, matched_major
    return False, None, None

# MÔ PHỎNG EMAIL THÔNG BÁO KẾT QUẢ DƯỚI DẠNG DEMO
def get_demo_email_body(email_address, name):
    return f"""Kính gửi Ứng viên {name},

Hệ thống Tuyển dụng Trực tuyến Vietcombank thông báo đã tiếp nhận thành công hồ sơ đăng ký của bạn.
Hồ sơ thông tin cá nhân và tệp văn bằng của bạn đã vượt qua vòng đối chiếu tự động trên hệ thống.

Mã số hồ sơ ứng tuyển: VCB-2026-9482
Vị trí ứng tuyển: CV khách hàng (kinh nghiệm) - Chi nhánh Hà Nội.

Hội đồng tuyển dụng sẽ xem xét chi tiết và liên hệ lại với bạn qua số điện thoại đăng ký trong vòng 05 ngày làm việc.

Trân trọng,
Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)."""

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'ocr_status' not in st.session_state:
    st.session_state.ocr_status = None # None, "APPROVE", "DENY"
if 'ocr_school' not in st.session_state:
    st.session_state.ocr_school = ""
if 'ocr_major' not in st.session_state:
    st.session_state.ocr_major = ""

# --- DỰNG LOGO OFFLINE BASE64 HOẶC DỰ PHÒNG ONLINE ---
logo_base64 = get_base64_image("vcblogo.png")
logo_src = f"data:image/png;base64,{logo_base64}" if logo_base64 else "https://www.vietcombank.com.vn/images/logo.png"

# --- THANH HEADER VIETCOMBANK CHUNG ---
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


if not st.session_state.logged_in:
    # ---------------- MÀN HÌNH ĐĂNG NHẬP ----------------
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
        st.markdown("<p style='text-align: right; margin-top: 10px; font-size:14px;'><b>Địa chỉ Email:*</b></p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: right; margin-top: 25px; font-size:14px;'><b>Mật khẩu:*</b></p>", unsafe_allow_html=True)
    with col_r:
        email_input = st.text_input("email", label_visibility="collapsed", placeholder="thaiq742@gmail.com")
        pass_input = st.text_input("pass", label_visibility="collapsed", type="password")
        
        if st.button("Đăng nhập"):
            if "@" in email_input and pass_input:
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.rerun()
            else:
                st.error("Vui lòng điền đúng định dạng Email và Mật khẩu!")
else:
    # ---------------- MÀN HÌNH ĐIỀN HỒ SƠ VÀ UPLOAD VĂN BẰNG ----------------
    st.markdown(f"<div class='vcb-page-title'>[I.2026_Hà Nội] CV khách hàng (kinh nghiệm) (6593)</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: right; padding-right:8%; font-size:13px;'>Xin chào: <b>{st.session_state.user_email}</b> | <span style='color:red; cursor:pointer;'>Đăng xuất</span></p>", unsafe_allow_html=True)
    
    st.markdown("<div class='login-container' style='max-width:92%; margin-bottom:15px;'>Xin chào anh/chị, Cảm ơn anh/chị đã quan tâm đến công tác tuyển dụng tại Vietcombank. Vui lòng hoàn tất mẫu thông tin cá nhân dưới đây và đính kèm bằng đại học (ảnh/pdf) để thực hiện đối soát điều kiện tự động.</div>", unsafe_allow_html=True)
    
    # ================= KHỐI 1: TÀI LIỆU CỦA TÔI (UPLOAD FILE) =================
    st.markdown("<div class='vcb-blue-bar'>▼ Tài liệu của tôi</div>", unsafe_allow_html=True)
    st.markdown("<div class='vcb-upload-note'>Các loại tệp được chấp nhận: DOCX, PDF, Hình ảnh và Văn bản</div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Sơ yếu lý lịch / Bằng đại học (Dạng PDF ảnh scan để chạy thử OCR):*", type=["pdf"])
    
    if uploaded_file is not None:
        # ---- THÊM LOGIC CHẶN DUNG LƯỢNG 5MB TẠI ĐÂY ----
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Megabytes tính bằng Bytes
        
        if uploaded_file.size > MAX_FILE_SIZE:
            # Hiện dòng chữ cảnh báo màu đỏ chính xác theo yêu cầu
            st.markdown(
                '<p style="color: #ff4b4b; font-weight: bold; margin-top: 10px; font-size: 14px;">'
                'file vượt quá dung lượng hãy nộp file dung lượng trong ngưỡng 5mb.'
                '</p>', 
                unsafe_allow_html=True
            )
            # Khóa không cho upload: Reset toàn bộ trạng thái file và kết quả quét về rỗng
            st.session_state.ocr_status = None
            uploaded_file = None
        else:
            # Nếu dung lượng hợp lệ (< 5MB) mới tiến hành quét OCR dữ liệu
            file_bytes = uploaded_file.read()
            df_rules = get_recruitment_rules()
            
            with st.spinner("⏳ Hệ thống đang quét tự động thông tin bề mặt văn bằng bằng công cụ OCR..."):
                success, school, major = scan_scanned_pdf_ocr(file_bytes, df_rules)
                if success:
                    st.session_state.ocr_status = "APPROVE"
                    st.session_state.ocr_school = school
                    st.session_state.ocr_major = major
                else:
                    st.session_state.ocr_status = "DENY"
    
    # Hiển thị trạng thái quét hồ sơ ngay dưới phần upload file
    if st.session_state.ocr_status == "APPROVE":
        st.markdown(f"""
            <div class='status-box status-approve'>
                ✅ STATUS: APPROVE <br/>
                Hợp lệ: Đã tìm thấy văn bằng đạt tiêu chuẩn thuộc Trường: [{st.session_state.ocr_school}] - Chuyên ngành: [{st.session_state.ocr_major}].
            </div>
        """, unsafe_allow_html=True)
    elif st.session_state.ocr_status == "DENY":
        st.markdown("""
            <div class='status-box status-deny'>
                ❌ STATUS: DENY <br/>
                Cảnh báo: Tệp tin tải lên không chứa thông tin Trường hoặc Chuyên ngành nằm trong danh sách xét tuyển ưu tiên của Ngân hàng.
            </div>
        """, unsafe_allow_html=True)

    # ================= KHỐI 2: THÔNG TIN HỒ SƠ (FORM 3 CỘT ĐỂ TRỐNG) =================
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Mở mặc định form Thông tin Hồ sơ giống hệt ảnh chụp
    with st.expander("▼ Thông tin Hồ sơ", expanded=True):
        st.caption("Vui lòng điền thông tin cá nhân của bạn. Các trường dấu (*) là bắt buộc.")
        
        # Hàng 1
        c1, c2, c3 = st.columns(3)
        with c1: name_ten = st.text_input("Tên:*", value="")
        with c2: name_ho = st.text_input("Họ và tên đệm:*", value="")
        with c3: gender = st.selectbox("Giới tính:*", ["", "Nam", "Nữ", "Khác"])
        
        # Hàng 2
        c1, c2, c3 = st.columns(3)
        with c1: dob = st.text_input("Ngày sinh (DD/MM/YYYY):*", value="", placeholder="Ví dụ: 07/04/2002")
        with c2: pob = st.text_input("Nơi sinh:*", value="")
        with c3: address = st.text_input("Địa chỉ hiện tại:*", value="")
        
        # Hàng 3
        c1, c2, c3 = st.columns(3)
        with c1: district = st.text_input("Quận/Huyện:*", value="")
        with c2: city = st.selectbox("Tỉnh / Thành phố:*", ["", "Hà Nội", "TP. Hồ Chí Minh", "Thái Bình", "Đà Nẵng", "Khác"])
        with c3: country = st.selectbox("Quốc gia:*", ["", "Việt Nam", "Nước ngoài"])
        
        # Hàng 4
        c1, c2, c3 = st.columns(3)
        with c1: zip_code = st.text_input("Mã bưu điện:", value="")
        with c2: phone = st.text_input("Số điện thoại:*", value="")
        with c3: alt_phone = st.text_input("Số điện thoại khác:", value="")
        
        # Hàng 5
        c1, c2, c3 = st.columns(3)
        with c1: username = st.text_input("Tài khoản/Username (Email):*", value=st.session_state.user_email)
        with c2: cccd = st.text_input("CMND/CCCD/Hộ chiếu:*", value="")
        with c3: cccd_date = st.text_input("Ngày cấp (DD/MM/YYYY):*", value="")
        
        # Hàng 6
        c1, c2, c3 = st.columns(3)
        with c1: height = st.text_input("Chiều cao (cm):", value="")
        with c2: weight = st.text_input("Cân nặng (kg):", value="")
        with c3: marriage = st.selectbox("Tình trạng hôn nhân:*", ["", "Độc thân", "Đã kết hôn", "Khác"])
        
        # Hàng 7 - Text Area
        achievements = st.text_area("Các thành tích nổi bật", value="", help="Kích cỡ câu trả lời phải là 1024 ký tự hoặc ít hơn.")

    # Các cấu trúc thư mục rỗng phía dưới mô phỏng theo thiết kế gốc của VCB
    with st.expander("▶ Kinh nghiệm làm việc"): st.write("Không có dữ liệu lịch sử")
    with st.expander("▶ Trình độ chuyên môn"): st.write("Hệ thống đồng bộ tự động từ mục Bằng Cấp")
    with st.expander("▶ Học vấn THPT"): st.text_input("Trường THPT:", value="")
    with st.expander("▶ Trình độ ngoại ngữ"): st.selectbox("Chứng chỉ Tiếng Anh:", ["", "IELTS", "TOEIC", "TOEFL"])
    with st.expander("▶ Kỹ năng tin học"): st.checkbox("MOS / IC3 / Bằng Tin học văn phòng ứng dụng")
    with st.expander("▶ Nghiên cứu khoa học"): st.write("Không có tài liệu đính kèm")
    with st.expander("▶ Thông tin gia đình"): st.write("Khai báo thông tin người thân (nếu có)")
    with st.expander("▶ Thông tin Cụ thể về Công việc"): st.write("Nguyện vọng địa bàn làm việc: Khu vực Hà Nội")

    # ================= KHỐI 3: THANH ĐIỀU HƯỚNG NÚT BẤM (XỬ LÝ LOGIC) =================
    st.markdown("<br/>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3, b_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with b_col1:
        st.button("Xem Hồ sơ")
    with b_col2:
        if st.button("Lưu"):
            st.toast("💾 Đã lưu tạm các thông tin biểu mẫu vào phiên làm việc!", icon="ℹ️")
            
    with b_col4:
        # XỬ LÝ LOGIC KIỂM TRA ĐIỀU KIỆN KHI ẤN NỘP ĐƠN
        if st.button("Nộp đơn"):
            required_fields = [name_ten, name_ho, gender, dob, pob, address, district, city, country, phone, username, cccd, cccd_date, marriage]
            is_form_filled = all(str(f).strip() != "" for f in required_fields)
            
            if st.session_state.ocr_status is None:
                st.error("❌ Bạn chưa đính kèm tài liệu Văn bằng/CV ở phần 'Tài liệu của tôi' hoặc file tải lên chưa đúng quy chuẩn!")
            elif st.session_state.ocr_status == "DENY":
                st.error("❌ Không thể nộp đơn: Văn bằng đính kèm của bạn không đáp ứng điều kiện lọc hồ sơ tự động của ngân hàng (STATUS: DENY).")
            elif not is_form_filled:
                st.error("❌ Không thể nộp đơn: Bạn bỏ sót một hoặc nhiều trường dữ liệu bắt buộc có dấu (*) trong phần 'Thông tin Hồ sơ'. Hãy điền đầy đủ để test tính năng.")
            else:
                st.balloons()
                st.success(f"🎉 Chúc mừng ứng viên {name_ho} {name_ten}! Hồ sơ ứng tuyển trực tuyến của bạn đã được gửi đi thành công.")
                
                demo_email_body = get_demo_email_body(username, f"{name_ho} {name_ten}")
                st.markdown(f"""
                    <div style='background-color: #E3F2FD; padding: 20px; border-radius: 4px; border-left: 6px solid #1E88E5; color: #0D47A1; margin-top: 15px;'>
                        <strong>📧 [DEMO HỆ THỐNG] MÔ PHỎNG THƯ GỬI VỀ EMAIL CỦA ỨNG VIÊN ({username}):</strong> <br/><br/>
                        <pre style='background-color: #ffffff; padding: 15px; color: #333; border: 1px dashed #1E88E5; font-family:Consolas, monospace;'>{demo_email_body}</pre>
                    </div>
                """, unsafe_allow_html=True)

    if st.sidebar.button("Đăng xuất (Reset Test)"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.ocr_status = None
        st.session_state.ocr_school = ""
        st.session_state.ocr_major = ""
        st.rerun()