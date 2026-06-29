# -*- coding: utf-8 -*-
"""
Script tạo dữ liệu mẫu chuẩn cho hệ thống tuyển dụng Vietcombank (demo_hr).
- Xóa toàn bộ data test cũ (nhập tay linh tinh).
- Tạo 35 hồ sơ ứng viên mẫu thực tế, đa dạng:
    + Trạng thái: approve / deny / cho_duyet / recheck (trộn đều)
    + Trình độ: Đại học / Cao đẳng / Thạc sĩ / Tiến sĩ
    + Trường trong nước / nước ngoài / liên kết
    + Ngoại ngữ: IELTS / TOEIC / TOEFL / Hsk / JLPT
    + Tuổi: phần lớn hợp lệ (<=30), một số quá tuổi để test rule deny
- KHÔNG đổi schema, KHÔNG đổi logic ứng dụng — chỉ thay dữ liệu.

Chạy: python3 seed_data.py
"""

import hashlib
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta
import random

DB_PATH = "demo_hr.db"

random.seed(42)

# Hằng số nhận diện "nước ngoài" — sao chép từ admin.py để tính computed_status
# y hệt logic thật của app, đảm bảo trang_thai mẫu khớp 100% với rule xét duyệt.
FOREIGN = ["nước ngoài", "liên kết"]


def parse_date_ddmmyyyy(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date()
    except Exception:
        return None


def compute_status(ho_so_dict, ds_cm):
    """Bản sao logic compute_status trong admin.py — dùng để kiểm chứng
    trang_thai gán cho data mẫu khớp đúng rule xét duyệt thật của hệ thống."""
    reasons = []
    today = date.today()

    dob = parse_date_ddmmyyyy(ho_so_dict.get("ngay_sinh"))
    if dob:
        age = (today - dob).days / 365.25
        if age > 30:
            reasons.append("qua_tuoi")
    else:
        reasons.append("khong_xac_dinh_ngay_sinh")

    recheck = False
    for cm in ds_cm:
        td = (cm.get("trinh_do") or "").strip()
        lh = (cm.get("loai_hinh_dao_tao") or "").strip()
        diem = (cm.get("diem_tong_ket") or "").strip()
        thang = (cm.get("thang_diem") or "").strip()
        qg = (cm.get("quoc_gia") or "").strip().lower()
        lt = (cm.get("loai_truong") or "").strip().lower()

        if "cao đẳng" in td.lower():
            reasons.append("cao_dang")

        try:
            if "/" in diem:
                p = diem.split("/")
                dv = float(p[0].replace(",", "."))
                sc = float(p[1].replace(",", "."))
                if sc >= 9 and dv < 6.5:
                    reasons.append("diem_thap")
                elif 3 <= sc < 9 and dv < 2.5:
                    reasons.append("diem_thap")
            else:
                dv = float(diem.replace(",", "."))
                if "/10" in thang and dv < 6.5:
                    reasons.append("diem_thap")
                elif "/4" in thang and dv < 2.5:
                    reasons.append("diem_thap")
        except Exception:
            pass

        if lh and "chính quy" not in lh.lower():
            reasons.append("khong_chinh_quy")

        if any(k in qg for k in FOREIGN) or any(k in lt for k in FOREIGN):
            recheck = True

    if reasons:
        return "deny"
    if recheck:
        return "cho_duyet"
    return "approve"

# ─────────────────────────────────────────────────────────────────────
# DANH SÁCH DỮ LIỆU NGUỒN (khớp đúng các option/enum có trong app.py)
# ─────────────────────────────────────────────────────────────────────

HO_NAM = ["Nguyễn Văn", "Trần Văn", "Lê Văn", "Phạm Văn", "Hoàng Văn",
          "Vũ Văn", "Đặng Văn", "Bùi Văn", "Đỗ Văn", "Ngô Văn"]
HO_NU = ["Nguyễn Thị", "Trần Thị", "Lê Thị", "Phạm Thị", "Hoàng Thị",
         "Vũ Thị", "Đặng Thị", "Bùi Thị", "Đỗ Thị", "Ngô Thị"]
TEN_NAM = ["Hùng", "Minh", "Đức", "Quân", "Long", "Tuấn", "Nam", "Phong",
           "Khải", "Bảo", "Sơn", "Anh", "Việt", "Đạt", "Kiên"]
TEN_NU = ["Linh", "Hương", "Trang", "Ngọc", "Anh", "Hà", "Mai", "Thảo",
          "Phương", "Yến", "Vy", "Quỳnh", "Nhi", "Lan", "Thu"]

TINH_THANH = ["Hà Nội", "TP. Hồ Chí Minh", "Thái Bình", "Đà Nẵng"]
QUAN_HUYEN = {
    "Hà Nội": ["Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Thanh Xuân", "Hoàng Mai"],
    "TP. Hồ Chí Minh": ["Quận 1", "Quận 3", "Bình Thạnh", "Tân Bình", "Gò Vấp"],
    "Thái Bình": ["Đông Hưng", "Hưng Hà", "Kiến Xương"],
    "Đà Nẵng": ["Hải Châu", "Thanh Khê", "Sơn Trà"],
}
DUONG = ["Nguyễn Trãi", "Lê Lợi", "Trần Hưng Đạo", "Hai Bà Trưng", "Hoàng Diệu",
         "Nguyễn Văn Cừ", "Phạm Văn Đồng", "Lý Thường Kiệt", "Kim Mã", "Cầu Giấy"]
MA_BUU_DIEN = {"Hà Nội": "100000", "TP. Hồ Chí Minh": "700000",
               "Thái Bình": "410000", "Đà Nẵng": "550000"}

NHOM_NGANH = {
    "Khối ngành Kinh tế - Quản lý": ["Tài chính Ngân hàng", "Kế toán", "Quản trị Kinh doanh"],
    "Khối ngành CNTT": ["Trí tuệ nhân tạo", "Khoa học máy tính", "Kỹ thuật máy tính"],
    "Khối ngành Luật": ["Luật kinh tế", "Luật dân sự", "Luật quốc tế"],
    "Khối ngành Kỹ thuật": ["Kỹ thuật điện", "Kỹ thuật cơ khí", "Kỹ thuật xây dựng"],
}

TRUONG_TRONG_NUOC = [
    ("NEU", "Trường Công lập đào tạo trong nước"),
    ("FTU", "Trường Công lập đào tạo trong nước"),
    ("BA", "Trường Công lập đào tạo trong nước"),
    ("UEH", "Trường Công lập đào tạo trong nước"),
    ("AOF", "Trường Công lập đào tạo trong nước"),
    ("Đại học Kinh tế - ĐHQGHN", "Trường Công lập đào tạo trong nước"),
    ("Đại học Thương mại", "Trường Dân lập đào tạo trong nước"),
    ("Đại học FPT", "Trường Dân lập đào tạo trong nước"),
    ("Đại học Hoa Sen", "Trường Dân lập đào tạo trong nước"),
]
TRUONG_NUOC_NGOAI = [
    ("National University of Singapore", "Trường nước ngoài"),
    ("University of Melbourne", "Trường nước ngoài"),
    ("RMIT Việt Nam", "Trường liên kết với trường nước ngoài đào tạo trong nước"),
    ("Đại học Việt Pháp (USTH liên kết)", "Trường liên kết với trường nước ngoài đào tạo trong nước"),
]

NGOAI_NGU_CHOICES = [
    ("Tiếng Anh", "IELTS"), ("Tiếng Anh", "TOEIC"), ("Tiếng Anh", "TOEFL"),
    ("Tiếng Trung", "Hsk"), ("Tiếng Nhật", "JLPT"), ("Tiếng Hàn", "JLPT"),
]

VAN_BANG = ["Cử nhân", "Kỹ sư"]
DON_VI_TG = "Năm"
HOC_HAM = ["Không có", "Lựa chọn"]


def random_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 28)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))


def fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def remove_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt để tạo email/slug hợp lệ (đ -> d riêng vì NFD không xử lý)."""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def hash_pw(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def build_profiles(n=35):
    profiles = []
    used_emails = set()

    for i in range(1, n + 1):
        is_nam = random.random() < 0.55
        if is_nam:
            ho = random.choice(HO_NAM)
            ten = random.choice(TEN_NAM)
            gioi_tinh = "Nam"
        else:
            ho = random.choice(HO_NU)
            ten = random.choice(TEN_NU)
            gioi_tinh = "Nữ"

        # Email duy nhất, không dấu, theo định dạng ten.ho@gmail.com
        ten_slug = remove_accents(ten).lower().replace(" ", "")
        ho_slug = remove_accents(ho.split()[-1]).lower().replace(" ", "")
        base_email = f"{ten_slug}.{ho_slug}{i}@gmail.com"
        while base_email in used_emails:
            base_email = f"{ten_slug}.{ho_slug}{i}{random.randint(1,99)}@gmail.com"
        used_emails.add(base_email)

        # Phân bổ "kịch bản" trạng thái mong muốn, để dữ liệu đa dạng và hợp lý:
        # 1) approve  (~40%) — Đại học/Thạc sĩ/Tiến sĩ, Chính quy, điểm cao, trong nước, tuổi <=30
        # 2) deny     (~25%) — vi phạm 1 trong các rule: quá tuổi / Cao đẳng / điểm thấp / không Chính quy
        # 3) recheck  (~20%) — trường/quốc gia nước ngoài, các tiêu chí khác đều ổn
        # 4) cho_duyet (~15%) — hồ sơ vừa nộp, admin chưa xử lý
        roll = random.random()
        if roll < 0.40:
            scenario = "approve"
        elif roll < 0.65:
            scenario = "deny"
        elif roll < 0.85:
            scenario = "recheck"
        else:
            scenario = "cho_duyet"

        # Ngày sinh theo scenario
        if scenario == "deny" and random.random() < 0.4:
            # một phần case deny là do quá tuổi (>30)
            dob = random_date(1985, 1994)
        else:
            # Sinh 1997-2004 -> tuổi ~22-29 tính đến giữa 2026, chắc chắn <=30
            # (tránh sinh 1996 vì người sinh đầu 1996 đã vừa quá 30 tuổi,
            # gây deny ngoài ý muốn cho case approve/recheck).
            dob = random_date(1997, 2004)

        tinh = random.choice(TINH_THANH)
        quan = random.choice(QUAN_HUYEN[tinh])
        dia_chi = f"Số {random.randint(1,200)} {random.choice(DUONG)}"

        sdt = "09" + "".join(str(random.randint(0, 9)) for _ in range(8))
        sdt_khac = "03" + "".join(str(random.randint(0, 9)) for _ in range(8))
        cccd = "".join(str(random.randint(0, 9)) for _ in range(12))
        ngay_cap_cccd = fmt(random_date(2018, 2024))

        chieu_cao = str(random.randint(155, 182))
        can_nang = str(random.randint(48, 80))
        hon_nhan = random.choices(
            ["Độc thân", "Đã kết hôn", "Khác"], weights=[80, 18, 2]
        )[0]

        thanh_tich_options = [
            "", "Sinh viên 5 tốt cấp trường", "Học bổng khuyến học 3 năm liên tiếp",
            "Giải Ba Olympic Tin học sinh viên", "Thành viên CLB Nghiên cứu khoa học",
            "Đại diện sinh viên trao đổi tại Singapore",
        ]
        thanh_tich = random.choice(thanh_tich_options)

        # ---- Học vấn (trinh_do_chuyen_mon) ----
        nhom = random.choice(list(NHOM_NGANH.keys()))
        chuyen_nganh = random.choice(NHOM_NGANH[nhom])

        if scenario == "deny" and random.random() < 0.35:
            trinh_do = "Cao đẳng"
        else:
            trinh_do = random.choices(
                ["Đại học", "Thạc sĩ", "Tiến sĩ"], weights=[75, 20, 5]
            )[0]

        van_bang = random.choice(VAN_BANG)

        if scenario == "recheck":
            ten_truong, loai_truong = random.choice(TRUONG_NUOC_NGOAI)
            quoc_gia_hs = "Nước ngoài"
            quoc_gia_cm = "Nước ngoài" if "nước ngoài" in loai_truong.lower() and "liên kết" not in loai_truong.lower() else "Việt Nam"
        else:
            ten_truong, loai_truong = random.choice(TRUONG_TRONG_NUOC)
            quoc_gia_hs = "Việt Nam"
            quoc_gia_cm = "Việt Nam"

        nam_bat_dau = dob.year + random.randint(18, 19)
        so_nam_hoc = 1 if trinh_do == "Thạc sĩ" else (3 if trinh_do == "Tiến sĩ" else random.choice([4, 4, 5]))
        ngay_bat_dau = fmt(date(nam_bat_dau, random.choice([8, 9]), random.randint(1, 28)))
        ngay_ket_thuc = fmt(date(nam_bat_dau + so_nam_hoc, random.choice([6, 7]), random.randint(1, 28)))

        if scenario == "deny" and random.random() < 0.35:
            loai_hinh = random.choice(["Tại chức", "Liên thông"])
        else:
            loai_hinh = "Chính quy"

        thang_diem = "/10"
        if scenario == "deny" and random.random() < 0.4:
            diem_tong_ket = str(round(random.uniform(4.0, 6.0), 1))  # điểm thấp, fail rule
        else:
            diem_tong_ket = str(round(random.uniform(6.6, 9.8), 1))

        if float(diem_tong_ket) >= 9.0:
            xep_loai = "Xuất sắc"
        elif float(diem_tong_ket) >= 8.0:
            xep_loai = "Giỏi"
        elif float(diem_tong_ket) >= 6.5:
            xep_loai = "Khá"
        else:
            xep_loai = "Trung bình"

        hoc_ham = random.choices(HOC_HAM, weights=[85, 15])[0]

        # ---- Ngoại ngữ ----
        ngon_ngu, chung_chi = random.choice(NGOAI_NGU_CHOICES)
        if chung_chi == "IELTS":
            diem_nn = str(round(random.uniform(5.5, 8.5), 1))
        elif chung_chi == "TOEIC":
            diem_nn = str(random.randint(550, 990))
        elif chung_chi == "TOEFL":
            diem_nn = str(random.randint(70, 110))
        elif chung_chi == "Hsk":
            diem_nn = str(random.randint(3, 6))
        else:  # JLPT
            diem_nn = random.choice(["N1", "N2", "N3"])

        # ---- trang_thai lưu DB ----
        # Tính bằng đúng hàm compute_status (sao chép từ admin.py) trên chính
        # dữ liệu vừa sinh, để trang_thai mẫu LUÔN khớp logic xét duyệt thật.
        ho_so_tam = {"ngay_sinh": fmt(dob)}
        cm_tam = [{
            "trinh_do": trinh_do,
            "loai_hinh_dao_tao": loai_hinh,
            "diem_tong_ket": diem_tong_ket,
            "thang_diem": thang_diem,
            "quoc_gia": quoc_gia_cm,
            "loai_truong": loai_truong,
        }]
        computed = compute_status(ho_so_tam, cm_tam)

        if computed == "cho_duyet":
            # QUAN TRỌNG: để None (NULL trong DB), KHÔNG phải literal "cho_duyet".
            # admin.py tính: effective = trang_thai or computed_status
            # Chuỗi "cho_duyet" là truthy trong Python -> nếu gán literal,
            # bulk_save()/nút "Duyệt danh sách" sẽ luôn ghi đè lại đúng giá trị
            # cũ "cho_duyet" và KHÔNG BAO GIỜ chuyển được sang approve/deny.
            trang_thai = None
        else:
            # approve / deny: admin đã duyệt đúng theo rule thật.
            trang_thai = computed

        ocr_status = "APPROVE" if computed in ("approve", "cho_duyet") else "REJECT"

        profile = {
            "email": base_email,
            "password": "Test@123",
            "ten": ten,
            "ho_ten_dem": ho,
            "gioi_tinh": gioi_tinh,
            "ngay_sinh": fmt(dob),
            "noi_sinh": tinh,
            "dia_chi": dia_chi,
            "quan_huyen": quan,
            "tinh_thanh_pho": tinh,
            "quoc_gia": quoc_gia_hs,
            "ma_buu_dien": MA_BUU_DIEN[tinh],
            "so_dien_thoai": sdt,
            "so_dien_thoai_khac": sdt_khac,
            "cccd": cccd,
            "ngay_cap_cccd": ngay_cap_cccd,
            "chieu_cao": chieu_cao,
            "can_nang": can_nang,
            "tinh_trang_hon_nhan": hon_nhan,
            "thanh_tich_noi_bat": thanh_tich,
            "ocr_status": ocr_status,
            "ocr_truong": ten_truong,
            "ocr_chuyen_nganh": chuyen_nganh,
            "trang_thai": trang_thai,
            "hoc_van": {
                "ngay_bat_dau": ngay_bat_dau,
                "ngay_ket_thuc": ngay_ket_thuc,
                "trinh_do": trinh_do,
                "van_bang": van_bang,
                "nhom_chuyen_nganh": nhom,
                "chuyen_nganh": chuyen_nganh,
                "quoc_gia": quoc_gia_cm,
                "loai_truong": loai_truong,
                "ten_truong": ten_truong,
                "thoi_gian_khoa_hoc": str(so_nam_hoc),
                "don_vi_thoi_gian": DON_VI_TG,
                "thang_diem": thang_diem,
                "diem_tong_ket": diem_tong_ket,
                "loai_hinh_dao_tao": loai_hinh,
                "xep_loai": xep_loai,
                "hoc_ham": hoc_ham,
            },
            "ngoai_ngu": {
                "ngon_ngu": ngon_ngu,
                "chung_chi": chung_chi,
                "diem": diem_nn,
            },
        }
        profiles.append(profile)

    return profiles


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ---- 1. XÓA TOÀN BỘ DATA CŨ (giữ nguyên schema) ----
    for table in ["trinh_do_ngoai_ngu", "trinh_do_chuyen_mon", "ho_so", "ung_vien"]:
        cur.execute(f"DELETE FROM {table}")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN "
                "('ung_vien','ho_so','trinh_do_chuyen_mon','trinh_do_ngoai_ngu')")
    conn.commit()

    # ---- 2. TẠO DATA MẪU MỚI ----
    profiles = build_profiles(35)

    nop_luc_base = date(2026, 6, 1)

    for idx, p in enumerate(profiles):
        # ung_vien
        pw_hash = hash_pw(p["password"])
        cur.execute(
            "INSERT INTO ung_vien (email, mat_khau_hash, tao_luc) VALUES (?, ?, ?)",
            (p["email"], pw_hash, f"2026-06-{(idx % 28) + 1:02d} 09:{(idx*7) % 60:02d}:00")
        )
        ung_vien_id = cur.lastrowid

        # ho_so
        nop_luc = nop_luc_base + timedelta(days=idx)
        cur.execute("""
            INSERT INTO ho_so (
                ung_vien_id, ten, ho_ten_dem, gioi_tinh, ngay_sinh, noi_sinh,
                dia_chi, quan_huyen, tinh_thanh_pho, quoc_gia, ma_buu_dien,
                so_dien_thoai, so_dien_thoai_khac, cccd, ngay_cap_cccd,
                chieu_cao, can_nang, tinh_trang_hon_nhan, thanh_tich_noi_bat,
                ocr_status, ocr_truong, ocr_chuyen_nganh, trang_thai, nop_luc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ung_vien_id, p["ten"], p["ho_ten_dem"], p["gioi_tinh"], p["ngay_sinh"], p["noi_sinh"],
            p["dia_chi"], p["quan_huyen"], p["tinh_thanh_pho"], p["quoc_gia"], p["ma_buu_dien"],
            p["so_dien_thoai"], p["so_dien_thoai_khac"], p["cccd"], p["ngay_cap_cccd"],
            p["chieu_cao"], p["can_nang"], p["tinh_trang_hon_nhan"], p["thanh_tich_noi_bat"],
            p["ocr_status"], p["ocr_truong"], p["ocr_chuyen_nganh"], p["trang_thai"],
            nop_luc.strftime("%Y-%m-%d %H:%M:%S")
        ))
        ho_so_id = cur.lastrowid

        # trinh_do_chuyen_mon
        hv = p["hoc_van"]
        cur.execute("""
            INSERT INTO trinh_do_chuyen_mon (
                ho_so_id, ngay_bat_dau, ngay_ket_thuc, trinh_do, van_bang,
                nhom_chuyen_nganh, chuyen_nganh, quoc_gia, loai_truong, ten_truong,
                thoi_gian_khoa_hoc, don_vi_thoi_gian, thang_diem, diem_tong_ket,
                loai_hinh_dao_tao, xep_loai, hoc_ham
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ho_so_id, hv["ngay_bat_dau"], hv["ngay_ket_thuc"], hv["trinh_do"], hv["van_bang"],
            hv["nhom_chuyen_nganh"], hv["chuyen_nganh"], hv["quoc_gia"], hv["loai_truong"], hv["ten_truong"],
            hv["thoi_gian_khoa_hoc"], hv["don_vi_thoi_gian"], hv["thang_diem"], hv["diem_tong_ket"],
            hv["loai_hinh_dao_tao"], hv["xep_loai"], hv["hoc_ham"]
        ))

        # trinh_do_ngoai_ngu
        nn = p["ngoai_ngu"]
        cur.execute("""
            INSERT INTO trinh_do_ngoai_ngu (ho_so_id, ngon_ngu, chung_chi, diem)
            VALUES (?,?,?,?)
        """, (ho_so_id, nn["ngon_ngu"], nn["chung_chi"], nn["diem"]))

    conn.commit()

    # ---- 3. KIỂM TRA NHANH ----
    print("=== KẾT QUẢ SEED DATA ===")
    for table in ["ung_vien", "ho_so", "trinh_do_chuyen_mon", "trinh_do_ngoai_ngu"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {cur.fetchone()[0]} dòng")

    cur.execute("SELECT trang_thai, COUNT(*) FROM ho_so GROUP BY trang_thai")
    print("\nPhân bố trang_thai:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()


if __name__ == "__main__":
    seed()