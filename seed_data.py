"""
seed_data.py — Xoá dữ liệu test cũ và nạp 35 hồ sơ ứng viên mẫu
Chạy: python3 seed_data.py
"""
import sqlite3, hashlib, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_hr.db")

# ─────────────────────────────────────────────────────────────────────
# DỮ LIỆU MẪU
# Cấu trúc mỗi ứng viên:
#   profile   → ho_so
#   edu       → trinh_do_chuyen_mon  (1 bản ghi)
#   lang      → trinh_do_ngoai_ngu   (1 bản ghi)
# ─────────────────────────────────────────────────────────────────────
CANDIDATES = [
    # ── 1 ──────────────────────────────────────────────────────────────
    dict(
        email="nguyen.thi.lan@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Thị", ten="Lan", gioi_tinh="Nữ",
            ngay_sinh="15/03/1998", noi_sinh="Hà Nội",
            dia_chi="12 Đường Trần Duy Hưng", quan_huyen="Cầu Giấy",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0912345601", cccd="001198003456",
            ngay_cap_cccd="10/06/2018", chieu_cao="162", can_nang="52",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên giỏi 4 năm liên tiếp, học bổng khuyến khích học tập",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế Quốc dân (NEU)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.5", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="7.0"),
    ),
    # ── 2 ──────────────────────────────────────────────────────────────
    dict(
        email="tran.van.minh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Trần Văn", ten="Minh", gioi_tinh="Nam",
            ngay_sinh="22/07/1997", noi_sinh="TP. Hồ Chí Minh",
            dia_chi="45 Nguyễn Thị Minh Khai", quan_huyen="Quận 3",
            tinh_thanh_pho="TP. Hồ Chí Minh", quoc_gia="Việt Nam",
            so_dien_thoai="0987654321", cccd="079197005678",
            ngay_cap_cccd="15/08/2017", chieu_cao="175", can_nang="68",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Top 5 sinh viên xuất sắc toàn trường năm 2021",
        ),
        edu=dict(
            trinh_do="Thạc sĩ", van_bang="Thạc sĩ",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Quản trị Kinh doanh",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế TP.HCM (UEH)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.8", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2019", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="850"),
    ),
    # ── 3 ──────────────────────────────────────────────────────────────
    dict(
        email="le.thi.hoa@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Lê Thị", ten="Hoa", gioi_tinh="Nữ",
            ngay_sinh="08/11/1999", noi_sinh="Đà Nẵng",
            dia_chi="23 Lê Duẩn", quan_huyen="Hải Châu",
            tinh_thanh_pho="Đà Nẵng", quoc_gia="Việt Nam",
            so_dien_thoai="0905112233", cccd="048199007891",
            ngay_cap_cccd="05/01/2019", chieu_cao="158", can_nang="48",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Giải nhì cuộc thi Sinh viên nghiên cứu khoa học cấp trường",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Đà Nẵng – Trường Kinh tế",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="7.8", xep_loai="Khá",
            ngay_bat_dau="01/09/2017", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="720"),
    ),
    # ── 4 ──────────────────────────────────────────────────────────────
    dict(
        email="pham.duc.long@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Phạm Đức", ten="Long", gioi_tinh="Nam",
            ngay_sinh="30/04/1996", noi_sinh="Hải Phòng",
            dia_chi="78 Lạch Tray", quan_huyen="Ngô Quyền",
            tinh_thanh_pho="Hải Phòng", quoc_gia="Việt Nam",
            so_dien_thoai="0934567890", cccd="031196009012",
            ngay_cap_cccd="20/05/2016", chieu_cao="178", can_nang="72",
            tinh_trang_hon_nhan="Đã kết hôn",
            thanh_tich_noi_bat="CFA Level 1, kinh nghiệm 3 năm tại ngân hàng BIDV",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Học viện Tài chính",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="7.5", xep_loai="Khá",
            ngay_bat_dau="01/09/2014", ngay_ket_thuc="30/06/2018",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="6.5"),
    ),
    # ── 5 ──────────────────────────────────────────────────────────────
    dict(
        email="hoang.thi.thu@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Hoàng Thị", ten="Thu", gioi_tinh="Nữ",
            ngay_sinh="14/09/2000", noi_sinh="Hà Nội",
            dia_chi="5 Phố Huế", quan_huyen="Hai Bà Trưng",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0978234567", cccd="001200011234",
            ngay_cap_cccd="01/10/2020", chieu_cao="160", can_nang="50",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên xuất sắc, giải ba Olympic Toán sinh viên toàn quốc",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Học viện Ngân hàng",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="9.1", xep_loai="Xuất sắc",
            ngay_bat_dau="01/09/2018", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="7.5"),
    ),
    # ── 6 ──────────────────────────────────────────────────────────────
    dict(
        email="nguyen.van.duc@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Văn", ten="Đức", gioi_tinh="Nam",
            ngay_sinh="25/12/1998", noi_sinh="Nghệ An",
            dia_chi="102 Lê Lợi", quan_huyen="Vinh",
            tinh_thanh_pho="Nghệ An", quoc_gia="Việt Nam",
            so_dien_thoai="0963456789", cccd="038198013456",
            ngay_cap_cccd="10/01/2018", chieu_cao="172", can_nang="65",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Thủ khoa đầu vào ĐH Ngoại thương, học bổng toàn phần 4 năm",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kinh tế Quốc tế",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Ngoại thương (FTU)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="9.3", xep_loai="Xuất sắc",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="8.0"),
    ),
    # ── 7 ──────────────────────────────────────────────────────────────
    dict(
        email="bui.thi.mai@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Bùi Thị", ten="Mai", gioi_tinh="Nữ",
            ngay_sinh="03/06/1997", noi_sinh="Cần Thơ",
            dia_chi="88 Nguyễn Trãi", quan_huyen="Ninh Kiều",
            tinh_thanh_pho="Cần Thơ", quoc_gia="Việt Nam",
            so_dien_thoai="0916789012", cccd="065197015678",
            ngay_cap_cccd="20/07/2017", chieu_cao="156", can_nang="46",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Đạt chứng chỉ ACCA Part 1, kinh nghiệm thực tập Big4",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Cần Thơ",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.2", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2015", ngay_ket_thuc="30/06/2019",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="780"),
    ),
    # ── 8 ── DENY: cao đẳng ────────────────────────────────────────────
    dict(
        email="do.van.thanh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Đỗ Văn", ten="Thành", gioi_tinh="Nam",
            ngay_sinh="11/02/2001", noi_sinh="Thái Bình",
            dia_chi="31 Lý Thường Kiệt", quan_huyen="Thái Bình",
            tinh_thanh_pho="Thái Bình", quoc_gia="Việt Nam",
            so_dien_thoai="0941234567", cccd="034201017890",
            ngay_cap_cccd="05/03/2021", chieu_cao="168", can_nang="60",
            tinh_trang_hon_nhan="Độc thân", thanh_tich_noi_bat="",
        ),
        edu=dict(
            trinh_do="Cao đẳng", van_bang="Bằng Cao đẳng",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Cao đẳng Kinh tế Kỹ thuật Thái Bình",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.0", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2019", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="500"),
    ),
    # ── 9 ──────────────────────────────────────────────────────────────
    dict(
        email="vo.thi.kim.anh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Võ Thị Kim", ten="Anh", gioi_tinh="Nữ",
            ngay_sinh="19/08/1999", noi_sinh="Bình Dương",
            dia_chi="156 Đại lộ Bình Dương", quan_huyen="Thủ Dầu Một",
            tinh_thanh_pho="Bình Dương", quoc_gia="Việt Nam",
            so_dien_thoai="0852345678", cccd="074199019012",
            ngay_cap_cccd="01/09/2019", chieu_cao="163", can_nang="53",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Học bổng IEU 4 năm, tình nguyện viên Hội chợ Tài chính 2022",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Dân lập đào tạo trong nước",
            ten_truong="Đại học Quốc tế (IEU) – ĐH Quốc gia TP.HCM",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.7", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2017", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="7.0"),
    ),
    # ── 10 ─────────────────────────────────────────────────────────────
    dict(
        email="dang.quoc.huy@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Đặng Quốc", ten="Huy", gioi_tinh="Nam",
            ngay_sinh="05/01/1998", noi_sinh="Hà Nội",
            dia_chi="99 Xuân Thủy", quan_huyen="Cầu Giấy",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0903456789", cccd="001198021234",
            ngay_cap_cccd="10/02/2018", chieu_cao="176", can_nang="70",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Giải nhất cuộc thi lập kế hoạch kinh doanh cấp quốc gia",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Quản trị Kinh doanh",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Quốc gia Hà Nội – Trường Kinh tế (VNU-UEB)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.0", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="860"),
    ),
    # ── 11 ── DENY: điểm thấp (/10 = 5.8) ─────────────────────────────
    dict(
        email="cao.thi.ngoc@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Cao Thị", ten="Ngọc", gioi_tinh="Nữ",
            ngay_sinh="17/05/2000", noi_sinh="Nam Định",
            dia_chi="44 Trần Hưng Đạo", quan_huyen="Nam Định",
            tinh_thanh_pho="Nam Định", quoc_gia="Việt Nam",
            so_dien_thoai="0975678901", cccd="036200023456",
            ngay_cap_cccd="01/06/2020", chieu_cao="157", can_nang="47",
            tinh_trang_hon_nhan="Độc thân", thanh_tich_noi_bat="",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Nam Định",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="5.8", xep_loai="Trung bình",
            ngay_bat_dau="01/09/2018", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="450"),
    ),
    # ── 12 ─────────────────────────────────────────────────────────────
    dict(
        email="truong.van.nam@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Trương Văn", ten="Nam", gioi_tinh="Nam",
            ngay_sinh="28/10/1997", noi_sinh="Khánh Hòa",
            dia_chi="67 Nguyễn Thị Minh Khai", quan_huyen="Nha Trang",
            tinh_thanh_pho="Khánh Hòa", quoc_gia="Việt Nam",
            so_dien_thoai="0918901234", cccd="056197025678",
            ngay_cap_cccd="05/11/2017", chieu_cao="174", can_nang="67",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên giỏi, thực tập sinh xuất sắc tại Agribank",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Nha Trang",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="7.6", xep_loai="Khá",
            ngay_bat_dau="01/09/2015", ngay_ket_thuc="30/06/2019",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="700"),
    ),
    # ── 13 ── CHỜ DUYỆT: trường nước ngoài ────────────────────────────
    dict(
        email="phan.thi.bich@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Phan Thị", ten="Bích", gioi_tinh="Nữ",
            ngay_sinh="09/03/1999", noi_sinh="Hà Nội",
            dia_chi="18 Phan Bội Châu", quan_huyen="Hoàn Kiếm",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0901234567", cccd="001199027890",
            ngay_cap_cccd="15/04/2019", chieu_cao="165", can_nang="54",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Học bổng toàn phần Chính phủ Úc (Endeavour), GPA 3.8/4.0",
        ),
        edu=dict(
            trinh_do="Thạc sĩ", van_bang="Thạc sĩ",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Finance & Banking",
            quoc_gia="Nước ngoài", loai_truong="Trường nước ngoài",
            ten_truong="University of Melbourne",
            loai_hinh_dao_tao="Chính quy", thang_diem="/4",
            diem_tong_ket="3.8", xep_loai="Distinction",
            ngay_bat_dau="01/02/2021", ngay_ket_thuc="30/11/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="8.5"),
    ),
    # ── 14 ─────────────────────────────────────────────────────────────
    dict(
        email="nguyen.duc.anh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Đức", ten="Anh", gioi_tinh="Nam",
            ngay_sinh="16/07/1998", noi_sinh="Bắc Ninh",
            dia_chi="55 Lý Thái Tổ", quan_huyen="Bắc Ninh",
            tinh_thanh_pho="Bắc Ninh", quoc_gia="Việt Nam",
            so_dien_thoai="0939012345", cccd="022198029012",
            ngay_cap_cccd="20/08/2018", chieu_cao="177", can_nang="73",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Top 10 sinh viên tiêu biểu ĐHQGHN, giải nhì Olympic Kinh tế",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Quốc gia Hà Nội – Trường Kinh tế (VNU-UEB)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.9", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="7.5"),
    ),
    # ── 15 ─────────────────────────────────────────────────────────────
    dict(
        email="ly.thi.phuong@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Lý Thị", ten="Phương", gioi_tinh="Nữ",
            ngay_sinh="02/04/2000", noi_sinh="Hồ Chí Minh",
            dia_chi="200 Hoàng Văn Thụ", quan_huyen="Phú Nhuận",
            tinh_thanh_pho="TP. Hồ Chí Minh", quoc_gia="Việt Nam",
            so_dien_thoai="0852678901", cccd="079200031234",
            ngay_cap_cccd="10/05/2020", chieu_cao="161", can_nang="49",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên xuất sắc UEH, giải nhất Cuộc thi Marketing quốc gia",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Marketing",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế TP.HCM (UEH)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.6", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2018", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="810"),
    ),
    # ── 16 ── DENY: loại hình tại chức ────────────────────────────────
    dict(
        email="mai.van.hieu@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Mai Văn", ten="Hiếu", gioi_tinh="Nam",
            ngay_sinh="14/06/1993", noi_sinh="Thanh Hóa",
            dia_chi="12 Phan Chu Trinh", quan_huyen="Thanh Hóa",
            tinh_thanh_pho="Thanh Hóa", quoc_gia="Việt Nam",
            so_dien_thoai="0962345678", cccd="038193033456",
            ngay_cap_cccd="15/07/2013", chieu_cao="170", can_nang="64",
            tinh_trang_hon_nhan="Đã kết hôn", thanh_tich_noi_bat="",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Hồng Đức",
            loai_hinh_dao_tao="Tại chức", thang_diem="/10",
            diem_tong_ket="7.2", xep_loai="Khá",
            ngay_bat_dau="01/09/2014", ngay_ket_thuc="30/06/2018",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="450"),
    ),
    # ── 17 ─────────────────────────────────────────────────────────────
    dict(
        email="tran.thi.thu.ha@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Trần Thị Thu", ten="Hà", gioi_tinh="Nữ",
            ngay_sinh="20/11/1998", noi_sinh="Quảng Ninh",
            dia_chi="88 Trần Phú", quan_huyen="Hạ Long",
            tinh_thanh_pho="Quảng Ninh", quoc_gia="Việt Nam",
            so_dien_thoai="0904567890", cccd="022198035678",
            ngay_cap_cccd="25/12/2018", chieu_cao="164", can_nang="53",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên giỏi NEU, CLB Ngân hàng & Đầu tư",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế Quốc dân (NEU)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.1", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="740"),
    ),
    # ── 18 ─────────────────────────────────────────────────────────────
    dict(
        email="le.hoang.son@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Lê Hoàng", ten="Sơn", gioi_tinh="Nam",
            ngay_sinh="07/02/1999", noi_sinh="Hà Nội",
            dia_chi="34 Kim Mã", quan_huyen="Ba Đình",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0973456789", cccd="001199037890",
            ngay_cap_cccd="15/03/2019", chieu_cao="179", can_nang="74",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Thủ khoa tốt nghiệp ĐHNT, học bổng VietinBank",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kinh tế Quốc tế",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Ngoại thương (FTU)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="9.0", xep_loai="Xuất sắc",
            ngay_bat_dau="01/09/2017", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="8.0"),
    ),
    # ── 19 ── CHỜ DUYỆT: quốc gia nước ngoài ──────────────────────────
    dict(
        email="nguyen.bao.chau@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Bảo", ten="Châu", gioi_tinh="Nữ",
            ngay_sinh="12/09/1997", noi_sinh="Hà Nội",
            dia_chi="77 Trần Phú", quan_huyen="Hà Đông",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0931234567", cccd="001197039012",
            ngay_cap_cccd="20/10/2017", chieu_cao="167", can_nang="56",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Học bổng MEXT Nhật Bản, GPA 3.9/4.0",
        ),
        edu=dict(
            trinh_do="Thạc sĩ", van_bang="Thạc sĩ",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Financial Economics",
            quoc_gia="Nước ngoài", loai_truong="Trường nước ngoài",
            ten_truong="Keio University",
            loai_hinh_dao_tao="Chính quy", thang_diem="/4",
            diem_tong_ket="3.9", xep_loai="Summa Cum Laude",
            ngay_bat_dau="01/04/2020", ngay_ket_thuc="31/03/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Nhật", chung_chi="JLPT", diem="N1"),
    ),
    # ── 20 ─────────────────────────────────────────────────────────────
    dict(
        email="pham.thi.quynh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Phạm Thị", ten="Quỳnh", gioi_tinh="Nữ",
            ngay_sinh="25/01/2000", noi_sinh="Hồ Chí Minh",
            dia_chi="120 Điện Biên Phủ", quan_huyen="Bình Thạnh",
            tinh_thanh_pho="TP. Hồ Chí Minh", quoc_gia="Việt Nam",
            so_dien_thoai="0867890123", cccd="079200041234",
            ngay_cap_cccd="01/02/2020", chieu_cao="162", can_nang="51",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Giải nhất FTU Business Challenge 2022, CFA Level 1",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Ngoại thương – Cơ sở II (FTU2)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.9", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2018", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="7.5"),
    ),
    # ── 21 ─────────────────────────────────────────────────────────────
    dict(
        email="vu.van.khanh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Vũ Văn", ten="Khánh", gioi_tinh="Nam",
            ngay_sinh="18/06/1996", noi_sinh="Hà Nội",
            dia_chi="25 Nguyễn Chí Thanh", quan_huyen="Đống Đa",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0945678901", cccd="001196043456",
            ngay_cap_cccd="25/07/2016", chieu_cao="174", can_nang="69",
            tinh_trang_hon_nhan="Đã kết hôn",
            thanh_tich_noi_bat="Kinh nghiệm 4 năm ngân hàng Techcombank, CPA Việt Nam",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Học viện Tài chính",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="7.9", xep_loai="Khá",
            ngay_bat_dau="01/09/2014", ngay_ket_thuc="30/06/2018",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="730"),
    ),
    # ── 22 ─────────────────────────────────────────────────────────────
    dict(
        email="dinh.thi.ngoc.han@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Đinh Thị Ngọc", ten="Hân", gioi_tinh="Nữ",
            ngay_sinh="03/12/1999", noi_sinh="Đà Lạt",
            dia_chi="45 Trần Phú", quan_huyen="Đà Lạt",
            tinh_thanh_pho="Lâm Đồng", quoc_gia="Việt Nam",
            so_dien_thoai="0906789012", cccd="068199045678",
            ngay_cap_cccd="10/01/2020", chieu_cao="159", can_nang="48",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên xuất sắc, tình nguyện viên SEA Games 31",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Đà Lạt",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.3", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2017", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="695"),
    ),
    # ── 23 ── DENY: quá tuổi (sinh 1992) ──────────────────────────────
    dict(
        email="ngo.thanh.tung@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Ngô Thanh", ten="Tùng", gioi_tinh="Nam",
            ngay_sinh="10/03/1992", noi_sinh="Hà Nội",
            dia_chi="14 Đội Cấn", quan_huyen="Ba Đình",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0907890123", cccd="001192047890",
            ngay_cap_cccd="15/04/2012", chieu_cao="173", can_nang="70",
            tinh_trang_hon_nhan="Đã kết hôn", thanh_tich_noi_bat="",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế Quốc dân (NEU)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="7.5", xep_loai="Khá",
            ngay_bat_dau="01/09/2010", ngay_ket_thuc="30/06/2014",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="600"),
    ),
    # ── 24 ─────────────────────────────────────────────────────────────
    dict(
        email="nguyen.thi.thanh.mai@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Thị Thanh", ten="Mai", gioi_tinh="Nữ",
            ngay_sinh="29/08/2001", noi_sinh="Hưng Yên",
            dia_chi="23 Phố Hiến", quan_huyen="Hưng Yên",
            tinh_thanh_pho="Hưng Yên", quoc_gia="Việt Nam",
            so_dien_thoai="0871234567", cccd="033201049012",
            ngay_cap_cccd="05/09/2021", chieu_cao="161", can_nang="50",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên giỏi, giải nhì Nghiên cứu khoa học cấp tỉnh",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Học viện Ngân hàng",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.4", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2019", ngay_ket_thuc="30/06/2023",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="760"),
    ),
    # ── 25 ─────────────────────────────────────────────────────────────
    dict(
        email="ha.minh.quan@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Hà Minh", ten="Quân", gioi_tinh="Nam",
            ngay_sinh="04/05/1999", noi_sinh="Hồ Chí Minh",
            dia_chi="78 Cách Mạng Tháng Tám", quan_huyen="Quận 3",
            tinh_thanh_pho="TP. Hồ Chí Minh", quoc_gia="Việt Nam",
            so_dien_thoai="0956789012", cccd="079199051234",
            ngay_cap_cccd="15/06/2019", chieu_cao="176", can_nang="71",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Top 3 sinh viên giỏi UEH, chứng chỉ Bloomberg Market Concepts",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế TP.HCM (UEH)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.7", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2017", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="7.0"),
    ),
    # ── 26 ─────────────────────────────────────────────────────────────
    dict(
        email="trinh.xuan.bach@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Trịnh Xuân", ten="Bách", gioi_tinh="Nam",
            ngay_sinh="21/10/1997", noi_sinh="Hà Tĩnh",
            dia_chi="56 Nguyễn Du", quan_huyen="Hà Tĩnh",
            tinh_thanh_pho="Hà Tĩnh", quoc_gia="Việt Nam",
            so_dien_thoai="0921345678", cccd="042197053456",
            ngay_cap_cccd="30/11/2017", chieu_cao="175", can_nang="68",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Thủ khoa đầu ra ĐH Vinh, Bí thư Đoàn khoa Kinh tế",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Vinh",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.8", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2015", ngay_ket_thuc="30/06/2019",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="750"),
    ),
    # ── 27 ─────────────────────────────────────────────────────────────
    dict(
        email="tong.thi.huong@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Tống Thị", ten="Hương", gioi_tinh="Nữ",
            ngay_sinh="13/04/2001", noi_sinh="Vĩnh Phúc",
            dia_chi="90 Mê Linh", quan_huyen="Phúc Yên",
            tinh_thanh_pho="Vĩnh Phúc", quoc_gia="Việt Nam",
            so_dien_thoai="0882345678", cccd="026201055678",
            ngay_cap_cccd="20/05/2021", chieu_cao="160", can_nang="49",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên 5 tốt cấp trung ương, tình nguyện viên quốc tế",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Học viện Ngân hàng",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.5", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2019", ngay_ket_thuc="30/06/2023",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="790"),
    ),
    # ── 28 ── DENY: điểm thấp (/4 = 1.9) ──────────────────────────────
    dict(
        email="lam.van.cuong@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Lâm Văn", ten="Cường", gioi_tinh="Nam",
            ngay_sinh="09/07/2000", noi_sinh="An Giang",
            dia_chi="11 Long Xuyên", quan_huyen="Long Xuyên",
            tinh_thanh_pho="An Giang", quoc_gia="Việt Nam",
            so_dien_thoai="0967890123", cccd="089200057890",
            ngay_cap_cccd="15/08/2020", chieu_cao="170", can_nang="62",
            tinh_trang_hon_nhan="Độc thân", thanh_tich_noi_bat="",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học An Giang",
            loai_hinh_dao_tao="Chính quy", thang_diem="/4",
            diem_tong_ket="1.9", xep_loai="Trung bình",
            ngay_bat_dau="01/09/2018", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="350"),
    ),
    # ── 29 ─────────────────────────────────────────────────────────────
    dict(
        email="nguyen.phuong.linh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Phương", ten="Linh", gioi_tinh="Nữ",
            ngay_sinh="16/02/1998", noi_sinh="Hà Nội",
            dia_chi="67 Láng Hạ", quan_huyen="Đống Đa",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0913456789", cccd="001198059012",
            ngay_cap_cccd="25/03/2018", chieu_cao="163", can_nang="51",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Học bổng Ngân hàng Nhà nước, giải nhất Olympiad Kinh tế FTU",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kinh tế Đối ngoại",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Ngoại thương (FTU)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="9.2", xep_loai="Xuất sắc",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="8.0"),
    ),
    # ── 30 ─────────────────────────────────────────────────────────────
    dict(
        email="doan.van.an@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Đoàn Văn", ten="An", gioi_tinh="Nam",
            ngay_sinh="23/11/2000", noi_sinh="Bình Định",
            dia_chi="45 Nguyễn Huệ", quan_huyen="Quy Nhơn",
            tinh_thanh_pho="Bình Định", quoc_gia="Việt Nam",
            so_dien_thoai="0981234567", cccd="052200061234",
            ngay_cap_cccd="30/12/2020", chieu_cao="172", can_nang="66",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên giỏi, quán quân Startup Weekend Quy Nhơn 2022",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Quản trị Kinh doanh",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Quy Nhơn",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.0", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2018", ngay_ket_thuc="30/06/2022",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="680"),
    ),
    # ── 31 ─────────────────────────────────────────────────────────────
    dict(
        email="vuong.thi.cam.tu@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Vương Thị Cẩm", ten="Tú", gioi_tinh="Nữ",
            ngay_sinh="07/08/1999", noi_sinh="Hồ Chí Minh",
            dia_chi="33 Sư Vạn Hạnh", quan_huyen="Quận 10",
            tinh_thanh_pho="TP. Hồ Chí Minh", quoc_gia="Việt Nam",
            so_dien_thoai="0852901234", cccd="079199063456",
            ngay_cap_cccd="15/09/2019", chieu_cao="164", can_nang="52",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Á khoa đầu vào UEH, sinh viên 5 tốt thành phố 2022",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế TP.HCM (UEH)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.7", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2017", ngay_ket_thuc="30/06/2021",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="820"),
    ),
    # ── 32 ─────────────────────────────────────────────────────────────
    dict(
        email="thai.van.toan@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Thái Văn", ten="Toàn", gioi_tinh="Nam",
            ngay_sinh="11/12/1998", noi_sinh="Huế",
            dia_chi="22 Lê Lợi", quan_huyen="Huế",
            tinh_thanh_pho="Thừa Thiên Huế", quoc_gia="Việt Nam",
            so_dien_thoai="0934901234", cccd="046198065678",
            ngay_cap_cccd="20/01/2019", chieu_cao="171", can_nang="64",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Sinh viên tiêu biểu ĐH Kinh tế Huế, giải nhì Olympic Kế toán",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Kế toán – Kiểm toán",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Kinh tế – ĐH Huế",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="8.4", xep_loai="Giỏi",
            ngay_bat_dau="01/09/2016", ngay_ket_thuc="30/06/2020",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="710"),
    ),
    # ── 33 ── CHỜ DUYỆT: trường nước ngoài ────────────────────────────
    dict(
        email="kim.thi.lan.anh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Kim Thị Lan", ten="Anh", gioi_tinh="Nữ",
            ngay_sinh="26/06/1998", noi_sinh="Hà Nội",
            dia_chi="40 Hai Bà Trưng", quan_huyen="Hoàn Kiếm",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0943456789", cccd="001198067890",
            ngay_cap_cccd="05/07/2018", chieu_cao="166", can_nang="55",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Học bổng Chính phủ Hàn Quốc (GKS), huy chương bạc ICPC châu Á",
        ),
        edu=dict(
            trinh_do="Thạc sĩ", van_bang="Thạc sĩ",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Financial Engineering",
            quoc_gia="Nước ngoài", loai_truong="Trường nước ngoài",
            ten_truong="KAIST (Korea Advanced Institute of Science and Technology)",
            loai_hinh_dao_tao="Chính quy", thang_diem="/4",
            diem_tong_ket="3.7", xep_loai="High Distinction",
            ngay_bat_dau="01/03/2021", ngay_ket_thuc="28/02/2023",
        ),
        lang=dict(ngon_ngu="Tiếng Hàn", chung_chi="TOPIK", diem="Level 5"),
    ),
    # ── 34 ─────────────────────────────────────────────────────────────
    dict(
        email="nguyen.manh.hung@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Nguyễn Mạnh", ten="Hùng", gioi_tinh="Nam",
            ngay_sinh="15/09/1996", noi_sinh="Vĩnh Long",
            dia_chi="33 Phạm Hùng", quan_huyen="Vĩnh Long",
            tinh_thanh_pho="Vĩnh Long", quoc_gia="Việt Nam",
            so_dien_thoai="0968901234", cccd="086196069012",
            ngay_cap_cccd="25/10/2016", chieu_cao="173", can_nang="67",
            tinh_trang_hon_nhan="Đã kết hôn",
            thanh_tich_noi_bat="Kinh nghiệm 5 năm tín dụng Agribank, chứng chỉ CRA",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Đại học Cần Thơ",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="7.8", xep_loai="Khá",
            ngay_bat_dau="01/09/2014", ngay_ket_thuc="30/06/2018",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="TOEIC", diem="650"),
    ),
    # ── 35 ─────────────────────────────────────────────────────────────
    dict(
        email="hoang.khanh.linh@gmail.com", password="Vietcombank@2024",
        profile=dict(
            ho_ten_dem="Hoàng Khánh", ten="Linh", gioi_tinh="Nữ",
            ngay_sinh="31/03/2000", noi_sinh="Hà Nội",
            dia_chi="10 Liễu Giai", quan_huyen="Ba Đình",
            tinh_thanh_pho="Hà Nội", quoc_gia="Việt Nam",
            so_dien_thoai="0902345678", cccd="001200071234",
            ngay_cap_cccd="10/04/2020", chieu_cao="162", can_nang="51",
            tinh_trang_hon_nhan="Độc thân",
            thanh_tich_noi_bat="Thủ khoa tốt nghiệp Học viện Ngân hàng 2023, học bổng VCB",
        ),
        edu=dict(
            trinh_do="Đại học", van_bang="Cử nhân",
            nhom_chuyen_nganh="Khối ngành Kinh tế - Quản lý",
            chuyen_nganh="Tài chính Ngân hàng",
            quoc_gia="Việt Nam", loai_truong="Trường Công lập đào tạo trong nước",
            ten_truong="Học viện Ngân hàng",
            loai_hinh_dao_tao="Chính quy", thang_diem="/10",
            diem_tong_ket="9.4", xep_loai="Xuất sắc",
            ngay_bat_dau="01/09/2019", ngay_ket_thuc="30/06/2023",
        ),
        lang=dict(ngon_ngu="Tiếng Anh", chung_chi="IELTS", diem="8.0"),
    ),
]


# ─────────────────────────────────────────────────────────────────────
# CHẠY SEED
# ─────────────────────────────────────────────────────────────────────
def seed():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Xoá dữ liệu cũ (thứ tự: child trước, parent sau)
    cur.execute("DELETE FROM trinh_do_ngoai_ngu")
    cur.execute("DELETE FROM trinh_do_chuyen_mon")
    cur.execute("DELETE FROM ho_so")
    cur.execute("DELETE FROM ung_vien")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN "
                "('ung_vien','ho_so','trinh_do_chuyen_mon','trinh_do_ngoai_ngu')")
    conn.commit()
    print(f"✅ Đã xoá dữ liệu cũ.")

    ok = 0
    for idx, c in enumerate(CANDIDATES, 1):
        pw_hash = hashlib.sha256(c["password"].encode()).hexdigest()

        # ung_vien
        cur.execute(
            "INSERT INTO ung_vien (email, mat_khau_hash) VALUES (?, ?)",
            (c["email"], pw_hash)
        )
        uv_id = cur.lastrowid

        # ho_so
        p = c["profile"]
        cur.execute("""
            INSERT INTO ho_so (
                ung_vien_id, ten, ho_ten_dem, gioi_tinh,
                ngay_sinh, noi_sinh, dia_chi, quan_huyen,
                tinh_thanh_pho, quoc_gia,
                so_dien_thoai, cccd, ngay_cap_cccd,
                chieu_cao, can_nang, tinh_trang_hon_nhan,
                thanh_tich_noi_bat, trang_thai
            ) VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'cho_duyet'
            )
        """, (
            uv_id,
            p["ten"], p["ho_ten_dem"], p["gioi_tinh"],
            p["ngay_sinh"], p["noi_sinh"], p["dia_chi"], p["quan_huyen"],
            p["tinh_thanh_pho"], p["quoc_gia"],
            p["so_dien_thoai"], p["cccd"], p["ngay_cap_cccd"],
            p["chieu_cao"], p["can_nang"], p["tinh_trang_hon_nhan"],
            p.get("thanh_tich_noi_bat", ""),
        ))
        hs_id = cur.lastrowid

        # trinh_do_chuyen_mon
        e = c["edu"]
        cur.execute("""
            INSERT INTO trinh_do_chuyen_mon (
                ho_so_id, trinh_do, van_bang,
                nhom_chuyen_nganh, chuyen_nganh, quoc_gia,
                loai_truong, ten_truong, loai_hinh_dao_tao,
                thang_diem, diem_tong_ket, xep_loai,
                ngay_bat_dau, ngay_ket_thuc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            hs_id,
            e["trinh_do"], e["van_bang"],
            e["nhom_chuyen_nganh"], e["chuyen_nganh"], e["quoc_gia"],
            e["loai_truong"], e["ten_truong"], e["loai_hinh_dao_tao"],
            e["thang_diem"], e["diem_tong_ket"], e["xep_loai"],
            e["ngay_bat_dau"], e["ngay_ket_thuc"],
        ))

        # trinh_do_ngoai_ngu
        lg = c["lang"]
        cur.execute(
            "INSERT INTO trinh_do_ngoai_ngu (ho_so_id, ngon_ngu, chung_chi, diem) "
            "VALUES (?,?,?,?)",
            (hs_id, lg["ngon_ngu"], lg["chung_chi"], lg["diem"])
        )

        ok += 1
        print(f"  [{idx:02d}] {p['ho_ten_dem']} {p['ten']} ({c['email']})")

    conn.commit()
    conn.close()

    print(f"\n🎉 Đã nạp thành công {ok} hồ sơ ứng viên mẫu vào database.")
    print(f"   Database: {DB_PATH}")


if __name__ == "__main__":
    seed()