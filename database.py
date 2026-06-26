import sqlite3
import hashlib
import os

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
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE,
            mat_khau_hash TEXT,
            tao_luc       TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # 2. HO_SO — thông tin hồ sơ chính
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ho_so (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            ung_vien_id         INTEGER NOT NULL REFERENCES ung_vien(id),

            ten                 TEXT,
            ho_ten_dem          TEXT,
            gioi_tinh           TEXT,
            ngay_sinh           TEXT,
            noi_sinh            TEXT,
            dia_chi             TEXT,
            quan_huyen          TEXT,
            tinh_thanh_pho      TEXT,
            quoc_gia            TEXT,
            ma_buu_dien         TEXT,
            so_dien_thoai       TEXT,
            so_dien_thoai_khac  TEXT,
            cccd                TEXT,
            ngay_cap_cccd       TEXT,
            chieu_cao           TEXT,
            can_nang            TEXT,
            tinh_trang_hon_nhan TEXT,
            thanh_tich_noi_bat  TEXT,

            ocr_status          TEXT,
            ocr_truong          TEXT,
            ocr_chuyen_nganh    TEXT,

            trang_thai          TEXT DEFAULT 'cho_duyet',
            nop_luc             TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 3. TRINH_DO_CHUYEN_MON — văn bằng (nhiều bản ghi per hồ sơ)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trinh_do_chuyen_mon (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_so_id            INTEGER NOT NULL REFERENCES ho_so(id) ON DELETE CASCADE,

            ngay_bat_dau        TEXT,
            ngay_ket_thuc       TEXT,
            trinh_do            TEXT,
            van_bang            TEXT,
            nhom_chuyen_nganh   TEXT,
            chuyen_nganh        TEXT,
            quoc_gia            TEXT,
            loai_truong         TEXT,
            ten_truong          TEXT,
            thoi_gian_khoa_hoc  TEXT,
            don_vi_thoi_gian    TEXT,
            thang_diem          TEXT,
            diem_tong_ket       TEXT,
            loai_hinh_dao_tao   TEXT,
            xep_loai            TEXT,
            hoc_ham             TEXT
        )
    """)

    # 4. TRINH_DO_NGOAI_NGU — ngoại ngữ (nhiều bản ghi per hồ sơ)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trinh_do_ngoai_ngu (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_so_id  INTEGER NOT NULL REFERENCES ho_so(id) ON DELETE CASCADE,

            ngon_ngu  TEXT,
            chung_chi TEXT,
            diem      TEXT
        )
    """)

    conn.commit()
    conn.close()


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
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
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
                'cho_duyet'
            )
        """, {"ung_vien_id": ung_vien_id, **thong_tin})

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