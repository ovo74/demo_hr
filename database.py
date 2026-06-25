import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "demo_hr.db"

# =====================================================================
# KHỞI TẠO CƠ SỞ DỮ LIỆU
# =====================================================================

def get_connection():
    """Trả về kết nối SQLite, bật foreign key."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row        # truy cập cột theo tên
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Tạo 4 bảng nếu chưa tồn tại.
    Gọi hàm này một lần khi app khởi động.
    """
    conn = get_connection()
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # 1. UNG_VIEN — thông tin đăng nhập
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ung_vien (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE,
            mat_khau_hash TEXT,               -- để dành cho admin sau
            tao_luc       TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------
    # 2. HO_SO — thông tin hồ sơ (1 ứng viên : nhiều hồ sơ)
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ho_so (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            ung_vien_id        INTEGER NOT NULL REFERENCES ung_vien(id),

            -- Thông tin cá nhân
            ten                TEXT,
            ho_ten_dem         TEXT,
            gioi_tinh          TEXT,
            ngay_sinh          TEXT,
            noi_sinh           TEXT,
            dia_chi            TEXT,
            quan_huyen         TEXT,
            tinh_thanh_pho     TEXT,
            quoc_gia           TEXT,
            ma_buu_dien        TEXT,
            so_dien_thoai      TEXT,
            so_dien_thoai_khac TEXT,

            -- Giấy tờ
            cccd               TEXT,
            ngay_cap_cccd      TEXT,

            -- Thể chất & hôn nhân
            chieu_cao          TEXT,
            can_nang           TEXT,
            tinh_trang_hon_nhan TEXT,

            -- Thành tích
            thanh_tich_noi_bat TEXT,

            -- Kết quả OCR văn bằng
            ocr_status         TEXT,           -- 'APPROVE' | 'DENY' | NULL
            ocr_truong         TEXT,
            ocr_chuyen_nganh   TEXT,

            -- Quản trị
            trang_thai         TEXT DEFAULT 'cho_duyet',  -- cho_duyet | da_duyet | tu_choi
            nop_luc            TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------
    # 3. TRINH_DO_CHUYEN_MON — văn bằng (nhiều per hồ sơ)
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trinh_do_chuyen_mon (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_so_id            INTEGER NOT NULL REFERENCES ho_so(id) ON DELETE CASCADE,

            ngay_bat_dau        TEXT,
            ngay_ket_thuc       TEXT,
            trinh_do            TEXT,    -- Đại học / Cao đẳng / Thạc sĩ / Tiến sĩ
            van_bang            TEXT,    -- Cử nhân / Kỹ sư / Khác
            nhom_chuyen_nganh   TEXT,
            chuyen_nganh        TEXT,
            quoc_gia            TEXT,
            loai_truong         TEXT,
            ten_truong          TEXT,
            thoi_gian_khoa_hoc  TEXT,
            don_vi_thoi_gian    TEXT,    -- Năm / Tháng
            thang_diem          TEXT,    -- /10 | /4
            diem_tong_ket       TEXT,
            loai_hinh_dao_tao   TEXT,    -- Chính quy / Tại chức / Liên thông
            xep_loai            TEXT,    -- Xuất sắc / Giỏi / Khá / Trung bình / Yếu
            hoc_ham             TEXT     -- Không có / Phó giáo sư / Giáo sư
        )
    """)

    # ------------------------------------------------------------------
    # 4. TRINH_DO_NGOAI_NGU — ngoại ngữ (nhiều per hồ sơ)
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trinh_do_ngoai_ngu (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_so_id INTEGER NOT NULL REFERENCES ho_so(id) ON DELETE CASCADE,

            ngon_ngu TEXT,    -- Tiếng Anh / Tiếng Trung ...
            chung_chi TEXT,   -- IELTS / TOEIC / TOEFL / Hsk / JLPT
            diem      TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Khởi tạo database thành công:", DB_PATH)


# =====================================================================
# CÁC HÀM NGHIỆP VỤ
# =====================================================================

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def lay_hoac_tao_ung_vien(email: str, password: str = "") -> int:
    """
    Tìm ứng viên theo email. Nếu chưa có thì tạo mới.
    Trả về ung_vien.id.
    """
    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute("SELECT id FROM ung_vien WHERE email = ?", (email,)).fetchone()
    if row:
        ung_vien_id = row["id"]
    else:
        cur.execute(
            "INSERT INTO ung_vien (email, mat_khau_hash) VALUES (?, ?)",
            (email, _hash_password(password) if password else None)
        )
        ung_vien_id = cur.lastrowid
        conn.commit()

    conn.close()
    return ung_vien_id


def luu_ho_so(
    ung_vien_id: int,
    thong_tin: dict,
    ds_chuyen_mon: list[dict],
    ds_ngoai_ngu: list[dict],
) -> int:
    """
    Lưu toàn bộ hồ sơ vào DB trong một transaction.

    thong_tin     : dict map 1-1 với các cột của bảng ho_so
    ds_chuyen_mon : list[dict], mỗi dict là một hàng trinh_do_chuyen_mon
    ds_ngoai_ngu  : list[dict], mỗi dict là một hàng trinh_do_ngoai_ngu

    Trả về ho_so.id vừa tạo.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # --- 1. Chèn hồ sơ chính ---
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
                'cho_duyet'
            )
        """, {"ung_vien_id": ung_vien_id, **thong_tin})

        ho_so_id = cur.lastrowid

        # --- 2. Chèn từng văn bằng ---
        for cm in ds_chuyen_mon:
            cur.execute("""
                INSERT INTO trinh_do_chuyen_mon (
                    ho_so_id, ngay_bat_dau, ngay_ket_thuc, trinh_do,
                    van_bang, nhom_chuyen_nganh, chuyen_nganh, quoc_gia,
                    loai_truong, ten_truong, thoi_gian_khoa_hoc, don_vi_thoi_gian,
                    thang_diem, diem_tong_ket, loai_hinh_dao_tao, xep_loai, hoc_ham
                ) VALUES (
                    :ho_so_id, :ngay_bat_dau, :ngay_ket_thuc, :trinh_do,
                    :van_bang, :nhom_chuyen_nganh, :chuyen_nganh, :quoc_gia,
                    :loai_truong, :ten_truong, :thoi_gian_khoa_hoc, :don_vi_thoi_gian,
                    :thang_diem, :diem_tong_ket, :loai_hinh_dao_tao, :xep_loai, :hoc_ham
                )
            """, {"ho_so_id": ho_so_id, **cm})

        # --- 3. Chèn từng ngoại ngữ ---
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


# =====================================================================
# TRUY VẤN (dùng cho giao diện admin sau)
# =====================================================================

def lay_danh_sach_ho_so(trang_thai: str = None) -> list[dict]:
    """Lấy tất cả hồ sơ, có thể lọc theo trang_thai."""
    conn = get_connection()
    if trang_thai:
        rows = conn.execute("""
            SELECT h.*, u.email
            FROM ho_so h
            JOIN ung_vien u ON u.id = h.ung_vien_id
            WHERE h.trang_thai = ?
            ORDER BY h.nop_luc DESC
        """, (trang_thai,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT h.*, u.email
            FROM ho_so h
            JOIN ung_vien u ON u.id = h.ung_vien_id
            ORDER BY h.nop_luc DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def lay_chi_tiet_ho_so(ho_so_id: int) -> dict | None:
    """Lấy đầy đủ thông tin 1 hồ sơ bao gồm cả bảng con."""
    conn = get_connection()
    ho_so = conn.execute("""
        SELECT h.*, u.email
        FROM ho_so h
        JOIN ung_vien u ON u.id = h.ung_vien_id
        WHERE h.id = ?
    """, (ho_so_id,)).fetchone()

    if not ho_so:
        conn.close()
        return None

    chuyen_mon = conn.execute(
        "SELECT * FROM trinh_do_chuyen_mon WHERE ho_so_id = ?", (ho_so_id,)
    ).fetchall()

    ngoai_ngu = conn.execute(
        "SELECT * FROM trinh_do_ngoai_ngu WHERE ho_so_id = ?", (ho_so_id,)
    ).fetchall()

    conn.close()
    return {
        **dict(ho_so),
        "chuyen_mon": [dict(r) for r in chuyen_mon],
        "ngoai_ngu":  [dict(r) for r in ngoai_ngu],
    }


def cap_nhat_trang_thai(ho_so_id: int, trang_thai: str):
    """Admin duyệt / từ chối hồ sơ."""
    conn = get_connection()
    conn.execute(
        "UPDATE ho_so SET trang_thai = ? WHERE id = ?",
        (trang_thai, ho_so_id)
    )
    conn.commit()
    conn.close()
