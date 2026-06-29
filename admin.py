import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, date

st.set_page_config(
    page_title="Admin – Vietcombank Tuyển dụng",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_hr.db")

# ─────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header,
[data-testid="stSidebar"],
[data-testid="stSidebarNav"] { visibility:hidden; display:none; }

.stApp { background:#f4f6f9; font-family:'Segoe UI',Arial,sans-serif; }

.vcb-bar {
    background:linear-gradient(90deg,#005f3d,#008a56);
    padding:0 28px; display:flex; align-items:center; gap:28px;
    height:50px; border-bottom:3px solid #ffcc00;
    border-radius:8px 8px 0 0;
}
.vcb-logo { font-size:20px; font-weight:900; letter-spacing:2px; color:#ffcc00; }
.vcb-chip { font-size:12.5px; color:rgba(255,255,255,.75); padding:4px 12px; border-radius:20px; }
.vcb-chip.on { background:rgba(255,255,255,.2); color:#fff; font-weight:700; }

.vcb-subnav {
    background:#fff; display:flex; padding:0 20px; border-bottom:2px solid #e2e6ea;
}
.vcb-tab { font-size:12.5px; padding:10px 18px; color:#666;
    border-bottom:3px solid transparent; font-weight:500; }
.vcb-tab.on { color:#006a4e; border-bottom:3px solid #006a4e; font-weight:700; }

.vcb-ph {
    background:#fff; padding:10px 20px; border-bottom:1px solid #e2e6ea;
    display:flex; justify-content:space-between; align-items:center;
}
.vcb-pt { font-size:14px; font-weight:700; color:#1a1a2e; }
.vcb-meta { font-size:11px; color:#aaa; margin-top:2px; }
.vcb-open { background:#e8f5e9; color:#2e7d32; border:1px solid #a5d6a7;
    padding:3px 12px; border-radius:20px; font-size:11.5px; font-weight:700; }

.stat-row {
    display:flex; gap:10px; padding:12px 20px;
    background:#fff; border-bottom:1px solid #e2e6ea; flex-wrap:wrap;
}
.stat-b { display:flex; flex-direction:column; align-items:center;
    padding:9px 20px; border-radius:8px; min-width:100px;
    border:2px solid #e8ecef; background:#fafafa; }
.stat-n { font-size:26px; font-weight:800; }
.stat-l { font-size:11px; color:#888; margin-top:1px; }
.s-ap .stat-n { color:#2e7d32; }
.s-dn .stat-n { color:#c62828; }
.s-rc .stat-n { color:#e65100; }
.s-tt .stat-n { color:#1565c0; }

[data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }

div[data-testid="stButton"] > button {
    background:linear-gradient(135deg,#005f3d,#008a56) !important;
    color:#fff !important; border:none !important;
    border-radius:6px !important; font-weight:700 !important;
    box-shadow:0 2px 6px rgba(0,95,61,.2) !important;
}
div[data-testid="stButton"] > button:hover { background:#004a30 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_all():
    conn = get_conn()
    rows = conn.execute("""
        SELECT h.id, h.ho_ten_dem, h.ten, h.gioi_tinh, h.ngay_sinh,
               h.dia_chi, h.quan_huyen, h.tinh_thanh_pho, h.quoc_gia,
               h.so_dien_thoai, h.so_dien_thoai_khac,
               h.cccd, h.ngay_cap_cccd, h.chieu_cao, h.can_nang,
               h.tinh_trang_hon_nhan, h.thanh_tich_noi_bat, h.noi_sinh,
               h.trang_thai, h.nop_luc, u.email
        FROM ho_so h JOIN ung_vien u ON u.id = h.ung_vien_id
        ORDER BY h.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def load_cm(hid):
    conn = get_conn()
    r = conn.execute(
        "SELECT * FROM trinh_do_chuyen_mon WHERE ho_so_id=? ORDER BY id", (hid,)
    ).fetchall()
    conn.close()
    return [dict(x) for x in r]

def load_nn(hid):
    conn = get_conn()
    r = conn.execute(
        "SELECT * FROM trinh_do_ngoai_ngu WHERE ho_so_id=? ORDER BY id", (hid,)
    ).fetchall()
    conn.close()
    return [dict(x) for x in r]

def save_status(hid, status):
    """Lưu trạng thái do admin chọn vào DB."""
    conn = get_conn()
    conn.execute("UPDATE ho_so SET trang_thai=? WHERE id=?", (status, hid))
    conn.commit()
    conn.close()

def bulk_save(records):
    conn = get_conn()
    for r in records:
        # Nếu admin đã ghi đè thủ công → giữ nguyên quyết định đó
        # Nếu chưa ai set (None) → dùng kết quả tính tự động
        effective = r.get("trang_thai") or r["computed_status"]
        conn.execute(
            "UPDATE ho_so SET trang_thai=? WHERE id=?",
            (effective, r["id"])
        )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# LOGIC TRẠNG THÁI TỰ ĐỘNG
# ─────────────────────────────────────────────────────────────────────
FOREIGN = ["nước ngoài", "quốc tế", "international", "foreign"]

def parse_date(s):
    if not s:
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except Exception:
            pass
    return None

def compute_status(c, ds_cm):
    """Trả về (computed_status, [lý do deny])."""
    reasons = []
    today   = date.today()

    dob = parse_date(c.get("ngay_sinh"))
    if dob:
        age = (today - dob).days / 365.25
        if age > 30:
            reasons.append(f"Quá tuổi ({int(age)} tuổi, tối đa 30)")
    else:
        reasons.append("Không xác định ngày sinh")

    recheck = False
    for cm in ds_cm:
        td    = (cm.get("trinh_do") or "").strip()
        lh    = (cm.get("loai_hinh_dao_tao") or "").strip()
        diem  = (cm.get("diem_tong_ket") or "").strip()
        thang = (cm.get("thang_diem") or "").strip()
        qg    = (cm.get("quoc_gia") or "").strip().lower()
        lt    = (cm.get("loai_truong") or "").strip().lower()

        if "cao đẳng" in td.lower():
            reasons.append("Trình độ Cao đẳng không hợp lệ")

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

        if lh and "chính quy" not in lh.lower():
            reasons.append(f"Loại hình '{lh}' không phải Chính quy")

        if any(k in qg for k in FOREIGN) or any(k in lt for k in FOREIGN):
            recheck = True

    if reasons:
        return "deny", reasons
    if recheck:
        return "cho_duyet", []   # recheck → chờ duyệt thủ công
    return "approve", []


# Nhãn hiển thị cho từng trạng thái
SLABEL = {
    "approve":   "✅ Đủ điều kiện",
    "deny":      "❌ Từ chối",
    "cho_duyet": "⏳ Chờ duyệt",
}


# ─────────────────────────────────────────────────────────────────────
# LOAD & ENRICH  (cache ngắn để sau rerun thấy dữ liệu mới ngay)
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=2)
def get_enriched():
    rows = load_all()
    out  = []
    for c in rows:
        ds_cm = load_cm(c["id"])
        ds_nn = load_nn(c["id"])
        comp, reasons = compute_status(c, ds_cm)
        out.append({
            **c,
            "computed_status": comp,       # trạng thái tính từ rule
            "deny_reasons":    reasons,
            "ds_cm":           ds_cm,
            "ds_nn":           ds_nn,
            # trang_thai từ DB (admin có thể đã ghi đè) → đây là giá trị hiển thị
            # c["trang_thai"] đã có sẵn trong **c
        })
    return out


# ─────────────────────────────────────────────────────────────────────
# DIALOG CHI TIẾT
# ─────────────────────────────────────────────────────────────────────
@st.dialog("📋 Thông tin chi tiết ứng viên", width="large")
def detail_dialog(rec):
    ho_ten = f"{rec['ho_ten_dem'] or ''} {rec['ten'] or ''}".strip()

    # Trạng thái hiển thị = giá trị DB hiện tại (admin có thể đã ghi đè)
    db_status   = rec.get("trang_thai") or rec["computed_status"]
    comp_status = rec["computed_status"]

    color_map = {"approve":"#2e7d32","deny":"#c62828","recheck":"#e65100","cho_duyet":"#1565c0"}
    bg_map    = {"approve":"#e8f5e9","deny":"#ffebee","recheck":"#fff3e0","cho_duyet":"#e3f2fd"}
    col_h = color_map.get(db_status, "#555")
    bg_h  = bg_map.get(db_status, "#f5f5f5")

    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;
         background:{bg_h};padding:10px 16px;border-radius:8px;margin-bottom:12px;
         border-left:5px solid {col_h};'>
        <div>
            <div style='font-size:17px;font-weight:800;color:#005f3d;'>{ho_ten}</div>
            <div style='font-size:11px;color:#888;margin-top:3px;'>
                Mã hồ sơ: <b>#{rec["id"]}</b> &nbsp;|&nbsp;
                Nộp lúc: {rec.get("nop_luc","—")} &nbsp;|&nbsp;
                Đề xuất tự động:
                <b style="color:{color_map.get(comp_status,'#555')}">
                    {SLABEL.get(comp_status, comp_status)}
                </b>
            </div>
        </div>
        <span style='background:{bg_h};color:{col_h};border:1.5px solid {col_h};
              padding:4px 12px;border-radius:20px;font-size:12px;font-weight:800;'>
            {SLABEL.get(db_status, db_status)}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Thông tin cá nhân ──
    st.markdown("##### 🧑 Thông tin cá nhân")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Email:** {rec.get('email','—')}")
        st.markdown(f"**Giới tính:** {rec.get('gioi_tinh','—')}")
        st.markdown(f"**Ngày sinh:** {rec.get('ngay_sinh','—')}")
        st.markdown(f"**Nơi sinh:** {rec.get('noi_sinh','—')}")
        st.markdown(f"**CCCD/CMND:** {rec.get('cccd','—')}")
        st.markdown(f"**Ngày cấp:** {rec.get('ngay_cap_cccd','—')}")
    with c2:
        st.markdown(f"**Số ĐT:** {rec.get('so_dien_thoai','—')}")
        st.markdown(f"**SĐT khác:** {rec.get('so_dien_thoai_khac','—')}")
        st.markdown(f"**Chiều cao:** {rec.get('chieu_cao','—')} cm")
        st.markdown(f"**Cân nặng:** {rec.get('can_nang','—')} kg")
        st.markdown(f"**Hôn nhân:** {rec.get('tinh_trang_hon_nhan','—')}")
        st.markdown(f"**Quốc tịch:** {rec.get('quoc_gia','—')}")
    addr = " – ".join(filter(None, [rec.get("dia_chi"), rec.get("quan_huyen"), rec.get("tinh_thanh_pho")]))
    st.markdown(f"**📍 Địa chỉ:** {addr or '—'}")
    if rec.get("thanh_tich_noi_bat"):
        st.markdown(f"**🏆 Thành tích:** {rec.get('thanh_tich_noi_bat')}")

    st.divider()

    # ── Trình độ chuyên môn ──
    st.markdown("##### 🎓 Trình độ chuyên môn")
    if rec["ds_cm"]:
        for i, cm in enumerate(rec["ds_cm"], 1):
            with st.expander(
                f"[{i}] {cm.get('ten_truong','—')}  ·  {cm.get('trinh_do','—')}",
                expanded=(i == 1)
            ):
                g1, g2 = st.columns(2)
                with g1:
                    for lbl, key in [
                        ("Tên trường","ten_truong"),("Trình độ","trinh_do"),
                        ("Văn bằng","van_bang"),("Nhóm CN","nhom_chuyen_nganh"),
                        ("Chuyên ngành","chuyen_nganh"),("Quốc gia","quoc_gia"),
                    ]:
                        st.markdown(f"**{lbl}:** {cm.get(key,'—')}")
                with g2:
                    diem_txt = f"{cm.get('diem_tong_ket','—')} {cm.get('thang_diem','')}".strip()
                    for lbl, val in [
                        ("Loại hình ĐT", cm.get("loai_hinh_dao_tao","—")),
                        ("Loại trường",  cm.get("loai_truong","—")),
                        ("Xếp loại",     cm.get("xep_loai","—")),
                        ("Điểm TK",      diem_txt),
                        ("Học hàm",      cm.get("hoc_ham","—")),
                        ("Thời gian",    f"{cm.get('ngay_bat_dau','—')} → {cm.get('ngay_ket_thuc','—')}"),
                    ]:
                        st.markdown(f"**{lbl}:** {val}")
    else:
        st.info("Chưa có dữ liệu trình độ chuyên môn.")

    st.divider()

    # ── Ngoại ngữ ──
    st.markdown("##### 🌐 Ngoại ngữ")
    if rec["ds_nn"]:
        for nn in rec["ds_nn"]:
            st.markdown(
                f"• **{nn.get('ngon_ngu','—')}** "
                f"– Chứng chỉ: **{nn.get('chung_chi','—')}** "
                f"– Điểm: **{nn.get('diem','—')}**"
            )
    else:
        st.info("Chưa có dữ liệu ngoại ngữ.")

    # ── Lý do deny/recheck ──
    if comp_status == "deny" and rec.get("deny_reasons"):
        st.divider()
        st.markdown("##### ⚠️ Lý do hệ thống đề xuất Từ chối")
        for r in rec["deny_reasons"]:
            st.error(f"• {r}")
    elif comp_status == "recheck":
        st.divider()
        st.warning("⚠️ Trường / Quốc gia nước ngoài — Admin cần xem xét và quyết định thủ công.")

    st.divider()

    # ── Cập nhật trạng thái ──
    st.markdown("##### ⚙️ Cập nhật trạng thái duyệt")

    opt_keys = ["approve", "deny", "cho_duyet"]
    opt_lbl  = {
        "approve":   "✅ Đủ điều kiện",
        "deny":      "❌ Từ chối",
        "cho_duyet": "⏳ Chờ duyệt",
    }
    # Default = trạng thái DB hiện tại (không phải computed)
    idx_def = opt_keys.index(db_status) if db_status in opt_keys else 0

    new_s = st.selectbox(
        "Chọn trạng thái",
        opt_keys,
        index=idx_def,
        format_func=lambda x: opt_lbl[x],
        key=f"sel_{rec['id']}"
    )

    col_s, col_c = st.columns(2)
    with col_s:
        if st.button("💾 Lưu trạng thái", key=f"sv_{rec['id']}", use_container_width=True):
            save_status(rec["id"], new_s)
            st.cache_data.clear()
            # QUAN TRỌNG: KHÔNG gọi st.rerun() ở đây.
            # st.rerun() bên trong dialog sẽ đóng dialog ngay lập tức
            # khiến người dùng không thấy thông báo thành công.
            st.success(
                f"✅ Đã lưu **{opt_lbl[new_s]}** thành công! "
                f"Nhấn **Đóng** để cập nhật bảng danh sách."
            )
    with col_c:
        if st.button("✖ Đóng", key=f"cl_{rec['id']}", use_container_width=True):
            # Clear cache TẠI ĐÂY để bảng reload với dữ liệu mới khi rerun
            st.cache_data.clear()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
# LAYOUT CHÍNH
# ─────────────────────────────────────────────────────────────────────

# Đọc logo, xoá nền trắng (giống app.py) rồi encode base64
import base64, io
from PIL import Image

def _load_logo(path):
    try:
        img = Image.open(path).convert("RGBA")
        new_data = []
        for r, g, b, a in img.getdata():
            # pixel gần-trắng → trong suốt
            if abs(r - g) < 15 and abs(g - b) < 15 and r > 180:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append((r, g, b, a))
        img.putdata(new_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vcblogo.png")
_logo_b64  = _load_logo(_logo_path)
_logo_tag  = (
    f'<div style="background:#fff;border-radius:6px;padding:4px 10px;display:flex;align-items:center;">'
    f'<img src="data:image/png;base64,{_logo_b64}" '
    f'style="height:30px;width:auto;object-fit:contain;" alt="Vietcombank">'
    f'</div>'
    if _logo_b64 else
    '<span class="vcb-logo">VCB</span>'
)

st.markdown(f"""
<div class="vcb-bar">
    {_logo_tag}
    <span class="vcb-chip">Tổng quan</span>
    <span class="vcb-chip on">Tuyển dụng</span>
    <span class="vcb-chip">Phỏng vấn</span>
    <span class="vcb-chip">Báo cáo</span>
    <span style="margin-left:auto;font-size:12px;color:rgba(255,255,255,.6);">👤 Admin HR</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="vcb-subnav">
    <div class="vcb-tab">📋 Chi tiết Yêu cầu</div>
    <div class="vcb-tab">💼 Thông tin việc làm</div>
    <div class="vcb-tab on">👥 Ứng viên</div>
    <div class="vcb-tab">📣 Thông báo Tuyển dụng</div>
    <div class="vcb-tab">🔍 Tìm kiếm Ứng viên</div>
</div>
""", unsafe_allow_html=True)

# Load dữ liệu
enriched = get_enriched()
total = len(enriched)

# Hiển thị thông báo thành công sau khi bấm "Duyệt danh sách ứng viên" ở lượt
# trước (đã lưu vào session_state TRƯỚC khi rerun vì st.success() gọi ngay
# trước st.rerun() sẽ bị mất). Hiển thị 1 lần rồi xóa, tránh lặp lại mỗi rerun.
if "bulk_success" in st.session_state:
    _bs = st.session_state.pop("bulk_success")
    st.success(
        f"✅ Đã áp dụng trạng thái cho {_bs['total']} hồ sơ — "
        f"{_bs['approve']} duyệt, {_bs['deny']} từ chối."
    )

# Đếm theo trang_thai (DB) — phản ánh quyết định thực tế của admin
n_ap = sum(1 for r in enriched if (r.get("trang_thai") or r["computed_status"]) == "approve")
n_dn = sum(1 for r in enriched if (r.get("trang_thai") or r["computed_status"]) == "deny")
n_cd = sum(1 for r in enriched if (r.get("trang_thai") or r["computed_status"]) in ("cho_duyet", "recheck"))

st.markdown(f"""
<div class="vcb-ph">
    <div>
        <div class="vcb-pt">[Sở giao dịch] Danh sách ứng viên tuyển dụng</div>
        <div class="vcb-meta">Tổng: <b>{total}</b> hồ sơ &nbsp;|&nbsp;
            Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>
    <span class="vcb-open">● Đang mở tuyển dụng</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stat-row">
    <div class="stat-b s-ap"><span class="stat-n">{n_ap}</span><span class="stat-l">✅ Đủ điều kiện</span></div>
    <div class="stat-b s-dn"><span class="stat-n">{n_dn}</span><span class="stat-l">❌ Từ chối</span></div>
    <div class="stat-b s-rc"><span class="stat-n">{n_cd}</span><span class="stat-l">⏳ Chờ duyệt</span></div>
    <div class="stat-b s-tt" style="margin-left:auto;">
        <span class="stat-n">{total}</span><span class="stat-l">📁 Tổng hồ sơ</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── Bộ lọc ──
cf1, cf2, cf3 = st.columns([3, 2, 2])
with cf1:
    q_name = st.text_input("Tên", placeholder="🔍 Nhập họ tên...", label_visibility="collapsed")
with cf2:
    q_st = st.selectbox("Trạng thái",
        ["Tất cả", "✅ Đủ điều kiện", "❌ Từ chối", "⏳ Chờ duyệt"],
        label_visibility="collapsed")
with cf3:
    q_td = st.selectbox("Trình độ",
        ["Tất cả trình độ", "Đại học", "Thạc sĩ", "Tiến sĩ", "Cao đẳng"],
        label_visibility="collapsed")

ST_MAP = {"✅ Đủ điều kiện": "approve", "❌ Từ chối": "deny", "⏳ Chờ duyệt": "cho_duyet"}

filtered = enriched
if q_name.strip():
    qn = q_name.strip().lower()
    filtered = [r for r in filtered
                if qn in (r["ho_ten_dem"] or "").lower()
                or qn in (r["ten"] or "").lower()]
if q_st != "Tất cả":
    ts = ST_MAP.get(q_st, "")
    filtered = [r for r in filtered
                if (r.get("trang_thai") or r["computed_status"]) in (
                    [ts, "recheck"] if ts == "cho_duyet" else [ts]
                )]
if q_td != "Tất cả trình độ":
    filtered = [r for r in filtered
                if any(q_td.lower() in (cm.get("trinh_do") or "").lower()
                       for cm in r["ds_cm"])]

st.markdown(
    f"<div style='font-size:11.5px;color:#888;padding:2px 0 6px;'>"
    f"Hiển thị <b>{len(filtered)}</b> / {total} hồ sơ</div>",
    unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# BẢNG st.dataframe + row selection
# ─────────────────────────────────────────────────────────────────────
if not filtered:
    st.info("Không có hồ sơ nào phù hợp với bộ lọc.")
else:
    rows = []
    for i, rec in enumerate(filtered, 1):
        cm0    = rec["ds_cm"][0] if rec["ds_cm"] else {}
        nn0    = rec["ds_nn"][0] if rec["ds_nn"] else {}
        ho_ten = f"{rec['ho_ten_dem'] or ''} {rec['ten'] or ''}".strip()

        # Trạng thái hiển thị = DB value (admin-controlled); fallback = computed
        display_status = rec.get("trang_thai") or rec["computed_status"]

        rows.append({
            "STT":            i,
            "Họ và tên":      ho_ten,
            "Email":          rec.get("email", "—"),
            "GT":             rec.get("gioi_tinh", "—"),
            "Ngày sinh":      rec.get("ngay_sinh", "—"),
            "Số ĐT":          rec.get("so_dien_thoai", "—"),
            "Tên trường":     cm0.get("ten_truong", "—"),
            "Trình độ":       cm0.get("trinh_do", "—"),
            "Chuyên ngành":   cm0.get("chuyen_nganh", "—"),
            "Điểm TK":        cm0.get("diem_tong_ket", "—"),
            "Thang":          cm0.get("thang_diem", ""),
            "Loại hình ĐT":   cm0.get("loai_hinh_dao_tao", "—"),
            "Loại trường":    cm0.get("loai_truong", "—"),
            "Ngoại ngữ":      nn0.get("ngon_ngu", "—"),
            "Chứng chỉ":      nn0.get("chung_chi", "—"),
            "Điểm NN":        nn0.get("diem", "—"),
            # Hiển thị nhãn (✅/❌/🔍) của trạng thái DB thực tế
            "Trạng thái":     SLABEL.get(display_status, display_status),
            # Cột cuối — nhắc user click để mở dialog
            "👁 Chi tiết":    "📋 Xem",
        })

    df_display = pd.DataFrame(rows)

    event = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=min(40 + len(filtered) * 37, 560),
        column_config={
            "STT":           st.column_config.NumberColumn("STT", width=45),
            "Họ và tên":     st.column_config.TextColumn("Họ và tên", width=155),
            "Email":         st.column_config.TextColumn("Email", width=185),
            "GT":            st.column_config.TextColumn("GT", width=45),
            "Ngày sinh":     st.column_config.TextColumn("Ngày sinh", width=88),
            "Số ĐT":         st.column_config.TextColumn("Số ĐT", width=108),
            "Tên trường":    st.column_config.TextColumn("Tên trường", width=155),
            "Trình độ":      st.column_config.TextColumn("Trình độ", width=85),
            "Chuyên ngành":  st.column_config.TextColumn("Chuyên ngành", width=145),
            "Điểm TK":       st.column_config.TextColumn("Điểm TK", width=65),
            "Thang":         st.column_config.TextColumn("Thang", width=52),
            "Loại hình ĐT":  st.column_config.TextColumn("Loại hình ĐT", width=98),
            "Loại trường":   st.column_config.TextColumn("Loại trường", width=135),
            "Ngoại ngữ":     st.column_config.TextColumn("Ngoại ngữ", width=78),
            "Chứng chỉ":     st.column_config.TextColumn("Chứng chỉ", width=78),
            "Điểm NN":       st.column_config.TextColumn("Điểm NN", width=62),
            "Trạng thái":    st.column_config.TextColumn("Trạng thái", width=128),
            "👁 Chi tiết":   st.column_config.TextColumn("Chi tiết", width=78),
        },
        selection_mode="single-row",
        on_select="rerun",
        key="main_tbl",
    )

    # Mở dialog khi user click vào hàng
    sel = event.selection.get("rows", []) if event.selection else []
    if sel and 0 <= sel[0] < len(filtered):
        detail_dialog(filtered[sel[0]])

    st.markdown(
        "<div style='font-size:11px;color:#bbb;padding:3px 0 10px;'>"
        "💡 Nhấp vào dòng bất kỳ để xem đầy đủ thông tin và thay đổi trạng thái duyệt</div>",
        unsafe_allow_html=True)

    # ── Nút Duyệt danh sách ──
    st.markdown("---")
    b1, b2 = st.columns([3, 1])

    # Tính số lượng theo trang_thai HIỆU LỰC (DB nếu có, không thì dùng rule tự động)
    # Đây là số liệu thật sẽ áp dụng khi bấm nút — KHÔNG dùng thuần computed_status,
    # vì hồ sơ đã được admin ghi đè thủ công (lưu trạng thái riêng) phải tính theo
    # giá trị đã lưu, không phải tính lại từ đầu.
    fa = sum(1 for r in filtered if (r.get("trang_thai") or r["computed_status"]) == "approve")
    fd = sum(1 for r in filtered if (r.get("trang_thai") or r["computed_status"]) == "deny")
    fc = sum(1 for r in filtered if (r.get("trang_thai") or r["computed_status"]) in ("cho_duyet", "recheck"))

    with b1:
        st.markdown(
            f"<div style='font-size:12.5px;color:#555;padding:6px 0;'>"
            f"Sẽ áp dụng trạng thái tự động cho <b>{len(filtered)}</b> hồ sơ đang hiển thị — "
            f"✅ <b style='color:#2e7d32;'>{fa}</b> duyệt &nbsp;"
            f"❌ <b style='color:#c62828;'>{fd}</b> từ chối &nbsp;"
            f"⏳ <b style='color:#1565c0;'>{fc}</b> chờ duyệt"
            f"</div>",
            unsafe_allow_html=True
        )
    with b2:
        # Khóa nút nếu còn hồ sơ chờ duyệt — admin phải xử lý hết "chờ duyệt"
        # (qua dialog chi tiết / lưu trạng thái thủ công) trước khi được áp dụng
        # trạng thái tự động cho cả danh sách.
        if st.button("✅ Duyệt danh sách ứng viên",
                     use_container_width=True, key="bulk",
                     disabled=(fc > 0)):
            bulk_save(filtered)
            st.cache_data.clear()
            # Lưu thông báo vào session_state TRƯỚC khi rerun
            # (st.success() gọi trước st.rerun() sẽ biến mất ngay)
            st.session_state["bulk_success"] = {
                "approve": fa,
                "deny":    fd,
                "total":   fa + fd,
            }
            st.rerun()
        if fc > 0:
            st.markdown(
                f"<div style='font-size:11px;color:#e65100;padding:4px 2px 0;'>"
                f"⏳ Còn <b>{fc}</b> hồ sơ chờ duyệt — xử lý hết để mở khóa nút này</div>",
                unsafe_allow_html=True
            )