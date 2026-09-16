# -*- coding: utf-8 -*-
"""
import_vcb_dot_iv_2025.py
Nhập danh sách ứng viên từ sheet "CVKH" (Chuyên viên khách hàng) trong file:
  001_SOGIAODICH_RA_SOAT_HO_SO_TUYEN_DUNG_DOT_IV_2025.XLSX
(Chỉ lấy dữ liệu sheet CVKH theo yêu cầu — không lấy sheet "CV CNTT".)

Vì file gốc đã che (mask) ngày/tháng sinh của một số ứng viên thành
"xx/xx/YYYY", script này TỰ BỊA ngày/tháng ngẫu nhiên hợp lệ (giữ
nguyên năm thật) cho các trường hợp đó — chỉ để có đủ dữ liệu demo,
KHÔNG phản ánh ngày sinh thật.

Trạng thái hồ sơ được tính TỰ ĐỘNG bằng đúng compute_status() /
luu_ho_so() trong database.py (giống hệt luồng ứng viên nộp đơn thật
qua app.py).

Chạy: python3 import_vcb_dot_iv_2025.py
"""
import re
import random
import database as db

# ─────────────────────────────────────────────────────────────────────
# DỮ LIỆU TRÍCH XUẤT TỪ FILE EXCEL (đã chuẩn hoá field, giữ nguyên giá
# trị gốc trong file — chỉ bịa lại ngày/tháng sinh cho các ô "xx/xx/…")
# ─────────────────────────────────────────────────────────────────────
RAW = [
    # ══════════════ Sheet "CVKH" — 19 ứng viên ══════════════
    dict(sheet="CVKH", ho_dem="Đoàn Phương", ten="Anh", email="phuonganh210903@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2003", chieu_cao="170", cccd="001303008848",
         ngay_cap="27/04/2022", dia_chi="Số 49/560 Nguyễn Văn Cừ, Bồ Đề, Hà Nội", sdt="0914563535",
         ten_truong="Học viện Ngân hàng", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Quản trị kinh doanh",
         xep_loai="Xuất sắc", diem="3.99", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="21/09/2021", ngay_kt="14/08/2025",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="940", ghi_chu="Chương trình liên kết ĐH CityU (Hoa Kỳ)"),
    dict(sheet="CVKH", ho_dem="Lại Quỳnh", ten="Anh", email="lqanh173@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2003", chieu_cao="160", cccd="035303005140",
         ngay_cap="25/04/2021", dia_chi="Ngõ 67, Phường Tương Mai", sdt="0336503289",
         ten_truong="Đại học Kinh tế Quốc dân", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Tài chính – Ngân hàng",
         xep_loai="Xuất sắc", diem="3.72", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="20/09/2021", ngay_kt="15/05/2025",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="785", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Tạ Thị Phương", ten="Anh", email="taphuonganh512003@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2003", chieu_cao="167", cccd="019303003446",
         ngay_cap="25/04/2021", dia_chi="Chính Kinh, Nhân Chính, Thanh Xuân, Hà Nội", sdt="0347898794",
         ten_truong="Học viện Ngân Hàng", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Tài chính – Ngân hàng",
         xep_loai="Xuất sắc", diem="3.85", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="10/09/2021", ngay_kt="25/06/2025",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="805",
         ghi_chu="Có chứng nhận đạt chuẩn kỹ năng sử dụng CNTT cơ bản trên Phụ lục văn bằng"),
    dict(sheet="CVKH", ho_dem="Đặng Châu", ten="Anh", email="chauanh.dang2028@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2002", chieu_cao="158", cccd="001302015342",
         ngay_cap="30/04/2021", dia_chi="Hà Nội", sdt="0339940609",
         ten_truong="Trường Đại học Ngoại thương", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Tài chính – Ngân hàng",
         xep_loai="Giỏi", diem="3.42", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/09/2020", ngay_kt="17/08/2024",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="835", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Nguyễn Ngọc", ten="Anh", email="nngocanh.hvnh@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2003", chieu_cao="158", cccd="001303037416",
         ngay_cap="18/12/2021", dia_chi="236 đường Khương Đình, phường Hạ Đình", sdt="0866920938",
         ten_truong="Học viện Ngân Hàng", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Tài chính – Ngân hàng",
         xep_loai="Xuất sắc", diem="3.75", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="05/09/2021", ngay_kt="26/05/2025",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="640", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Phạm Vân", ten="Anh", email="phamvananh.pmy@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2000", chieu_cao="158", cccd="051300000562",
         ngay_cap="10/04/2021", dia_chi="184 Minh Khai", sdt="0829243456",
         ten_truong="Đại học Kinh tế quốc dân", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Quản trị kinh doanh",
         xep_loai="Giỏi", diem="3.57", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/08/2018", ngay_kt="10/03/2025",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="765", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Vũ Đặng Nguyệt", ten="Anh", email="nguyetanh.workingcontact@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2001", chieu_cao="165", cccd="022301003758",
         ngay_cap="26/12/2022", dia_chi="75 ngách 80/185 Nguyễn Lương Bằng", sdt="0912332001",
         ten_truong="Đại học Kinh tế Quốc dân", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Quản trị và kinh doanh quốc tế",
         xep_loai="Giỏi", diem="3.49", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="05/09/2019", ngay_kt="30/08/2023",
         ngon_ngu="Anh", chung_chi="IELTS", diem_nn="5.5", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Mai Hải", ten="Dương", email="maiduong274@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/2003", chieu_cao="179", cccd="001203001148",
         ngay_cap="20/07/2022", dia_chi="Phòng 11 Nhà A8 Tổ dân phố 17, phường Nghĩa Đô, Hà Nội", sdt="0974031475",
         ten_truong="Học viện Tài chính", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Tài chính – Ngân hàng",
         xep_loai="Giỏi", diem="3.27", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/10/2021", ngay_kt="30/06/2025",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="685", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Nguyễn Hoàng", ten="Dương", email="duongnguyenhoang.vn@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/2003", chieu_cao="178", cccd="030203003040",
         ngay_cap="17/05/2021", dia_chi="B12 Thanh Xuân Bắc", sdt="0378259887",
         ten_truong="Học viện Tài chính", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Đầu tư tài chính",
         xep_loai="Khá", diem="3.03", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="05/09/2021", ngay_kt="02/08/2025",
         ngon_ngu="Anh", chung_chi="B1", diem_nn="5/10", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Nguyễn Thuỳ", ten="Dương", email="ntd02.work@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2002", chieu_cao="155", cccd="025302009273",
         ngay_cap="31/05/2021", dia_chi="42/142 Nguyễn Ngọc Nại", sdt="0363298121",
         ten_truong="Học viện Tài chính", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Kinh tế đầu tư",
         xep_loai="Khá", diem="2.78", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/10/2020", ngay_kt="31/05/2024",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="510", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Nguyễn Thùy", ten="Dương", email="ngthuyduong105@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2002", chieu_cao="166", cccd="001302000567",
         ngay_cap="29/04/2021", dia_chi="Ngõ 99 Định Công Hạ", sdt="0989386248",
         ten_truong="Học viện Ngân hàng", nhom_nganh="KINH TẾ - QUẢN LÝ", chuyen_nganh="Tài chính – Ngân hàng",
         xep_loai="Giỏi", diem="3.39", trinh_do="Đại học", loai_hinh="Chính quy",
         loai_truong="Trường ĐH công lập trong nước", ngay_bd="15/10/2020", ngay_kt="21/06/2024",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="760", ghi_chu=None),
    dict(sheet="CVKH", ho_dem="Chu Nhật", ten="Anh", email="cnhatanh.work@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/2002", chieu_cao="1m83", cccd="001212013935",
         ngay_cap="10/05/2021", dia_chi="Số 8 Tổ 48 Phường Hồng Hà, Hà Nội", sdt="0794050469",
         ten_truong="Trường Quốc tế - Đại học Quốc gia Hà Nội", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Kế toán, phân tích và kiểm toán", xep_loai="Giỏi", diem="3.23", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="05/09/2020", ngay_kt="11/08/2024",
         ngon_ngu=None, chung_chi=None, diem_nn=None, ghi_chu="Trường tốt nghiệp không phù hợp"),
    dict(sheet="CVKH", ho_dem="Nguyễn Thu", ten="Hằng", email="hang310390@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/1990", chieu_cao="158", cccd="036190018598",
         ngay_cap="07/05/2023", dia_chi="số 68 ngõ 44 Trần Thái Tông", sdt="0904770305",
         ten_truong="Đại học Bách khoa Hà Nội liên kết Đại học Troy, Hoa Kỳ", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Quản trị kinh doanh", xep_loai="Khá", diem="3.11", trinh_do="Đại học",
         loai_hinh="Liên kết", loai_truong="Trường liên kết", ngay_bd="05/09/2008", ngay_kt="27/03/2013",
         ngon_ngu="Anh", chung_chi="IELTS", diem_nn="5.5", ghi_chu="Quá tuổi"),
    dict(sheet="CVKH", ho_dem="Phan Trung", ten="Hiếu", email="hieuphan05@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/1998", chieu_cao="170", cccd="014098001853",
         ngay_cap=None, dia_chi="TDP Thảo Nguyên, phường Vân Sơn, tỉnh Sơn La", sdt="0969497598",
         ten_truong="Trường Đại học Kinh tế - Đại học Quốc gia Hà Nội", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Kinh tế chính trị", xep_loai="Khá", diem="2.88", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/09/2016", ngay_kt="01/03/2020",
         ngon_ngu="Anh", chung_chi="IELTS", diem_nn="6.0", ghi_chu="Chuyên ngành không phù hợp"),
    dict(sheet="CVKH", ho_dem="Lê Đình", ten="Hiệp", email="hiepld.yec@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/2001", chieu_cao="171", cccd="040201024379",
         ngay_cap="11/08/2021", dia_chi="Vinhomes Smart City, Tây Mỗ, Nam Từ Liêm, Hà Nội", sdt="0982315510",
         ten_truong="Đại học Kinh tế - Đại học quốc gia Hà Nội", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Chinh sách công", xep_loai="Giỏi", diem="3.29", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="15/09/2019", ngay_kt="13/07/2023",
         ngon_ngu="Anh", chung_chi="B1", diem_nn=None, ghi_chu="Chuyên ngành không phù hợp"),
    dict(sheet="CVKH", ho_dem="Cao Sỹ", ten="Long", email="caosylonght@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/1997", chieu_cao="1m66", cccd="027097000006",
         ngay_cap="15/11/2021", dia_chi="P4K15 tổ 24 ngõ 55 Phố Nguyễn An Ninh", sdt="0948791666",
         ten_truong="Đại học Kinh Tế Quốc Dân", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Kinh tế và quản lý nguồn nhân lực", xep_loai="Khá", diem="7.32", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/10/2015", ngay_kt="01/07/2019",
         ngon_ngu="Anh", chung_chi="B (cấp trước ngày 15/01/2020)", diem_nn="Khá",
         ghi_chu="Chuyên ngành k phù hợp. CCTA B k đạt yêu cầu"),
    dict(sheet="CVKH", ho_dem="Lê Mai", ten="Phương", email="mphuongcustoms@gmail.com",
         gioi_tinh="F", ngay_sinh_mask="xx/xx/2003", chieu_cao="158", cccd="038303023118",
         ngay_cap="26/02/2025", dia_chi="Long Biên, Hà Nội", sdt="0962349118",
         ten_truong="Học viện Tài chính", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Hải quan và nghiệp vụ ngoại thương", xep_loai="Xuất sắc", diem="3.96", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="05/09/2021", ngay_kt="25/06/2025",
         ngon_ngu="Anh/Trung Quốc", chung_chi="IELTS/HSK/HSKK", diem_nn="7.0", ghi_chu="Chuyên ngành không phù hợp"),
    dict(sheet="CVKH", ho_dem="Trần Minh", ten="Tuấn", email="minhtuantr01@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/2001", chieu_cao="181", cccd="001201030807",
         ngay_cap="16/09/2021", dia_chi="Thôn Đức Hậu, Xã Đa Phúc, Hà Nội", sdt="0373175923",
         ten_truong="Đại học Bách khoa Hà Nội", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Quản trị kinh doanh", xep_loai="Xuất Sắc", diem="3.66", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="05/09/2019", ngay_kt="01/10/2023",
         ngon_ngu=None, chung_chi=None, diem_nn=None, ghi_chu="Trường tốt nghiệp không phù hợp"),
    dict(sheet="CVKH", ho_dem="Nguyễn Đức", ten="Tùng", email="nguyenductung28122k@gmail.com",
         gioi_tinh="M", ngay_sinh_mask="xx/xx/2000", chieu_cao="170", cccd="019200009466",
         ngay_cap="25/06/2021", dia_chi="Quận Bắc Từ Liêm, Hà Nội", sdt="0387164230",
         ten_truong="Học Viện Tài Chính", nhom_nganh="KINH TẾ - QUẢN LÝ",
         chuyen_nganh="Hải quan và nghiệp vụ ngoại thương", xep_loai="Giỏi", diem="3.28", trinh_do="Đại học",
         loai_hinh="Chính quy", loai_truong="Trường ĐH công lập trong nước", ngay_bd="01/08/2018", ngay_kt="30/06/2022",
         ngon_ngu="Anh", chung_chi="TOEIC", diem_nn="590", ghi_chu="Chuyên ngành không phù hợp"),
]


def fake_dob(masked: str, seed_key: str) -> str:
    """'xx/xx/2003' -> ngày/tháng ngẫu nhiên hợp lệ, giữ nguyên năm thật.
    Seed theo email để có thể chạy lại và ra kết quả giống nhau."""
    year = re.match(r"xx/xx/(\d{4})", masked).group(1)
    rnd = random.Random(seed_key)
    day = rnd.randint(1, 28)
    month = rnd.randint(1, 12)
    return f"{day:02d}/{month:02d}/{year}"


def infer_thang_diem(diem_str):
    try:
        v = float(str(diem_str).replace(",", "."))
    except Exception:
        return None
    if v <= 4.5:
        return "/4"
    if v <= 10:
        return "/10"
    return None  # hệ điểm khác (VD hệ Anh) — bỏ trống, không áp rule so điểm


def run():
    print(f"Bắt đầu nhập {len(RAW)} hồ sơ từ sheet CVKH trong file "
          f"001_SOGIAODICH_RA_SOAT_HO_SO_TUYEN_DUNG_DOT_IV_2025.XLSX ...\n")
    counts = {}

    for idx, r in enumerate(RAW, 1):
        if r.get("ngay_sinh_mask"):
            ngay_sinh = fake_dob(r["ngay_sinh_mask"], r["email"])
        else:
            ngay_sinh = r["ngay_sinh"]

        gioi_tinh = "Nữ" if r["gioi_tinh"] == "F" else "Nam"

        thong_tin = {
            "ma_buu_dien": None,
            "so_dien_thoai_khac": None,
            "ocr_status": None,
            "ocr_truong": None,
            "ocr_chuyen_nganh": None,
            "ho_ten_dem": r["ho_dem"],
            "ten": r["ten"],
            "gioi_tinh": gioi_tinh,
            "ngay_sinh": ngay_sinh,
            "noi_sinh": None,
            "dia_chi": r["dia_chi"],
            "quan_huyen": None,
            "tinh_thanh_pho": None,
            "quoc_gia": "Việt Nam",
            "so_dien_thoai": r["sdt"],
            "cccd": r["cccd"],
            "ngay_cap_cccd": r["ngay_cap"],
            "chieu_cao": r["chieu_cao"],
            "can_nang": None,
            "tinh_trang_hon_nhan": None,
            "thanh_tich_noi_bat": r["ghi_chu"],
        }

        ds_cm = [{
            "thoi_gian_khoa_hoc": None,
            "don_vi_thoi_gian": None,
            "hoc_ham": None,
            "ngay_bat_dau": r["ngay_bd"],
            "ngay_ket_thuc": r["ngay_kt"],
            "trinh_do": r["trinh_do"],
            "van_bang": "Cử nhân" if r["trinh_do"] == "Đại học" else r["trinh_do"],
            "nhom_chuyen_nganh": r["nhom_nganh"],
            "chuyen_nganh": r["chuyen_nganh"],
            "quoc_gia": "Việt Nam",
            "loai_truong": r["loai_truong"],
            "ten_truong": r["ten_truong"],
            "thang_diem": infer_thang_diem(r["diem"]),
            "diem_tong_ket": str(r["diem"]),
            "loai_hinh_dao_tao": r["loai_hinh"],
            "xep_loai": r["xep_loai"],
        }]

        ds_nn = []
        if r["ngon_ngu"]:
            ds_nn = [{
                "ngon_ngu": r["ngon_ngu"],
                "chung_chi": r["chung_chi"],
                "diem": str(r["diem_nn"]) if r["diem_nn"] is not None else None,
            }]

        uv_id = db.lay_hoac_tao_ung_vien(r["email"], "Vietcombank@2024")
        computed = db.compute_status(thong_tin, ds_cm, ds_nn)
        db.luu_ho_so(uv_id, thong_tin, ds_cm, ds_nn)

        counts[computed] = counts.get(computed, 0) + 1
        print(f"  [{idx:02d}][{r['sheet']:<8}] {r['ho_dem']} {r['ten']:<10} "
              f"(sinh {ngay_sinh}) -> {computed}")

    print("\n=== KẾT QUẢ ===")
    for k, label in [("approve", "✅ approve"), ("deny", "❌ deny"),
                      ("cho_duyet", "⏳ cho_duyet"), ("phong_van", "🎯 phong_van")]:
        print(f"  {label}: {counts.get(k, 0)}")
    print(f"  Tổng: {sum(counts.values())}")


if __name__ == "__main__":
    run()
