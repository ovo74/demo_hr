import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, date

st.set_page_config(
    page_title="Admin – Vietcombank Tuyển dụng",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_hr.db")

# ─────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stSidebar"] {visibility:hidden; display:none;}
.stApp {background:#f4f6f9; font-family:'Segoe UI',Arial,sans-serif;}

.vcb-bar {
    background:linear-gradient(90deg,#005f3d,#008a56);
    padding:0 28px; display:flex; align-items:center; gap:28px;
    height:50px; border-bottom:3px solid #ffcc00;
    border-radius:8px 8px 0 0; margin-bottom:0;
}
.vcb-logo {font-size:20px;font-weight:900;letter-spacing:2px;color:#ffcc00;}
.vcb-chip {font-size:12.5px;color:rgba(255,255,255,.75);padding:4px 12px;border-radius:20px;}
.vcb-chip.on {background:rgba(255,255,255,.2);color:#fff;font-weight:700;}

.vcb-subnav {
    background:#fff; display:flex; padding:0 20px;
    border-bottom:2px solid #e2e6ea; gap:0; margin-bottom:0;
}
.vcb-tab {
    font-size:12.5px; padding:10px 18px; color:#666;
    border-bottom:3px solid transparent; font-weight:500; cursor:default;
}
.vcb-tab.on {color:#006a4e; border-bottom:3px solid #006a4e; font-weight:700;}

.vcb-ph {
    background:#fff; padding:10px 20px; border-bottom:1px solid #e2e6ea;
    display:flex; justify-content:space-between; align-items:center;
}
.vcb-pt {font-size:14px; font-weight:700; color:#1a1a2e;}
.vcb-meta {font-size:11px; color:#aaa; margin-top:2px;}
.vcb-open {
    background:#e8f5e9; color:#2e7d32; border:1px solid #a5d6a7;
    padding:3px 12px; border-radius:20px; font-size:11.5px; font-weight:700;
}

.stat-row {
    display:flex; gap:10px; padding:12px 20px;
    background:#fff; border-bottom:1px solid #e2e6ea; flex-wrap:wrap;
}
.stat-b {
    display:flex; flex-direction:column; align-items:center;
    padding:9px 20px; border-radius:8px; min-width:100px;
    border:2px solid #e8ecef; background:#fafafa;
}
.stat-n {font-size:26px; font-weight:800;}
.stat-l {font-size:11px; color:#888; margin-top:1px;}
.s-ap .stat-n {color:#2e7d32;}
.s-dn .stat-n {color:#c62828;}
.s-rc .stat-n {color:#e65100;}
.s-tt .stat-n {color:#1565c0;}

/* Override Streamlit dataframe */
[data-testid="stDataFrame"] {border-radius:8px; overflow:hidden;}

/* Buttons */
div[data-testid="stButton"] > button {
    background:linear-gradient(135deg,#005f3d,#008a56) !important;
    color:#fff !important; border:none !important;
    border-radius:6px !important; font-weight:700 !important;
    box-shadow:0 2px 6px rgba(0,95,61,.2) !important;
}
div[data-testid="stButton"] > button:hover {
    background:#004a30 !important;
}
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
        FROM ho_so h JOIN ung_vien u ON u.id=h.ung_vien_id
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
    conn = get_conn()
    conn.execute("UPDATE ho_so SET trang_thai=? WHERE id=?", (status, hid))
    conn.commit()
    conn.close()

def bulk_save(records):
    conn = get_conn()
    for r in records:
        conn.execute(
            "UPDATE ho_so SET trang_thai=? WHERE id=?",
            (r["computed_status"], r["id"])
        )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# LOGIC TRẠNG THÁI
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
    reasons = []
    today   = date.today()

    dob = parse_date(c.get("ngay_sinh"))
    if dob:
        age = (today - dob).days / 365.25
        if age > 30:
            reasons.append(f"Quá tuổi ({int(age)} tuổi)")
    else:
        reasons.append("Không xác định ngày sinh")

    recheck = False
    for cm in ds_cm:
        td     = (cm.get("trinh_do") or "").strip()
        lh     = (cm.get("loai_hinh_dao_tao") or "").strip()
        diem   = (cm.get("diem_tong_ket") or "").strip()
        thang  = (cm.get("thang_diem") or "").strip()
        qg     = (cm.get("quoc_gia") or "").strip().lower()
        lt     = (cm.get("loai_truong") or "").strip().lower()

        if "cao đẳng" in td.lower():
            reasons.append(f"Trình độ Cao đẳng không hợp lệ")

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
        return "recheck", []
    return "approve", []

SLABEL = {
    "approve":   "✅ Đủ điều kiện",
    "deny":      "❌ Từ chối",
    "recheck":   "🔍 Cần xem xét",
    "cho_duyet": "⏳ Chờ duyệt",
}


# ─────────────────────────────────────────────────────────────────────
# LOAD & ENRICH
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3)
def get_enriched():
    rows = load_all()
    out  = []
    for c in rows:
        ds_cm = load_cm(c["id"])
        ds_nn = load_nn(c["id"])
        status, reasons = compute_status(c, ds_cm)
        out.append({
            **c,
            "computed_status": status,
            "deny_reasons":    reasons,
            "ds_cm":           ds_cm,
            "ds_nn":           ds_nn,
        })
    return out


# ─────────────────────────────────────────────────────────────────────
# DIALOG CHI TIẾT
# ─────────────────────────────────────────────────────────────────────
@st.dialog("📋 Thông tin chi tiết ứng viên", width="large")
def detail_dialog(rec):
    ho_ten = f"{rec['ho_ten_dem'] or ''} {rec['ten'] or ''}".strip()
    cs     = rec["computed_status"]
    b_lbl  = SLABEL.get(cs, cs)

    color_map = {"approve": "#2e7d32", "deny": "#c62828",
                 "recheck": "#e65100", "cho_duyet": "#1565c0"}
    bg_map    = {"approve": "#e8f5e9", "deny": "#ffebee",
                 "recheck": "#fff3e0", "cho_duyet": "#e3f2fd"}
    col_h = color_map.get(cs, "#333")
    bg_h  = bg_map.get(cs, "#f5f5f5")

    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;
         background:{bg_h};padding:10px 16px;border-radius:8px;margin-bottom:12px;
         border-left:5px solid {col_h};'>
        <div>
            <div style='font-size:17px;font-weight:800;color:#005f3d;'>{ho_ten}</div>
            <div style='font-size:11px;color:#888;margin-top:3px;'>
                Mã hồ sơ: <b>#{rec["id"]}</b> &nbsp;|&nbsp; Nộp lúc: {rec.get("nop_luc","—")}
            </div>
        </div>
        <span style='background:{bg_h};color:{col_h};border:1.5px solid {col_h};
              padding:4px 12px;border-radius:20px;font-size:12px;font-weight:800;'>
            {b_lbl}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Thông tin cá nhân
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

    addr = " – ".join(filter(None, [
        rec.get("dia_chi"), rec.get("quan_huyen"), rec.get("tinh_thanh_pho")
    ]))
    st.markdown(f"**📍 Địa chỉ:** {addr or '—'}")
    if rec.get("thanh_tich_noi_bat"):
        st.markdown(f"**🏆 Thành tích:** {rec.get('thanh_tich_noi_bat')}")

    st.divider()

    # Trình độ chuyên môn
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
                        ("Tên trường","ten_truong"), ("Trình độ","trinh_do"),
                        ("Văn bằng","van_bang"),     ("Nhóm CN","nhom_chuyen_nganh"),
                        ("Chuyên ngành","chuyen_nganh"), ("Quốc gia","quoc_gia"),
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
                        ("Thời gian",
                         f"{cm.get('ngay_bat_dau','—')} → {cm.get('ngay_ket_thuc','—')}"),
                    ]:
                        st.markdown(f"**{lbl}:** {val}")
    else:
        st.info("Chưa có dữ liệu trình độ chuyên môn.")

    st.divider()

    # Ngoại ngữ
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

    # Lý do deny / recheck
    if cs == "deny" and rec.get("deny_reasons"):
        st.divider()
        st.markdown("##### ⚠️ Lý do từ chối tự động")
        for r in rec["deny_reasons"]:
            st.error(f"• {r}")
    elif cs == "recheck":
        st.divider()
        st.warning(
            "⚠️ Trường / Quốc gia nước ngoài — "
            "Admin cần xem xét và quyết định thủ công."
        )

    st.divider()

    # Duyệt trạng thái
    st.markdown("##### ⚙️ Cập nhật trạng thái duyệt")
    opt_keys = ["approve", "deny", "recheck"]
    opt_lbl  = {
        "approve": "✅ Đủ điều kiện",
        "deny":    "❌ Từ chối",
        "recheck": "🔍 Cần xem xét",
    }
    idx_def = opt_keys.index(cs) if cs in opt_keys else 0
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
            st.success("✅ Đã lưu!")
            st.rerun()
    with col_c:
        if st.button("✖ Đóng", key=f"cl_{rec['id']}", use_container_width=True):
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
# LAYOUT CHÍNH
# ─────────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="vcb-bar">
    <span class="vcb-logo">VCB</span>
    <span class="vcb-chip">Tổng quan</span>
    <span class="vcb-chip on">Tuyển dụng</span>
    <span class="vcb-chip">Phỏng vấn</span>
    <span class="vcb-chip">Báo cáo</span>
    <span style="margin-left:auto;font-size:12px;color:rgba(255,255,255,.6);">👤 Admin HR</span>
</div>
""", unsafe_allow_html=True)

# Sub-nav
st.markdown("""
<div class="vcb-subnav">
    <div class="vcb-tab">📋 Chi tiết Yêu cầu</div>
    <div class="vcb-tab">💼 Thông tin việc làm</div>
    <div class="vcb-tab on">👥 Ứng viên</div>
    <div class="vcb-tab">📣 Thông báo Tuyển dụng</div>
    <div class="vcb-tab">🔍 Tìm kiếm Ứng viên</div>
</div>
""", unsafe_allow_html=True)

# Load
enriched = get_enriched()
total    = len(enriched)
n_ap = sum(1 for r in enriched if r["computed_status"] == "approve")
n_dn = sum(1 for r in enriched if r["computed_status"] == "deny")
n_rc = sum(1 for r in enriched if r["computed_status"] == "recheck")

# Page header
st.markdown(f"""
<div class="vcb-ph">
    <div>
        <div class="vcb-pt">[Sở giao dịch] Danh sách ứng viên tuyển dụng</div>
        <div class="vcb-meta">
            Tổng: <b>{total}</b> hồ sơ &nbsp;|&nbsp;
            Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </div>
    <span class="vcb-open">● Đang mở tuyển dụng</span>
</div>
""", unsafe_allow_html=True)

# Stat bubbles
st.markdown(f"""
<div class="stat-row">
    <div class="stat-b s-ap">
        <span class="stat-n">{n_ap}</span>
        <span class="stat-l">✅ Đủ điều kiện</span>
    </div>
    <div class="stat-b s-dn">
        <span class="stat-n">{n_dn}</span>
        <span class="stat-l">❌ Từ chối</span>
    </div>
    <div class="stat-b s-rc">
        <span class="stat-n">{n_rc}</span>
        <span class="stat-l">🔍 Cần xem xét</span>
    </div>
    <div class="stat-b s-tt" style="margin-left:auto;">
        <span class="stat-n">{total}</span>
        <span class="stat-l">📁 Tổng hồ sơ</span>
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
        ["Tất cả", "✅ Đủ điều kiện", "❌ Từ chối", "🔍 Cần xem xét"],
        label_visibility="collapsed")
with cf3:
    q_td = st.selectbox("Trình độ",
        ["Tất cả trình độ", "Đại học", "Thạc sĩ", "Tiến sĩ", "Cao đẳng"],
        label_visibility="collapsed")

ST_MAP = {
    "✅ Đủ điều kiện": "approve",
    "❌ Từ chối":       "deny",
    "🔍 Cần xem xét":  "recheck",
}

filtered = enriched
if q_name.strip():
    qn = q_name.strip().lower()
    filtered = [r for r in filtered
                if qn in (r["ho_ten_dem"] or "").lower()
                or qn in (r["ten"] or "").lower()]
if q_st != "Tất cả":
    ts = ST_MAP.get(q_st, "")
    filtered = [r for r in filtered if r["computed_status"] == ts]
if q_td != "Tất cả trình độ":
    filtered = [r for r in filtered
                if any(q_td.lower() in (cm.get("trinh_do") or "").lower()
                       for cm in r["ds_cm"])]

st.markdown(
    f"<div style='font-size:11.5px;color:#888;padding:2px 0 4px;'>"
    f"Hiển thị <b>{len(filtered)}</b> / {total} hồ sơ</div>",
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────────────
# BẢNG — st.dataframe với row selection
# ─────────────────────────────────────────────────────────────────────
if not filtered:
    st.info("Không có hồ sơ nào phù hợp với bộ lọc.")
else:
    # Xây dựng DataFrame hiển thị
    rows = []
    for i, rec in enumerate(filtered, 1):
        cm0 = rec["ds_cm"][0] if rec["ds_cm"] else {}
        nn0 = rec["ds_nn"][0] if rec["ds_nn"] else {}
        ho_ten = f"{rec['ho_ten_dem'] or ''} {rec['ten'] or ''}".strip()
        rows.append({
            "STT":         i,
            "Họ và tên":   ho_ten,
            "Email":       rec.get("email", "—"),
            "Giới tính":   rec.get("gioi_tinh", "—"),
            "Ngày sinh":   rec.get("ngay_sinh", "—"),
            "Số ĐT":       rec.get("so_dien_thoai", "—"),
            "Tên trường":  cm0.get("ten_truong", "—"),
            "Trình độ":    cm0.get("trinh_do", "—"),
            "Chuyên ngành": cm0.get("chuyen_nganh", "—"),
            "Điểm TK":     cm0.get("diem_tong_ket", "—"),
            "Thang":       cm0.get("thang_diem", ""),
            "Loại hình ĐT": cm0.get("loai_hinh_dao_tao", "—"),
            "Loại trường": cm0.get("loai_truong", "—"),
            "Ngoại ngữ":   nn0.get("ngon_ngu", "—"),
            "Chứng chỉ":   nn0.get("chung_chi", "—"),
            "Điểm NN":     nn0.get("diem", "—"),
            "Trạng thái":  SLABEL.get(rec["computed_status"], rec["computed_status"]),
            "👁 Chi tiết":  "🔍 Xem",
        })

    df_display = pd.DataFrame(rows)

    # Render bảng với selection
    event = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=min(40 + len(filtered) * 37, 520),
        column_config={
            "STT":          st.column_config.NumberColumn("STT", width=48),
            "Họ và tên":    st.column_config.TextColumn("Họ và tên", width=160),
            "Email":        st.column_config.TextColumn("Email", width=190),
            "Giới tính":    st.column_config.TextColumn("GT", width=50),
            "Ngày sinh":    st.column_config.TextColumn("Ngày sinh", width=90),
            "Số ĐT":        st.column_config.TextColumn("Số ĐT", width=110),
            "Tên trường":   st.column_config.TextColumn("Tên trường", width=160),
            "Trình độ":     st.column_config.TextColumn("Trình độ", width=90),
            "Chuyên ngành": st.column_config.TextColumn("Chuyên ngành", width=150),
            "Điểm TK":      st.column_config.TextColumn("Điểm TK", width=70),
            "Thang":        st.column_config.TextColumn("Thang", width=55),
            "Loại hình ĐT": st.column_config.TextColumn("Loại hình ĐT", width=100),
            "Loại trường":  st.column_config.TextColumn("Loại trường", width=140),
            "Ngoại ngữ":    st.column_config.TextColumn("Ngoại ngữ", width=80),
            "Chứng chỉ":    st.column_config.TextColumn("Chứng chỉ", width=80),
            "Điểm NN":      st.column_config.TextColumn("Điểm NN", width=65),
            "Trạng thái":   st.column_config.TextColumn("Trạng thái", width=130),
            "👁 Chi tiết":  st.column_config.TextColumn("Chi tiết", width=80),
        },
        selection_mode="single-row",
        on_select="rerun",
        key="main_table",
    )

    # Xử lý khi chọn hàng
    sel_rows = event.selection.get("rows", []) if event.selection else []
    if sel_rows:
        idx = sel_rows[0]
        if 0 <= idx < len(filtered):
            detail_dialog(filtered[idx])

    st.markdown(
        "<div style='font-size:11px;color:#bbb;padding:2px 0 8px;'>"
        "💡 Nhấp vào dòng bất kỳ (hoặc cột 👁 Chi tiết) để xem đầy đủ thông tin và duyệt trạng thái</div>",
        unsafe_allow_html=True
    )

    # ── Nút duyệt danh sách ──
    st.markdown("---")
    b1, b2 = st.columns([3, 1])
    with b1:
        fa = sum(1 for r in filtered if r["computed_status"] == "approve")
        fd = sum(1 for r in filtered if r["computed_status"] == "deny")
        fr = sum(1 for r in filtered if r["computed_status"] == "recheck")
        st.markdown(
            f"<div style='font-size:12.5px;color:#555;padding:6px 0;'>"
            f"Sẽ áp dụng trạng thái tự động cho <b>{len(filtered)}</b> hồ sơ đang hiển thị — "
            f"✅ <b style='color:#2e7d32;'>{fa}</b> duyệt &nbsp;"
            f"❌ <b style='color:#c62828;'>{fd}</b> từ chối &nbsp;"
            f"🔍 <b style='color:#e65100;'>{fr}</b> xem xét"
            f"</div>",
            unsafe_allow_html=True
        )
    with b2:
        if st.button("✅ Duyệt danh sách ứng viên",
                     use_container_width=True, key="bulk"):
            bulk_save(filtered)
            st.cache_data.clear()
            st.success(f"✅ Đã duyệt {len(filtered)} hồ sơ!")
            st.rerun()