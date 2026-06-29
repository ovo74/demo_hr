# -*- coding: utf-8 -*-
"""
Script THÊM 120 hồ sơ ứng viên mẫu mới vào demo_hr.db, theo ĐÚNG logic
compute_status MỚI nhất trong admin.py (đã có thêm trạng thái "phong_van"
và các rule về nhóm chuyên ngành / trường công lập / FOREIGN mới).

QUAN TRỌNG: Script này KHÔNG xóa dữ liệu cũ. Nó chỉ INSERT thêm 120 hồ sơ
mới, nối tiếp vào 35 hồ sơ hiện có (admin đã tự tay xử lý trạng thái cho
35 hồ sơ đó rồi, không được đụng vào).

Đảm bảo đủ cả 4 trạng thái xuất hiện trong 120 hồ sơ mới:
  - "phong_van"  (🎯 Phỏng vấn thẳng) — Xuất sắc + tốt nghiệp <1 năm + ngoại ngữ cao
  - "approve"    (✅ Đủ điều kiện)
  - "deny"       (❌ Từ chối)
  - "cho_duyet"  (⏳ Chờ duyệt — do trường/quốc gia nước ngoài, cần admin xét tay)

Chạy: python3 seed_extra_120.py
"""

import hashlib
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta
import random

DB_PATH = "demo_hr.db"

random.seed(2026)

# ─────────────────────────────────────────────────────────────────────
# BẢN SAO Y NGUYÊN LOGIC compute_status TỪ admin.py (bản mới nhất trên
# GitHub) — để trang_thai data mẫu khớp 100% với rule xét duyệt thật.
# ─────────────────────────────────────────────────────────────────────

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


def parse_date(s):
    if not s:
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except Exception:
            pass
    return None


def check_language_phong_van(ds_nn: list) -> bool:
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


def compute_status(c, ds_cm, ds_nn=None):
    """Bản sao 1:1 hàm compute_status trong admin.py (commit mới nhất)."""
    ds_nn = ds_nn or []
    reasons = []
    today = date.today()
    one_year_ago = date(today.year - 1, today.month, today.day)

    dob = parse_date(c.get("ngay_sinh"))
    if dob:
        age = (today - dob).days / 365.25
        if age > 30:
            reasons.append(f"qua_tuoi_{int(age)}")
    else:
        reasons.append("khong_xac_dinh_ngay_sinh")

    recheck = False
    xet_phong_van_xep_loai = False
    xet_phong_van_ngay = False

    for cm in ds_cm:
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
        ngay_kt = parse_date(cm.get("ngay_ket_thuc"))

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

        ok_nhom = any(k in nhom for k in NHOM_CHAP_NHAN)
        ok_luat = ("luật" in nhom) and any(k in cn for k in CHUYEN_NGANH_LUAT_CHAP_NHAN)
        if nhom and not ok_nhom and not ok_luat:
            reasons.append("nhom_chuyen_nganh_khong_phu_hop")

        if LOAI_TRUONG_CONG_LAP in lt_low:
            ok_truong = any(k in truong for k in TRUONG_CONG_LAP_OK)
            if not ok_truong:
                reasons.append("truong_cong_lap_khong_trong_danh_sach")

        if any(k in qg for k in FOREIGN) or any(k in lt_low for k in FOREIGN):
            recheck = True

        if "xuất sắc" in xep:
            xet_phong_van_xep_loai = True
        if ngay_kt and one_year_ago <= ngay_kt <= today:
            xet_phong_van_ngay = True

    lang_ok = check_language_phong_van(ds_nn)
    du_phong_van = xet_phong_van_xep_loai and xet_phong_van_ngay and lang_ok

    if reasons:
        return "deny"
    if recheck:
        return "cho_duyet"
    if du_phong_van:
        return "phong_van"
    return "approve"


# ─────────────────────────────────────────────────────────────────────
# DANH SÁCH DỮ LIỆU NGUỒN
# ─────────────────────────────────────────────────────────────────────

HO_NAM = ["Nguyễn Văn", "Trần Văn", "Lê Văn", "Phạm Văn", "Hoàng Văn",
          "Vũ Văn", "Đặng Văn", "Bùi Văn", "Đỗ Văn", "Ngô Văn",
          "Dương Văn", "Lý Văn", "Phan Văn", "Trương Văn", "Đinh Văn"]
HO_NU = ["Nguyễn Thị", "Trần Thị", "Lê Thị", "Phạm Thị", "Hoàng Thị",
         "Vũ Thị", "Đặng Thị", "Bùi Thị", "Đỗ Thị", "Ngô Thị",
         "Dương Thị", "Lý Thị", "Phan Thị", "Trương Thị", "Đinh Thị"]
TEN_NAM = ["Hùng", "Minh", "Đức", "Quân", "Long", "Tuấn", "Nam", "Phong",
           "Khải", "Bảo", "Sơn", "Anh", "Việt", "Đạt", "Kiên",
           "Hiếu", "Khang", "Phúc", "Thắng", "Trung", "Vinh", "Duy",
           "Hoàng", "Quang", "Thành"]
TEN_NU = ["Linh", "Hương", "Trang", "Ngọc", "Anh", "Hà", "Mai", "Thảo",
          "Phương", "Yến", "Vy", "Quỳnh", "Nhi", "Lan", "Thu",
          "Hằng", "Hiền", "Trinh", "Tâm", "Nga", "Thư", "Diệp",
          "Vân", "My", "Giang"]

TINH_THANH = ["Hà Nội", "TP. Hồ Chí Minh", "Thái Bình", "Đà Nẵng"]
QUAN_HUYEN = {
    "Hà Nội": ["Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Thanh Xuân", "Hoàng Mai",
               "Ba Đình", "Long Biên", "Tây Hồ", "Nam Từ Liêm"],
    "TP. Hồ Chí Minh": ["Quận 1", "Quận 3", "Bình Thạnh", "Tân Bình", "Gò Vấp",
                         "Quận 7", "Phú Nhuận", "Thủ Đức", "Quận 10"],
    "Thái Bình": ["Đông Hưng", "Hưng Hà", "Kiến Xương", "Quỳnh Phụ", "Vũ Thư"],
    "Đà Nẵng": ["Hải Châu", "Thanh Khê", "Sơn Trà", "Ngũ Hành Sơn", "Liên Chiểu"],
}
DUONG = ["Nguyễn Trãi", "Lê Lợi", "Trần Hưng Đạo", "Hai Bà Trưng", "Hoàng Diệu",
         "Nguyễn Văn Cừ", "Phạm Văn Đồng", "Lý Thường Kiệt", "Kim Mã", "Cầu Giấy",
         "Nguyễn Huệ", "Trường Chinh", "Giải Phóng", "Tô Hiệu", "Bạch Đằng"]
MA_BUU_DIEN = {"Hà Nội": "100000", "TP. Hồ Chí Minh": "700000",
               "Thái Bình": "410000", "Đà Nẵng": "550000"}

# QUAN TRỌNG: chỉ "Kinh tế - Quản lý" và "Luật" (với chuyên ngành Luật kinh tế)
# được compute_status MỚI chấp nhận cho vị trí Chuyên viên Khách hàng.
# Các nhóm CNTT/Kỹ thuật vẫn được sinh ra (để test rule deny) nhưng KHÔNG
# chiếm tỉ trọng chính, để phần lớn hồ sơ "hợp lệ" thực sự hợp lệ.
NHOM_NGANH_OK = {
    "Khối ngành Kinh tế - Quản lý": ["Tài chính Ngân hàng", "Kế toán", "Quản trị Kinh doanh"],
    "Khối ngành Luật": ["Luật kinh tế"],  # CHỈ Luật kinh tế mới được chấp nhận
}
NHOM_NGANH_KHONG_OK = {
    "Khối ngành CNTT": ["Trí tuệ nhân tạo", "Khoa học máy tính", "Kỹ thuật máy tính"],
    "Khối ngành Luật": ["Luật dân sự", "Luật quốc tế"],  # Luật khác Luật kinh tế -> deny
    "Khối ngành Kỹ thuật": ["Kỹ thuật điện", "Kỹ thuật cơ khí", "Kỹ thuật xây dựng"],
}

# Trường công lập: CHỈ 4 trường này được chấp nhận khi loai_truong = "Công lập"
TRUONG_CONG_LAP_HOP_LE = [
    ("NEU", "Trường Công lập đào tạo trong nước"),
    ("FTU", "Trường Công lập đào tạo trong nước"),
    ("AOF", "Trường Công lập đào tạo trong nước"),
    ("BA", "Trường Công lập đào tạo trong nước"),
]
# Trường công lập KHÔNG nằm trong danh sách -> deny dù mọi thứ khác đều ổn
TRUONG_CONG_LAP_KHONG_HOP_LE = [
    ("Đại học Kinh tế - ĐHQGHN", "Trường Công lập đào tạo trong nước"),
    ("Đại học Bách Khoa Hà Nội", "Trường Công lập đào tạo trong nước"),
    ("Đại học Kinh tế TP.HCM", "Trường Công lập đào tạo trong nước"),
    ("Đại học Luật Hà Nội", "Trường Công lập đào tạo trong nước"),
]
# Trường dân lập: KHÔNG bị áp rule "4 trường công lập" (rule chỉ check khi
# loai_truong chứa đúng "Công lập đào tạo trong nước")
TRUONG_DAN_LAP = [
    ("Đại học Thương mại", "Trường Dân lập đào tạo trong nước"),
    ("Đại học FPT", "Trường Dân lập đào tạo trong nước"),
    ("Đại học Hoa Sen", "Trường Dân lập đào tạo trong nước"),
    ("Đại học Văn Lang", "Trường Dân lập đào tạo trong nước"),
    ("Đại học Duy Tân", "Trường Dân lập đào tạo trong nước"),
]
TRUONG_NUOC_NGOAI = [
    ("National University of Singapore", "Trường nước ngoài"),
    ("University of Melbourne", "Trường nước ngoài"),
    ("University of Auckland", "Trường nước ngoài"),
    ("Yonsei University (Hàn Quốc)", "Trường quốc tế"),
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
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def hash_pw(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def get_existing_emails():
    """Lấy email đã tồn tại trong DB để tránh trùng khi insert thêm."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT email FROM ung_vien")
    existing = {r[0] for r in cur.fetchall()}
    conn.close()
    return existing


def build_profiles(n, used_emails, start_idx=1000):
    """
    used_emails: set email đã có trong DB (để tránh đụng email cũ).
    start_idx: offset để slug email không trùng với 35 hồ sơ cũ (vốn dùng
               index 1..35), tránh kiểu "minh.nguyen5@gmail.com" bị lặp ý
               tưởng dù về mặt kỹ thuật vẫn check trùng email rồi.
    """
    profiles = []

    # ── Phân bổ scenario CHẶT để đảm bảo đủ cả 4 trạng thái trong 120 hồ sơ ──
    # phong_van ~15%, approve ~40%, deny ~30%, cho_duyet(recheck) ~15%
    scenario_pool = (
        ["phong_van"] * 18 +
        ["approve"] * 48 +
        ["deny"] * 36 +
        ["recheck"] * 18
    )
    while len(scenario_pool) < n:
        scenario_pool.append(random.choice(["phong_van", "approve", "deny", "recheck"]))
    scenario_pool = scenario_pool[:n]
    random.shuffle(scenario_pool)

    for i, scenario in enumerate(scenario_pool, start=start_idx):
        is_nam = random.random() < 0.55
        if is_nam:
            ho = random.choice(HO_NAM)
            ten = random.choice(TEN_NAM)
            gioi_tinh = "Nam"
        else:
            ho = random.choice(HO_NU)
            ten = random.choice(TEN_NU)
            gioi_tinh = "Nữ"

        ten_slug = remove_accents(ten).lower().replace(" ", "")
        ho_slug = remove_accents(ho.split()[-1]).lower().replace(" ", "")
        base_email = f"{ten_slug}.{ho_slug}{i}@gmail.com"
        while base_email in used_emails:
            base_email = f"{ten_slug}.{ho_slug}{i}{random.randint(100,999)}@gmail.com"
        used_emails.add(base_email)

        # ── Ngày sinh ──
        if scenario == "deny" and random.random() < 0.25:
            dob = random_date(1985, 1994)  # quá tuổi
        else:
            dob = random_date(1997, 2004)  # <=30 tuổi tính tới 2026

        tinh = random.choice(TINH_THANH)
        quan = random.choice(QUAN_HUYEN[tinh])
        dia_chi = f"Số {random.randint(1,200)} {random.choice(DUONG)}"

        sdt = "09" + "".join(str(random.randint(0, 9)) for _ in range(8))
        sdt_khac = "03" + "".join(str(random.randint(0, 9)) for _ in range(8))
        cccd = "".join(str(random.randint(0, 9)) for _ in range(12))
        ngay_cap_cccd = fmt(random_date(2018, 2024))

        chieu_cao = str(random.randint(155, 182))
        can_nang = str(random.randint(48, 80))
        hon_nhan = random.choices(["Độc thân", "Đã kết hôn", "Khác"], weights=[80, 18, 2])[0]

        thanh_tich_options = [
            "", "Sinh viên 5 tốt cấp trường", "Học bổng khuyến học 3 năm liên tiếp",
            "Giải Ba Olympic Tin học sinh viên", "Thành viên CLB Nghiên cứu khoa học",
            "Đại diện sinh viên trao đổi tại Singapore", "Thủ khoa đầu vào",
        ]
        thanh_tich = random.choice(thanh_tich_options)

        # ── Trình độ chuyên môn — phụ thuộc scenario ──
        if scenario == "deny":
            # Trộn các kiểu lỗi để đa dạng nguyên nhân deny:
            # 1) Cao đẳng | 2) nhóm ngành không phù hợp | 3) trường công lập
            # không trong danh sách | 4) điểm thấp | 5) không chính quy
            deny_type = random.choice([
                "cao_dang", "nhom_sai", "truong_cong_lap_sai",
                "diem_thap", "khong_chinh_quy",
            ])
        else:
            deny_type = None

        if deny_type == "cao_dang":
            trinh_do = "Cao đẳng"
            nhom = random.choice(list(NHOM_NGANH_OK.keys()))
            chuyen_nganh = random.choice(NHOM_NGANH_OK[nhom])
            ten_truong, loai_truong = random.choice(TRUONG_CONG_LAP_HOP_LE + TRUONG_DAN_LAP)
        elif deny_type == "nhom_sai":
            trinh_do = random.choices(["Đại học", "Thạc sĩ"], weights=[85, 15])[0]
            nhom = random.choice(list(NHOM_NGANH_KHONG_OK.keys()))
            chuyen_nganh = random.choice(NHOM_NGANH_KHONG_OK[nhom])
            ten_truong, loai_truong = random.choice(TRUONG_CONG_LAP_HOP_LE + TRUONG_DAN_LAP)
        elif deny_type == "truong_cong_lap_sai":
            trinh_do = random.choices(["Đại học", "Thạc sĩ"], weights=[85, 15])[0]
            nhom = random.choice(list(NHOM_NGANH_OK.keys()))
            chuyen_nganh = random.choice(NHOM_NGANH_OK[nhom])
            ten_truong, loai_truong = random.choice(TRUONG_CONG_LAP_KHONG_HOP_LE)
        else:
            # approve / phong_van / recheck / deny(diem_thap|khong_chinh_quy):
            # PHẢI dùng nhóm ngành + trường HỢP LỆ, để lý do deny (nếu có)
            # chỉ đến từ đúng 1 nguyên nhân được chỉ định (điểm hoặc loại hình).
            trinh_do = random.choices(["Đại học", "Thạc sĩ", "Tiến sĩ"], weights=[75, 20, 5])[0]
            nhom = random.choice(list(NHOM_NGANH_OK.keys()))
            chuyen_nganh = random.choice(NHOM_NGANH_OK[nhom])
            if scenario == "recheck":
                ten_truong, loai_truong = random.choice(TRUONG_NUOC_NGOAI)
            else:
                ten_truong, loai_truong = random.choice(TRUONG_CONG_LAP_HOP_LE + TRUONG_DAN_LAP)

        van_bang = random.choice(VAN_BANG)

        quoc_gia_hs = "Nước ngoài" if scenario == "recheck" else "Việt Nam"
        if scenario == "recheck":
            quoc_gia_cm = "Nước ngoài"
        else:
            quoc_gia_cm = "Việt Nam"

        nam_bat_dau = dob.year + random.randint(18, 19)
        so_nam_hoc = 1 if trinh_do == "Thạc sĩ" else (3 if trinh_do == "Tiến sĩ" else random.choice([4, 4, 5]))
        ngay_bat_dau = fmt(date(nam_bat_dau, random.choice([8, 9]), random.randint(1, 28)))

        if scenario == "phong_van":
            # Phải tốt nghiệp trong vòng 1 năm tính đến 29/06/2026
            # -> ngay_ket_thuc nằm trong [29/06/2025, 29/06/2026]
            grad_date = date(2025, 7, 1) + timedelta(days=random.randint(0, 360))
            ngay_ket_thuc = fmt(grad_date)
        else:
            ngay_ket_thuc = fmt(date(nam_bat_dau + so_nam_hoc, random.choice([6, 7]), random.randint(1, 28)))

        if deny_type == "khong_chinh_quy":
            loai_hinh = random.choice(["Tại chức", "Liên thông"])
        else:
            loai_hinh = "Chính quy"

        thang_diem = "/10"
        if deny_type == "diem_thap":
            diem_tong_ket = str(round(random.uniform(4.0, 6.0), 1))
        elif scenario == "phong_van":
            diem_tong_ket = str(round(random.uniform(9.0, 9.9), 1))  # phải Xuất sắc
        else:
            diem_tong_ket = str(round(random.uniform(6.6, 9.8), 1))

        dtk_float = float(diem_tong_ket)
        if dtk_float >= 9.0:
            xep_loai = "Xuất sắc"
        elif dtk_float >= 8.0:
            xep_loai = "Giỏi"
        elif dtk_float >= 6.5:
            xep_loai = "Khá"
        else:
            xep_loai = "Trung bình"

        # Ép xep_loai đúng yêu cầu cho scenario "phong_van" (đã set điểm >=9
        # nên xep_loai luôn ra "Xuất sắc" tự nhiên, nhưng double-check):
        if scenario == "phong_van":
            xep_loai = "Xuất sắc"

        hoc_ham = random.choices(HOC_HAM, weights=[85, 15])[0]

        # ── Ngoại ngữ — scenario "phong_van" PHẢI có chứng chỉ vượt ngưỡng ──
        if scenario == "phong_van":
            ngon_ngu = "Tiếng Anh"
            chung_chi = random.choice(["IELTS", "TOEIC", "TOEFL"])
            if chung_chi == "IELTS":
                diem_nn = str(round(random.uniform(7.5, 9.0), 1))  # > 7.0
            elif chung_chi == "TOEIC":
                diem_nn = str(random.randint(800, 990))  # > 785
            else:  # TOEFL
                diem_nn = str(random.randint(560, 600))  # > 550
        else:
            ngon_ngu, chung_chi = random.choice(NGOAI_NGU_CHOICES)
            if chung_chi == "IELTS":
                diem_nn = str(round(random.uniform(5.0, 7.0), 1))  # dưới hoặc bằng ngưỡng
            elif chung_chi == "TOEIC":
                diem_nn = str(random.randint(500, 785))
            elif chung_chi == "TOEFL":
                diem_nn = str(random.randint(70, 550))
            elif chung_chi == "Hsk":
                diem_nn = str(random.randint(3, 6))
            else:  # JLPT
                diem_nn = random.choice(["N1", "N2", "N3"])

        # ── trang_thai lưu DB — tính bằng đúng compute_status mới ──
        ho_so_tam = {"ngay_sinh": fmt(dob)}
        cm_tam = [{
            "trinh_do": trinh_do,
            "loai_hinh_dao_tao": loai_hinh,
            "diem_tong_ket": diem_tong_ket,
            "thang_diem": thang_diem,
            "quoc_gia": quoc_gia_cm,
            "loai_truong": loai_truong,
            "ten_truong": ten_truong,
            "nhom_chuyen_nganh": nhom,
            "chuyen_nganh": chuyen_nganh,
            "xep_loai": xep_loai,
            "ngay_ket_thuc": ngay_ket_thuc,
        }]
        nn_tam = [{"chung_chi": chung_chi, "diem": diem_nn}]
        computed = compute_status(ho_so_tam, cm_tam, nn_tam)

        if computed == "cho_duyet":
            # truthy-string bug: phải để None để bulk_save/nút duyệt hoạt động
            trang_thai = None
        else:
            trang_thai = computed

        ocr_status = "APPROVE" if computed in ("approve", "phong_van", "cho_duyet") else "REJECT"

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
            "_scenario": scenario,
            "_computed": computed,
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


def seed_extra(n=120):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    used_emails = get_existing_emails()
    profiles = build_profiles(n, used_emails, start_idx=1000)

    # Thời điểm nộp: đợt tuyển thứ 2, sau đợt cũ — trải dài ~5 tuần,
    # dồn nhiều hơn về cuối, giờ nộp rải trong ngày làm việc.
    dot_tuyen_start = date(2026, 6, 1)
    dot_tuyen_days = 35

    nop_luc_list = []
    for idx in range(len(profiles)):
        progress = idx / max(len(profiles) - 1, 1)
        day_offset = int((progress ** 0.6) * dot_tuyen_days)
        day_offset = max(0, min(dot_tuyen_days, day_offset + random.randint(-2, 2)))
        nop_date = dot_tuyen_start + timedelta(days=day_offset)
        hour = random.randint(8, 22)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        nop_luc_list.append(datetime(nop_date.year, nop_date.month, nop_date.day, hour, minute, second))
    nop_luc_list.sort()

    for idx, p in enumerate(profiles):
        pw_hash = hash_pw(p["password"])
        tao_luc = nop_luc_list[idx] - timedelta(minutes=random.randint(2, 45))
        cur.execute(
            "INSERT INTO ung_vien (email, mat_khau_hash, tao_luc) VALUES (?, ?, ?)",
            (p["email"], pw_hash, tao_luc.strftime("%Y-%m-%d %H:%M:%S"))
        )
        ung_vien_id = cur.lastrowid

        nop_luc = nop_luc_list[idx]
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

        nn = p["ngoai_ngu"]
        cur.execute("""
            INSERT INTO trinh_do_ngoai_ngu (ho_so_id, ngon_ngu, chung_chi, diem)
            VALUES (?,?,?,?)
        """, (ho_so_id, nn["ngon_ngu"], nn["chung_chi"], nn["diem"]))

    conn.commit()

    print("=== KẾT QUẢ THÊM DATA ===")
    cur.execute("SELECT COUNT(*) FROM ho_so")
    print(f"Tổng ho_so hiện tại trong DB: {cur.fetchone()[0]}")

    from collections import Counter
    print("\nPhân bố computed_status của 120 hồ sơ MỚI thêm:")
    print(Counter(p["_computed"] for p in profiles))

    print("\nPhân bố trang_thai (giá trị lưu DB) của 120 hồ sơ MỚI thêm:")
    print(Counter(p["trang_thai"] for p in profiles))

    conn.close()


if __name__ == "__main__":
    seed_extra(120)