import sqlite3
import hashlib
import os
from datetime import datetime, date


class EmailDaTonTaiError(Exception):
    """Raise khi email đã có hồ sơ trong DB — dùng để hiển thị lỗi thân thiện ở app.py."""
    pass

# Đường dẫn tuyệt đối — luôn trỏ đúng file dù chạy từ terminal nào
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_hr.db")

# =====================================================================
# KẾT NỐI & KHỞI TẠO
# =====================================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tạo toàn bộ bảng nếu chưa tồn tại. Gọi một lần khi app khởi động."""
    conn = get_connection()
    cur = conn.cursor()

    # 1. UNG_VIEN — thông tin đăng nhập
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ung_vien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            mat_khau_hash TEXT,
            tao_luc TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 2. HO_SO — thông tin hồ sơ chính
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ho_so (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ung_vien_id INTEGER NOT NULL REFERENCES ung_vien(id),
            ten TEXT,
            ho_ten_dem TEXT,
            gioi_tinh TEXT,
            ngay_sinh TEXT,
            noi_sinh TEXT,
            dia_chi TEXT,
            quan_huyen TEXT,
            tinh_thanh_pho TEXT,
            quoc_gia TEXT,
            ma_buu_dien TEXT,
            so_dien_thoai TEXT,
            so_dien_thoai_khac TEXT,
            cccd TEXT,
            ngay_cap_cccd TEXT,
            chieu_cao TEXT,
            can_nang TEXT,
            tinh_trang_hon_nhan TEXT,
            thanh_tich_noi_bat TEXT,
            ocr_status TEXT,
            ocr_truong TEXT,
            ocr_chuyen_nganh TEXT,
            trang_thai TEXT DEFAULT 'cho_duyet',
            nop_luc TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 3. TRINH_DO_CHUYEN_MON — văn bằng (nhiều bản ghi per hồ sơ)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trinh_do_chuyen_mon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_so_id INTEGER NOT NULL REFERENCES ho_so(id) ON DELETE CASCADE,
            ngay_bat_dau TEXT,
            ngay_ket_thuc TEXT,
            trinh_do TEXT,
            van_bang TEXT,
            nhom_chuyen_nganh TEXT,
            chuyen_nganh TEXT,
            quoc_gia TEXT,
            loai_truong TEXT,
            ten_truong TEXT,
            thoi_gian_khoa_hoc TEXT,
            don_vi_thoi_gian TEXT,
            thang_diem TEXT,
            diem_tong_ket TEXT,
            loai_hinh_dao_tao TEXT,
            xep_loai TEXT,
            hoc_ham TEXT
        )
    """)

    # 4. TRINH_DO_NGOAI_NGU — ngoại ngữ (nhiều bản ghi per hồ sơ)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trinh_do_ngoai_ngu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_so_id INTEGER NOT NULL REFERENCES ho_so(id) ON DELETE CASCADE,
            ngon_ngu TEXT,
            chung_chi TEXT,
            diem TEXT
        )
    """)

    conn.commit()
    conn.close()


# =====================================================================
# LOGIC TRẠNG THÁI TỰ ĐỘNG
# ─────────────────────────────────────────────────────────────────────
# Bản sao Y HỆT logic compute_status trong admin.py. Mục đích: khi ứng
# viên bấm "Nộp đơn" ở app.py, hồ sơ được chấm tự động NGAY LÚC NỘP và
# trang_thai được lưu thẳng kết quả (deny / approve / phong_van), thay vì
# luôn mặc định 'cho_duyet' rồi chờ admin xử lý tay từng hồ sơ.
#
# CHỈ giữ trang_thai = None (chờ duyệt) cho đúng 1 trường hợp: hồ sơ có
# trường/quốc gia đào tạo ở NƯỚC NGOÀI — vì đây là case cần admin xem xét
# thủ công (rule "recheck" trong admin.py), không thể tự động quyết.
#
# QUAN TRỌNG: hàm này được định nghĩa NGAY TẠI ĐÂY (không import từ
# admin.py) để tránh việc database.py vô tình kéo theo toàn bộ admin.py
# chạy (admin.py có st.set_page_config() và nhiều lệnh Streamlit ở cấp
# module — import nó từ app.py/database.py sẽ làm hỏng giao diện ứng viên).
# Nếu admin.py thay đổi rule trong tương lai, cần cập nhật đồng bộ cả 2 nơi.
# =====================================================================

FOREIGN = ["nước ngoài", "quốc tế", "international", "foreign"]

NHOM_CHAP_NHAN = ["kinh tế - quản lý", "kinh te - quan ly"]
CHUYEN_NGANH_LUAT_CHAP_NHAN = ["luật kinh tế", "luat kinh te"]

TRUONG_CONG_LAP_OK = [
    "kinh tế quốc dân", "neu",
    "ngoại thương", "ftu",
    "học viện tài chính", "aof",
    "học viện ngân hàng", "ba",
]
LOAI_TRUONG_CONG_LAP = "trường công lập đào tạo trong nước"

PHONG_VAN_IELTS = 7.0
PHONG_VAN_TOEIC = 785
PHONG_VAN_TOEFL = 550


def _parse_date(s):
    if not s:
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except Exception:
            pass
    return None


def _check_language_phong_van(ds_nn: list) -> bool:
    """True nếu có ít nhất 1 chứng chỉ đạt ngưỡng phỏng vấn."""
    for nn in ds_nn:
        cc = (nn.get("chung_chi") or "").upper()
        try:
            diem = float(str(nn.get("diem") or "0").replace(",", "."))
        except Exception:
            continue
        if "IELTS" in cc and diem > PHONG_VAN_IELTS:
            return True
        if "TOEIC" in cc and diem > PHONG_VAN_TOEIC:
            return True
        if "TOEFL" in cc and diem > PHONG_VAN_TOEFL:
            return True
    return False


def compute_status(thong_tin: dict, ds_chuyen_mon: list, ds_ngoai_ngu: list = None):
    """
    Trả về trang_thai tự động: "deny" | "cho_duyet" | "phong_van" | "approve".
    Thứ tự ưu tiên: deny → cho_duyet (nước ngoài, cần admin xét tay) →
    phong_van (đủ 3 điều kiện) → approve.

    Đây là bản sao 1:1 hàm compute_status trong admin.py, chỉ đổi tên
    tham số cho khớp với cách gọi từ luu_ho_so().
    """
    ds_ngoai_ngu = ds_ngoai_ngu or []
    reasons = []
    today = date.today()
    one_year_ago = date(today.year - 1, today.month, today.day)

    dob = _parse_date(thong_tin.get("ngay_sinh"))
    if dob:
        age = (today - dob).days / 365.25
        if age > 30:
            reasons.append(f"Quá tuổi ({int(age)} tuổi, tối đa 30)")
    else:
        reasons.append("Không xác định ngày sinh")

    recheck = False
    xet_phong_van_xep_loai = False
    xet_phong_van_ngay = False

    for cm in ds_chuyen_mon:
        td = (cm.get("trinh_do") or "").strip()
        lh = (cm.get("loai_hinh_dao_tao") or "").strip()
        diem = (cm.get("diem_tong_ket") or "").strip()
        thang = (cm.get("thang_diem") or "").strip()
        qg = (cm.get("quoc_gia") or "").strip().lower()
        lt = (cm.get("loai_truong") or "").strip()
        lt_low = lt.lower()
        truong = (cm.get("ten_truong") or "").strip().lower()
        nhom = (cm.get("nhom_chuyen_nganh") or "").strip().lower()
        cn = (cm.get("chuyen_nganh") or "").strip().lower()
        xep = (cm.get("xep_loai") or "").strip().lower()
        ngay_kt = _parse_date(cm.get("ngay_ket_thuc"))

        # ── Trình độ ──
        if "cao đẳng" in td.lower():
            reasons.append("Trình độ Cao đẳng không hợp lệ")

        # ── Điểm tổng kết ──
        try:
            if "/" in diem:
                p = diem.split("/")
                dv = float(p[0].replace(",", "."))
                sc = float(p[1].replace(",", "."))
                if sc >= 9 and dv < 6.5:
                    reasons.append(f"Điểm {dv}/{sc} < 6.5")
                elif 3 <= sc < 9 and dv < 2.5:
                    reasons.append(f"Điểm {dv}/{sc} < 2.5")
            else:
                dv = float(diem.replace(",", "."))
                if "/10" in thang and dv < 6.5:
                    reasons.append(f"Điểm {dv}/10 < 6.5")
                elif "/4" in thang and dv < 2.5:
                    reasons.append(f"Điểm {dv}/4 < 2.5")
        except Exception:
            pass

        # ── Loại hình đào tạo ──
        if lh and "chính quy" not in lh.lower():
            reasons.append(f"Loại hình '{lh}' không phải Chính quy")

        # ── Nhóm chuyên ngành (YC vị trí Chuyên viên KH) ──
        ok_nhom = any(k in nhom for k in NHOM_CHAP_NHAN)
        ok_luat = ("luật" in nhom) and any(k in cn for k in CHUYEN_NGANH_LUAT_CHAP_NHAN)
        if nhom and not ok_nhom and not ok_luat:
            reasons.append(
                f"Nhóm chuyên ngành '{cm.get('nhom_chuyen_nganh')}' "
                f"không phù hợp vị trí Chuyên viên Khách hàng"
            )

        # ── Tên trường (chỉ áp dụng khi Công lập trong nước) ──
        if LOAI_TRUONG_CONG_LAP in lt_low:
            ok_truong = any(k in truong for k in TRUONG_CONG_LAP_OK)
            if not ok_truong:
                reasons.append(
                    f"Trường '{cm.get('ten_truong')}' không thuộc danh sách "
                    f"công lập được chấp nhận (NEU, FTU, AOF, BA)"
                )

        # ── Recheck (nước ngoài) ──
        if any(k in qg for k in FOREIGN) or any(k in lt_low for k in FOREIGN):
            recheck = True

        # ── Điều kiện Phỏng vấn thẳng ──
        if "xuất sắc" in xep:
            xet_phong_van_xep_loai = True
        if ngay_kt and one_year_ago <= ngay_kt <= today:
            xet_phong_van_ngay = True

    lang_ok = _check_language_phong_van(ds_ngoai_ngu)
    du_phong_van = xet_phong_van_xep_loai and xet_phong_van_ngay and lang_ok

    if reasons:
        return "deny"
    if recheck:
        return "cho_duyet"
    if du_phong_van:
        return "phong_van"
    return "approve"


# =====================================================================
# NGHIỆP VỤ LƯU DỮ LIỆU
# =====================================================================

def lay_hoac_tao_ung_vien(email: str, password: str = "") -> int:
    """Tìm ứng viên theo email. Nếu chưa có thì INSERT mới. Trả về id."""
    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT id FROM ung_vien WHERE email = ?", (email,)
    ).fetchone()

    if row:
        ung_vien_id = row["id"]
    else:
        pw_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        cur.execute(
            "INSERT INTO ung_vien (email, mat_khau_hash) VALUES (?, ?)",
            (email, pw_hash)
        )
        ung_vien_id = cur.lastrowid
        conn.commit()

    conn.close()
    return ung_vien_id


def luu_ho_so(
    ung_vien_id: int,
    thong_tin: dict,
    ds_chuyen_mon: list,
    ds_ngoai_ngu: list,
) -> int:
    """
    Lưu toàn bộ hồ sơ vào DB trong một transaction.
    Trả về ho_so.id vừa INSERT.

    trang_thai được TÍNH TỰ ĐỘNG ngay lúc nộp bằng compute_status() —
    chỉ để None (chờ duyệt) khi hồ sơ thuộc case "cho_duyet" (trường/quốc
    gia nước ngoài, cần admin xem xét thủ công). Các trường hợp khác
    (deny / approve / phong_van) được quyết định và lưu thẳng luôn,
    admin có thể xem lại và ghi đè tay qua giao diện nếu cần.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # -- Kiểm tra trùng: 1 ung_vien chỉ được có 1 ho_so --
        existing = cur.execute(
            "SELECT id FROM ho_so WHERE ung_vien_id = ? LIMIT 1", (ung_vien_id,)
        ).fetchone()
        if existing:
            raise EmailDaTonTaiError(
                f"Hồ sơ của tài khoản này đã tồn tại (mã hồ sơ #{existing['id']}). "
                "Mỗi email chỉ được nộp một hồ sơ duy nhất."
            )

        # -- Tính trạng thái tự động ngay lúc nộp --
        computed = compute_status(thong_tin, ds_chuyen_mon, ds_ngoai_ngu)
        # "cho_duyet" là literal-truthy trong Python: nếu lưu thẳng chuỗi
        # này, nút "Duyệt danh sách" / bulk_save() trong admin.py sẽ luôn
        # giữ lại giá trị cũ và không bao giờ chuyển sang approve/deny
        # được nữa (xem admin.py: effective = trang_thai or computed_status).
        # Do đó phải lưu None để admin.py tự fallback đúng sang
        # computed_status khi cần.
        trang_thai_luu = None if computed == "cho_duyet" else computed

        # -- Hồ sơ chính --
        cur.execute("""
            INSERT INTO ho_so (
                ung_vien_id, ten, ho_ten_dem, gioi_tinh,
                ngay_sinh, noi_sinh, dia_chi, quan_huyen,
                tinh_thanh_pho, quoc_gia, ma_buu_dien,
                so_dien_thoai, so_dien_thoai_khac,
                cccd, ngay_cap_cccd,
                chieu_cao, can_nang, tinh_trang_hon_nhan,
                thanh_tich_noi_bat,
                ocr_status, ocr_truong, ocr_chuyen_nganh,
                trang_thai
            ) VALUES (
                :ung_vien_id, :ten, :ho_ten_dem, :gioi_tinh,
                :ngay_sinh, :noi_sinh, :dia_chi, :quan_huyen,
                :tinh_thanh_pho, :quoc_gia, :ma_buu_dien,
                :so_dien_thoai, :so_dien_thoai_khac,
                :cccd, :ngay_cap_cccd,
                :chieu_cao, :can_nang, :tinh_trang_hon_nhan,
                :thanh_tich_noi_bat,
                :ocr_status, :ocr_truong, :ocr_chuyen_nganh,
                :trang_thai
            )
        """, {
            "ung_vien_id": ung_vien_id,
            **thong_tin,
            "trang_thai": trang_thai_luu,
        })
        ho_so_id = cur.lastrowid

        # -- Trình độ chuyên môn --
        for cm in ds_chuyen_mon:
            cur.execute("""
                INSERT INTO trinh_do_chuyen_mon (
                    ho_so_id,
                    ngay_bat_dau, ngay_ket_thuc, trinh_do,
                    van_bang, nhom_chuyen_nganh, chuyen_nganh, quoc_gia,
                    loai_truong, ten_truong,
                    thoi_gian_khoa_hoc, don_vi_thoi_gian,
                    thang_diem, diem_tong_ket,
                    loai_hinh_dao_tao, xep_loai, hoc_ham
                ) VALUES (
                    :ho_so_id,
                    :ngay_bat_dau, :ngay_ket_thuc, :trinh_do,
                    :van_bang, :nhom_chuyen_nganh, :chuyen_nganh, :quoc_gia,
                    :loai_truong, :ten_truong,
                    :thoi_gian_khoa_hoc, :don_vi_thoi_gian,
                    :thang_diem, :diem_tong_ket,
                    :loai_hinh_dao_tao, :xep_loai, :hoc_ham
                )
            """, {"ho_so_id": ho_so_id, **cm})

        # -- Trình độ ngoại ngữ --
        for nn in ds_ngoai_ngu:
            cur.execute("""
                INSERT INTO trinh_do_ngoai_ngu (ho_so_id, ngon_ngu, chung_chi, diem)
                VALUES (:ho_so_id, :ngon_ngu, :chung_chi, :diem)
            """, {"ho_so_id": ho_so_id, **nn})

        conn.commit()
        return ho_so_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def kiem_tra_email_da_nop(email: str) -> bool:
    """
    Trả về True nếu email này đã có hồ sơ được nộp trong DB.
    Dùng để chặn trùng email khi ứng viên bấm Nộp đơn.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT h.id
        FROM ho_so h
        JOIN ung_vien u ON u.id = h.ung_vien_id
        WHERE u.email = ?
        LIMIT 1
    """, (email,)).fetchone()
    conn.close()
    return row is not None