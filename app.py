import streamlit as st
import pandas as pd
import fitz  # PyMuPDF để xử lý PDF ảnh scan
import easyocr
import cv2
import numpy as np
import re
import unicodedata
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

    /* Nút "Upload": LUÔN hiện rõ (nền trắng, chữ/icon màu đậm), không phụ
       thuộc hover, để nổi bật trên nền xanh của vùng kéo-thả phía trên.
       Dùng nhiều selector dự phòng vì tên data-testid của nút có thể
       khác nhau giữa các bản Streamlit. */
    div[data-testid="stFileUploader"] section button,
    div[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploader"] section [data-testid*="BaseButton"],
    div[data-testid="stFileUploader"] section [data-testid$="-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #CFD8DC !important;
        border-radius: 4px !important;
        opacity: 1 !important;
    }
    div[data-testid="stFileUploader"] section button *,
    div[data-testid="stFileUploaderDropzone"] button *,
    div[data-testid="stFileUploader"] section [data-testid*="BaseButton"] *,
    div[data-testid="stFileUploader"] section [data-testid$="-secondary"] * {
        color: #29B6F6 !important;
        fill: #29B6F6 !important;
    }

    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #CFD8DC !important;
    }
    .remove-btn-container { display: flex; justify-content: flex-end; margin-top: 10px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# QUY TẮC TUYỂN DỤNG (bảng gợi ý trường/ngành — chỉ dùng để hỗ trợ khớp lựa chọn
# trên form, KHÔNG dùng để tự động approve/deny hồ sơ)
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
# TIỆN ÍCH SO KHỚP MỜ (OCR tiếng Việt thường mất dấu / lệch khoảng trắng)
# ─────────────────────────────────────────────────────────────────────
def _khong_dau(s: str) -> str:
    """Bỏ dấu + hạ chữ thường + coi dấu gạch ngang/gạch chéo như khoảng trắng
    (VD: "TÀI CHÍNH-NGÂN HÀNG" -> "tai chinh ngan hang", khớp được với từ điển
    "Tài chính Ngân hàng" dù văn bằng viết liền dấu gạch ngang, không cách)."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[\-–—/]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


# ─────────────────────────────────────────────────────────────────────
# TIỀN XỬ LÝ ẢNH TRƯỚC KHI OCR — tăng độ chính xác cho văn bằng scan
# (độ phân giải cao hơn + khử nhiễu + tăng tương phản nhị phân hoá thích ứng)
# ─────────────────────────────────────────────────────────────────────
def _preprocess_page_for_ocr(pix):
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    elif pix.n == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img[:, :, 0] if img.ndim == 3 else img
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    gray = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    return gray


# ─────────────────────────────────────────────────────────────────────
# CACHE ENGINE OCR
# ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_ocr_engine():
    return easyocr.Reader(['vi', 'en'], gpu=False)


# ─────────────────────────────────────────────────────────────────────
# QUÉT OCR VĂN BẰNG — trả về (raw_text, extracted_fields_dict)
# ─────────────────────────────────────────────────────────────────────
def run_ocr_on_pdf(file_bytes):
    """Quét toàn bộ PDF (mỗi trang scale 3x + tiền xử lý ảnh) và ghép text."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    reader = load_ocr_engine()
    extracted_text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Scale 3x thay vì 2x để giữ được chi tiết chữ nhỏ trên văn bằng scan
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        processed = _preprocess_page_for_ocr(pix)
        results = reader.readtext(processed, detail=0, paragraph=False)
        extracted_text += " ".join(results) + "\n"

    return extracted_text


# ─────────────────────────────────────────────────────────────────────
# TRÍCH XUẤT TRƯỜNG THÔNG TIN TỪ VĂN BẰNG (v2)
#
# Bài học rút ra khi test với văn bằng scan thật: OCR tiếng Việt có dấu rất
# hay bị garble (mất dấu, lẫn ký tự, nuốt mất nhãn "Ngành:"/"Trường:"...).
# Vì vậy chiến lược 2 lớp được áp dụng:
#   1) Regex theo nhãn (label-based) cho các trường có định dạng khá ổn định
#      (ngày sinh, xếp loại, loại hình, văn bằng, họ tên có tiền tố Bà/Ông).
#   2) So khớp theo TỪ ĐIỂN (dictionary match) cho Trường/Chuyên ngành — vì
#      nhãn "Trường:"/"Ngành:" trên văn bằng thật RẤT hay bị OCR nuốt mất,
#      nhưng tên trường/tên ngành thực tế (dù viết hoa/thường lẫn lộn) vẫn
#      còn nằm đâu đó trong văn bản → so khớp mờ (bỏ dấu) với danh sách
#      trường/ngành phổ biến đáng tin cậy hơn nhiều so với bắt theo nhãn.
# Toàn bộ kết quả CHỈ dùng để gợi ý điền sẵn — ứng viên luôn xem lại & sửa.
# ─────────────────────────────────────────────────────────────────────
_NGAY_SINH_PATTERNS = [
    # "Ngày, tháng, năm sinh: dd/mm/yyyy" — kể cả khi OCR đọc nhầm "năm" -> "hăm"/"nam"
    r"(?:ngày,?\s*tháng,?\s*)?(?:năm|nam|hăm)\s*sinh\s*[:\-]?\s*(\d{1,2})\s*[\/\.\-]\s*(\d{1,2})\s*[\/\.\-]\s*(\d{4})",
    r"(?:sinh\s*ngày|ngày\s*sinh)\s*[:\-]?\s*(\d{1,2})\s*[\/\.\-]\s*(\d{1,2})\s*[\/\.\-]\s*(\d{4})",
    r"sinh\s*ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})",
]

_HOTEN_PATTERNS = [
    r"họ\s*(?:và|,)?\s*tên(?:\s*(?:là|sinh\s*viên|học\s*viên))?\s*[:\-]?\s*"
    r"([^\n\d,;]{3,60}?)(?=\s+sinh\s*ngày|\s+ngày\s*sinh|\s+nam\s*sinh|[\n,;]|$)",
    # Nhiều bản sao y/chứng thực văn bằng VN ghi "Bà/Ông <Họ tên>" — khá đáng tin cậy
    r"(?:Bà|Ông)[ \t]+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:[ \t]+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4})",
]

# ── Văn bằng / Xếp loại / Loại hình đào tạo: so khớp trên bản KHÔNG DẤU ──
# Lý do đổi từ regex-có-dấu sang so khớp không dấu: chữ tiêu đề/in hoa trên
# văn bằng (VD "BẰNG CỬ NHÂN") rất hay bị OCR đọc ra thành "BANG CU NHAN"
# (mất dấu hoàn toàn) — regex yêu cầu ký tự có dấu sẽ luôn trượt trong
# trường hợp này. So khớp không dấu + ánh xạ về nhãn tiếng Việt chuẩn
# (canonical) vừa chịu lỗi OCR tốt hơn, vừa đảm bảo giá trị điền vào form
# luôn đúng chính tả có dấu (không phụ thuộc OCR đọc đúng dấu hay không).
_VAN_BANG_CANON = [("thac si", "Thạc sĩ"), ("tien si", "Tiến sĩ"), ("ky su", "Kỹ sư"), ("cu nhan", "Cử nhân")]
_LOAI_HINH_CANON = [
    ("vua hoc vua lam", "Vừa học vừa làm"), ("lien thong", "Liên thông"),
    ("tai chuc", "Tại chức"), ("tu xa", "Từ xa"), ("chinh quy", "Chính quy"),
]
# Nhãn "xếp loại"/"hạng tốt nghiệp" thường bị OCR nuốt dấu ("Xep loai", "Hang tot nghiep")
# nên cũng so khớp trên bản không dấu; giá trị Giỏi/Khá... nếu OCR đọc sai 1-2 ký tự
# (VD "Gidi" thay vì "Giỏi") sẽ không khớp được — đây là giới hạn còn lại, ứng viên
# vẫn cần xem lại field này.
_XEP_LOAI_LABEL_KD = r"(?:xep\s*loai(?:\s*tot\s*nghiep)?|hang\s*tot\s*nghiep)\s*[:\-]?\s*"
_XEP_LOAI_CANON = [
    ("xuat sac", "Xuất sắc"), ("trung binh kha", "Trung bình khá"),
    ("trung binh", "Trung bình"), ("gioi", "Giỏi"), ("kha", "Khá"), ("yeu", "Yếu"),
]


def _match_canon(text_kd: str, canon_list, window: str = None):
    """So khớp danh sách (từ_khóa_không_dấu, nhãn_chuẩn) trên bản text không dấu.
    window: nếu truyền vào, chỉ tìm trong đoạn text đó (dùng khi cần bám theo nhãn)."""
    hay = window if window is not None else text_kd
    for kd, canon in canon_list:
        if kd in hay:
            return canon
    return None


# Danh mục trường/ngành phổ biến để so khớp mờ (bỏ dấu) — có thể mở rộng thêm.
# Nguồn: TRUONG_CONG_LAP_OK cộng thêm 1 số trường/ngành hay gặp khác.
_KNOWN_SCHOOLS = [
    "Học viện Ngân hàng", "Banking Academy",
    "Đại học Kinh tế Quốc dân", "National Economics University",
    "Đại học Ngoại thương", "Foreign Trade University",
    "Học viện Tài chính", "Academy of Finance",
    "Đại học Bách khoa Hà Nội", "Hanoi University of Science and Technology",
    "Đại học Kinh tế TP.HCM", "Đại học Kinh tế - Đại học Quốc gia Hà Nội",
    "Đại học Troy", "Troy University",
    "Đại học RMIT", "RMIT University",
    "Học viện Tài chính", "Đại học Thương mại",
]
_KNOWN_MAJORS = [
    "Hệ thống thông tin quản lý", "Management Information System",
    "Tài chính Ngân hàng", "Banking and Finance",
    "Quản trị Kinh doanh", "Business Administration",
    "Kế toán", "Accounting",
    "Kinh tế đối ngoại", "Công nghệ thông tin",
    "Kinh doanh Tổng hợp", "General Business",
    "Luật kinh tế", "Kinh tế chính trị",
]


def _dict_match(text: str, candidates: list):
    """So khớp mờ (bỏ dấu) — trả về ứng viên KHỚP DÀI NHẤT tìm thấy trong text (hoặc None)."""
    best = None
    for cand in candidates:
        if _khong_dau(cand) in _khong_dau(text):
            if best is None or len(cand) > len(best):
                best = cand
    return best


def extract_diploma_fields(raw_text: str) -> dict:
    """
    Trích xuất các trường thông tin có cấu trúc (họ tên, ngày sinh, trường, ngành,
    xếp loại, loại hình đào tạo, văn bằng...) từ text OCR thô của văn bằng.
    Đây là bước GỢI Ý ĐIỀN SẴN cho ứng viên — không phải căn cứ xét duyệt.
    """
    text = raw_text or ""
    result = {}

    # Ngày sinh: thử các mẫu nhãn trước, nếu không có thì fallback lấy
    # bất kỳ dd/mm/yyyy hợp lệ nào có năm sinh nằm trong khoảng hợp lý.
    for pat in _NGAY_SINH_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            d, mo, y = m.groups()
            try:
                if 1955 <= int(y) <= 2010:
                    result["ngay_sinh"] = f"{int(d):02d}/{int(mo):02d}/{y}"
                    break
            except ValueError:
                pass
    if "ngay_sinh" not in result:
        for m in re.finditer(r"(\d{1,2})\s*[\/\.]\s*(\d{1,2})\s*[\/\.]\s*(\d{4})", text):
            d, mo, y = m.groups()
            if 1955 <= int(y) <= 2010 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                result["ngay_sinh"] = f"{int(d):02d}/{int(mo):02d}/{y}"
                break

    for pat in _HOTEN_PATTERNS:
        m = re.search(pat, text)
        if m:
            val = re.sub(r"\s+", " ", m.group(1)).strip(" .,:;-")
            if val:
                result["ho_ten"] = val.title()
                break

    text_kd = _khong_dau(text)  # bản không dấu, dùng chung cho các so khớp bên dưới

    m = re.search(_XEP_LOAI_LABEL_KD + r"(.{0,25})", text_kd)
    if m:
        xep_loai = _match_canon(text_kd, _XEP_LOAI_CANON, window=m.group(1))
        if xep_loai:
            result["xep_loai"] = xep_loai

    loai_hinh = _match_canon(text_kd, _LOAI_HINH_CANON)
    if loai_hinh:
        result["loai_hinh"] = loai_hinh

    van_bang = _match_canon(text_kd, _VAN_BANG_CANON)
    if van_bang:
        result["van_bang"] = van_bang

    # Trường / Chuyên ngành: so khớp từ điển thay vì bắt theo nhãn — vì nhãn
    # "Trường:"/"Ngành:" trên văn bằng thật rất hay bị OCR nuốt mất.
    truong = _dict_match(text, _KNOWN_SCHOOLS)
    if truong:
        result["truong"] = truong
    nganh = _dict_match(text, _KNOWN_MAJORS)
    if nganh:
        result["chuyen_nganh"] = nganh

    # Đối chiếu thêm với rules.xlsx (nếu có) để chuẩn hoá cách viết — tham khảo thêm
    try:
        df_rules = get_recruitment_rules()
        if "truong" not in result:
            for _, row in df_rules.iterrows():
                if _khong_dau(str(row["Truong_Dai_Hoc"])) in _khong_dau(text):
                    result["truong"] = row["Truong_Dai_Hoc"]
                    break
    except Exception:
        pass

    return result


def _tach_ho_ten(ho_ten_day_du: str):
    """Tách 'Họ tên đầy đủ' -> (họ đệm, tên) theo quy ước VN: từ cuối cùng là Tên."""
    parts = (ho_ten_day_du or "").split()
    if len(parts) < 2:
        return "", ho_ten_day_du or ""
    return " ".join(parts[:-1]), parts[-1]


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
    st.session_state.ocr_status = None      # None | 'OCR_OK' | 'OCR_NO_TEXT'
if 'ocr_school' not in st.session_state:
    st.session_state.ocr_school = ""        # trường trích xuất được từ văn bằng (để lưu/đối chiếu)
if 'ocr_major' not in st.session_state:
    st.session_state.ocr_major = ""         # ngành trích xuất được từ văn bằng (để lưu/đối chiếu)
if 'ocr_prefilled_file' not in st.session_state:
    st.session_state.ocr_prefilled_file = None   # tránh điền lại/ghi đè khi rerun cùng 1 file
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
        email_input = st.text_input("email", label_visibility="collapsed", placeholder="email")
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
    st.caption(
        "🔍 Hệ thống sẽ tự động quét văn bằng bằng OCR và **gợi ý điền sẵn** một số trường bên dưới "
        "(họ tên, ngày sinh, trường, chuyên ngành...). Đây chỉ là công cụ hỗ trợ tham khảo — "
        "**vui lòng luôn kiểm tra & chỉnh sửa lại** cho đúng trước khi nộp đơn. Quyết định xét duyệt "
        "hồ sơ luôn dựa trên toàn bộ thông tin bạn tự khai, có đối chiếu chéo với văn bằng đã quét."
    )

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
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            # Chỉ chạy OCR + điền sẵn form 1 LẦN cho mỗi file (tránh ghi đè
            # mỗi khi Streamlit rerun do người dùng gõ phím ở ô khác)
            if st.session_state.ocr_prefilled_file != file_id:
                file_bytes = uploaded_file.read()
                with st.spinner("⏳ Hệ thống đang quét tự động thông tin văn bằng bằng công cụ OCR..."):
                    raw_text = run_ocr_on_pdf(file_bytes)
                    fields = extract_diploma_fields(raw_text)

                st.session_state.ocr_prefilled_file = file_id
                # 3 trạng thái rõ ràng — KHÔNG được đồng nhất "đọc được chữ" với
                # "trích xuất được field cụ thể nào" (đây chính là lỗi khiến banner
                # báo thành công dù form không được điền field nào cả):
                if not raw_text.strip():
                    st.session_state.ocr_status = "OCR_NO_TEXT"       # không đọc được chữ gì
                elif not fields:
                    st.session_state.ocr_status = "OCR_TEXT_NO_FIELD" # đọc được chữ nhưng không khớp field nào
                else:
                    st.session_state.ocr_status = "OCR_OK"            # có ít nhất 1 field được điền sẵn
                st.session_state.ocr_school = fields.get("truong", "")
                st.session_state.ocr_major  = fields.get("chuyen_nganh", "")

                # ── Điền sẵn (prefill) vào form — ứng viên vẫn chỉnh sửa được bình thường ──
                if fields.get("ho_ten"):
                    ho_dem, ten = _tach_ho_ten(fields["ho_ten"])
                    if ten:
                        st.session_state["form_ten"] = ten
                    if ho_dem:
                        st.session_state["form_ho"] = ho_dem
                if fields.get("ngay_sinh"):
                    st.session_state["form_dob"] = fields["ngay_sinh"]

                first_cm_idx = st.session_state.cm_items[0]
                if fields.get("truong"):
                    st.session_state[f"cm_school_name_{first_cm_idx}"] = fields["truong"]

                    # Tự động chọn "Loại trường" nếu nhận diện được là 1 trong các
                    # trường công lập trong nước quen thuộc (NEU/FTU/AOF/BA...).
                    # Danh sách khớp với TRUONG_CONG_LAP_OK trong database.py để nhất
                    # quán với rule xét duyệt thật — nếu sau này thêm trường công lập
                    # mới vào rule xét duyệt, nhớ bổ sung cả ở đây.
                    _TRUONG_CONG_LAP_KEYWORDS = [
                        "kinh te quoc dan", "neu", "ngoai thuong", "ftu",
                        "hoc vien tai chinh", "aof", "hoc vien ngan hang", "ba",
                    ]
                    if any(k in _khong_dau(fields["truong"]) for k in _TRUONG_CONG_LAP_KEYWORDS):
                        st.session_state[f"cm_school_type_{first_cm_idx}"] = "Trường Công lập đào tạo trong nước"

                _TRINH_DO_OPT = ["Đại học", "Cao đẳng", "Thạc sĩ", "Tiến sĩ"]
                _VAN_BANG_OPT = ["Cử nhân", "Kỹ sư"]
                _LOAI_HINH_OPT = ["Chính quy", "Tại chức", "Liên thông"]
                _XEP_LOAI_OPT = ["Xuất sắc", "Giỏi", "Khá", "Trung bình", "Yếu"]
                _NHOM_MAJORS = {
                    "Khối ngành Kinh tế - Quản lý": ["Tài chính Ngân hàng", "Kế toán", "Quản trị Kinh doanh"],
                    "Khối ngành CNTT": ["Trí tuệ nhân tạo", "Khoa học máy tính", "Kỹ thuật máy tính"],
                    "Khối ngành Luật": ["Luật kinh tế", "Luật dân sự", "Luật quốc tế"],
                    "Khối ngành Kỹ thuật": ["Kỹ thuật điện", "Kỹ thuật cơ khí", "Kỹ thuật xây dựng"],
                }

                def _map_option(value, options):
                    if not value:
                        return None
                    v = _khong_dau(value)
                    for opt in options:
                        if _khong_dau(opt) in v or v in _khong_dau(opt):
                            return opt
                    return None

                if fields.get("van_bang"):
                    m = _map_option(fields["van_bang"], _VAN_BANG_OPT)
                    if m:
                        st.session_state[f"cm_degree_{first_cm_idx}"] = m
                        if not fields.get("trinh_do") and m == "Cử nhân":
                            st.session_state[f"cm_level_{first_cm_idx}"] = "Đại học"
                if fields.get("loai_hinh"):
                    m = _map_option(fields["loai_hinh"], _LOAI_HINH_OPT)
                    if m:
                        st.session_state[f"cm_train_type_{first_cm_idx}"] = m
                if fields.get("xep_loai"):
                    m = _map_option(fields["xep_loai"], _XEP_LOAI_OPT)
                    if m:
                        st.session_state[f"cm_rank_{first_cm_idx}"] = m

                # Chuyên ngành: thử khớp vào 1 trong các nhóm có sẵn; nếu không
                # khớp được nhóm nào thì đẩy sang "Khác" + điền text tự do
                if fields.get("chuyen_nganh"):
                    matched_group, matched_major = None, None
                    for grp, majors in _NHOM_MAJORS.items():
                        m = _map_option(fields["chuyen_nganh"], majors)
                        if m:
                            matched_group, matched_major = grp, m
                            break
                    if matched_group:
                        st.session_state[f"cm_group_{first_cm_idx}"] = matched_group
                        st.session_state[f"cm_major_select_{first_cm_idx}"] = matched_major
                    else:
                        st.session_state[f"cm_group_{first_cm_idx}"] = "Khác"
                        st.session_state[f"cm_major_text_{first_cm_idx}"] = fields["chuyen_nganh"]

                with st.expander("🔍 Nhật ký hệ thống — Dữ liệu chữ OCR trích xuất được"):
                    st.text(raw_text.strip() if raw_text.strip() else "[Không nhận diện được ký tự nào trên văn bằng]")
                    if fields:
                        st.markdown("**Các trường đã tự động nhận diện & điền sẵn vào form bên dưới:**")
                        st.json(fields)
                    else:
                        st.warning("Không trích xuất được trường thông tin có cấu trúc nào — vui lòng tự điền form thủ công.")

                st.rerun()

    if st.session_state.ocr_status == "OCR_OK":
        st.markdown("""
            <div style='background:#E3F2FD;border-left:4px solid #29B6F6;padding:10px 15px;
                        border-radius:4px;margin-top:8px;font-size:13px;color:#0D47A1;'>
                ✅ Hệ thống đã quét văn bằng và điền sẵn một số trường thông tin bên dưới.
                Vui lòng kiểm tra lại & chỉnh sửa nếu cần trước khi nộp đơn.
            </div>
        """, unsafe_allow_html=True)
    elif st.session_state.ocr_status == "OCR_TEXT_NO_FIELD":
        st.markdown("""
            <div style='background:#FFF3E0;border-left:4px solid #FB8C00;padding:10px 15px;
                        border-radius:4px;margin-top:8px;font-size:13px;color:#E65100;'>
                ⚠️ Hệ thống đọc được chữ trên văn bằng nhưng KHÔNG nhận diện được trường thông tin
                cụ thể nào (họ tên/trường/ngành...) để tự điền — có thể do văn bằng dùng font/định dạng
                chưa có trong danh mục nhận diện. Xem chi tiết chữ đã quét ở mục "🔍 Nhật ký hệ thống"
                bên dưới, và vui lòng tự điền đầy đủ thông tin bằng tay.
            </div>
        """, unsafe_allow_html=True)
    elif st.session_state.ocr_status == "OCR_NO_TEXT":
        st.markdown("""
            <div style='background:#FFF3E0;border-left:4px solid #FB8C00;padding:10px 15px;
                        border-radius:4px;margin-top:8px;font-size:13px;color:#E65100;'>
                ⚠️ Hệ thống không nhận diện được chữ trên văn bằng (ảnh mờ/nghiêng/độ phân giải thấp).
                Vui lòng tự điền đầy đủ thông tin bên dưới bằng tay.
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    # KHỐI 2: THÔNG TIN HỒ SƠ
    # ─────────────────────────────────────────────────────────────────
    with st.expander("▼ Thông tin Hồ sơ", expanded=True):
        st.caption("Vui lòng điền thông tin cá nhân của bạn. Các trường dấu (*) là bắt buộc.")

        c1, c2, c3 = st.columns(3)
        with c1: name_ten = st.text_input("Tên:*", key="form_ten")
        with c2: name_ho  = st.text_input("Họ và tên đệm:*", key="form_ho")
        with c3: gender   = st.selectbox("Giới tính:*", ["Lựa chọn", "Nam", "Nữ", "Khác"])

        c1, c2, c3 = st.columns(3)
        with c1: dob     = st.text_input("Ngày sinh (DD/MM/YYYY):*", key="form_dob", placeholder="Ví dụ: 07/04/2002")
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
                    "ocr_status", "ocr_school", "ocr_major", "ocr_prefilled_file",
                    "form_ten", "form_ho", "form_dob",
                    "cm_items", "nn_items", "cm_counter", "nn_counter"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()