import streamlit as st
import sqlite3
import pandas as pd
from database import init_db, DB_PATH

# ─────────────────────────────────────────────────────────────────────
# CẤU HÌNH TRANG
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DB Viewer — demo_hr",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()  # đảm bảo bảng đã tồn tại

# ─────────────────────────────────────────────────────────────────────
# CSS — phong cách terminal / SQL client
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Nền tối toàn trang */
.stApp { background-color: #1e1e2e !important; font-family: 'Consolas', 'Courier New', monospace; }

/* Sidebar */
[data-testid="stSidebar"] { background-color: #181825 !important; }
[data-testid="stSidebar"] * { color: #cdd6f4 !important; }

/* Ẩn header / footer mặc định */
#MainMenu, footer, header { visibility: hidden; }

/* Tiêu đề lớn */
h1, h2, h3 { color: #89dceb !important; font-family: 'Consolas', monospace !important; }

/* Nhãn widget */
label[data-testid="stWidgetLabel"] p,
.stCaption p, p, span { color: #cdd6f4 !important; }

/* Text area SQL */
.stTextArea textarea {
    background-color: #11111b !important;
    color: #a6e3a1 !important;
    font-family: 'Consolas', 'Courier New', monospace !important;
    font-size: 14px !important;
    border: 1px solid #313244 !important;
}

/* Nút bấm */
.stButton > button {
    background-color: #313244 !important;
    color: #89dceb !important;
    border: 1px solid #45475a !important;
    border-radius: 4px !important;
    font-family: 'Consolas', monospace !important;
    font-weight: bold !important;
}
.stButton > button:hover { background-color: #45475a !important; }

/* Selectbox */
div[data-baseweb="select"] {
    background-color: #11111b !important;
    border: 1px solid #313244 !important;
}
div[data-baseweb="select"] span { color: #cdd6f4 !important; }

/* Bảng dữ liệu */
[data-testid="stDataFrame"] { border: 1px solid #313244 !important; }

/* Metric boxes */
[data-testid="stMetric"] {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] { color: #a6e3a1 !important; font-family: 'Consolas', monospace !important; }
[data-testid="stMetricLabel"] { color: #6c7086 !important; }

/* Divider */
hr { border-color: #313244 !important; }

/* Badge thành công / lỗi */
.badge-ok  { background:#1e3a2f; color:#a6e3a1; border:1px solid #a6e3a1; padding:2px 10px; border-radius:4px; font-size:12px; }
.badge-err { background:#3a1e1e; color:#f38ba8; border:1px solid #f38ba8; padding:2px 10px; border-radius:4px; font-size:12px; }

/* Tabs */
[data-testid="stTabs"] button { color: #6c7086 !important; font-family: 'Consolas', monospace !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #89dceb !important; border-bottom: 2px solid #89dceb !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# HÀM TIỆN ÍCH
# ─────────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """Chạy SQL bất kỳ. Trả về (DataFrame, None) hoặc (None, error_msg)."""
    try:
        conn = get_conn()
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)


def count_table(table: str) -> int:
    try:
        conn = get_conn()
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return 0


def get_all_tables() -> list[str]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def styled_dataframe(df: pd.DataFrame):
    """Hiển thị DataFrame với style SQL-client."""
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=False,
        column_config={
            col: st.column_config.TextColumn(col, width="medium")
            for col in df.columns
        },
    )


# ─────────────────────────────────────────────────────────────────────
# SIDEBAR — ĐIỀU HƯỚNG & CÀI ĐẶT
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗄️ demo_hr.db")
    st.markdown(f"`{DB_PATH}`")
    st.markdown("---")

    tables = get_all_tables()
    st.markdown("**TABLES**")
    for t in tables:
        n = count_table(t)
        st.markdown(f"&nbsp;&nbsp;📋 `{t}` &nbsp;<span style='color:#6c7086;font-size:12px;'>({n} rows)</span>", unsafe_allow_html=True)

    st.markdown("---")
    auto_refresh = st.toggle("🔄 Auto-refresh (5 s)", value=False)
    if st.button("⟳ Refresh ngay"):
        st.rerun()
    st.markdown("---")
    st.markdown("<span style='color:#6c7086;font-size:12px;'>DB Viewer v1.0<br/>demo_hr project</span>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()


# ─────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────
st.markdown("# 🗄️ Database Viewer — `demo_hr.db`")
st.markdown("Giao diện kiểm tra dữ liệu thời gian thực. Nhấn **Refresh** hoặc bật **Auto-refresh** sau mỗi lần ứng viên nộp đơn.")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────
# METRICS TỔNG QUAN
# ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("👤 Ứng viên",      count_table("ung_vien"))
col2.metric("📄 Hồ sơ",         count_table("ho_so"))
col3.metric("🎓 Văn bằng",      count_table("trinh_do_chuyen_mon"))
col4.metric("🌐 Ngoại ngữ",     count_table("trinh_do_ngoai_ngu"))

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────
# TABS — MỖI BẢNG MỘT TAB + TAB SQL THỦ CÔNG
# ─────────────────────────────────────────────────────────────────────
tab_uv, tab_hs, tab_cm, tab_nn, tab_join, tab_sql = st.tabs([
    "👤 ung_vien",
    "📄 ho_so",
    "🎓 chuyen_mon",
    "🌐 ngoai_ngu",
    "🔗 JOIN tổng hợp",
    "⌨️ SQL thủ công",
])

# ── Tab: UNG_VIEN ──────────────────────────────────────────────────
with tab_uv:
    st.markdown("### `SELECT * FROM ung_vien`")
    df, err = run_query("SELECT * FROM ung_vien ORDER BY id DESC")
    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("Chưa có ứng viên nào. Hãy đăng nhập vào giao diện ứng tuyển để tạo bản ghi.")
    else:
        st.markdown(f"<span class='badge-ok'>✓ {len(df)} rows</span>", unsafe_allow_html=True)
        st.caption(f"Columns: {', '.join(df.columns.tolist())}")
        styled_dataframe(df)

# ── Tab: HO_SO ────────────────────────────────────────────────────
with tab_hs:
    st.markdown("### `SELECT * FROM ho_so`")

    # Bộ lọc nhanh
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        filter_status = st.selectbox(
            "Lọc theo trang_thai:",
            ["-- Tất cả --", "cho_duyet", "da_duyet", "tu_choi"],
            key="filter_hs_status"
        )
    with f_col2:
        filter_ocr = st.selectbox(
            "Lọc theo ocr_status:",
            ["-- Tất cả --", "APPROVE", "DENY"],
            key="filter_hs_ocr"
        )

    where_clauses = []
    if filter_status != "-- Tất cả --":
        where_clauses.append(f"trang_thai = '{filter_status}'")
    if filter_ocr != "-- Tất cả --":
        where_clauses.append(f"ocr_status = '{filter_ocr}'")
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    df, err = run_query(f"SELECT * FROM ho_so {where_sql} ORDER BY id DESC")
    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("Không có bản ghi nào khớp điều kiện lọc.")
    else:
        st.markdown(f"<span class='badge-ok'>✓ {len(df)} rows</span>", unsafe_allow_html=True)
        st.caption(f"Columns: {', '.join(df.columns.tolist())}")
        styled_dataframe(df)

# ── Tab: CHUYEN MON ───────────────────────────────────────────────
with tab_cm:
    st.markdown("### `SELECT * FROM trinh_do_chuyen_mon`")
    df, err = run_query("SELECT * FROM trinh_do_chuyen_mon ORDER BY id DESC")
    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("Chưa có dữ liệu trình độ chuyên môn.")
    else:
        st.markdown(f"<span class='badge-ok'>✓ {len(df)} rows</span>", unsafe_allow_html=True)
        st.caption(f"Columns: {', '.join(df.columns.tolist())}")
        styled_dataframe(df)

# ── Tab: NGOAI NGU ────────────────────────────────────────────────
with tab_nn:
    st.markdown("### `SELECT * FROM trinh_do_ngoai_ngu`")
    df, err = run_query("SELECT * FROM trinh_do_ngoai_ngu ORDER BY id DESC")
    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("Chưa có dữ liệu ngoại ngữ.")
    else:
        st.markdown(f"<span class='badge-ok'>✓ {len(df)} rows</span>", unsafe_allow_html=True)
        st.caption(f"Columns: {', '.join(df.columns.tolist())}")
        styled_dataframe(df)

# ── Tab: JOIN TỔNG HỢP ────────────────────────────────────────────
with tab_join:
    st.markdown("### Hồ sơ đầy đủ — JOIN 4 bảng")
    st.caption("Mỗi ứng viên + hồ sơ + văn bằng + ngoại ngữ đầu tiên (dùng để xem nhanh)")

    JOIN_SQL = """
SELECT
    u.id                            AS uv_id,
    u.email,
    h.id                            AS hs_id,
    h.ho_ten_dem || ' ' || h.ten   AS ho_ten,
    h.gioi_tinh,
    h.ngay_sinh,
    h.so_dien_thoai,
    h.cccd,
    h.tinh_thanh_pho,
    h.ocr_status,
    h.ocr_truong,
    h.ocr_chuyen_nganh,
    h.trang_thai,
    h.nop_luc,
    cm.trinh_do,
    cm.van_bang,
    cm.ten_truong,
    cm.chuyen_nganh,
    cm.xep_loai,
    cm.diem_tong_ket,
    nn.ngon_ngu,
    nn.chung_chi,
    nn.diem                         AS diem_nn
FROM ho_so h
JOIN ung_vien u          ON u.id = h.ung_vien_id
LEFT JOIN trinh_do_chuyen_mon cm ON cm.ho_so_id = h.id
LEFT JOIN trinh_do_ngoai_ngu  nn ON nn.ho_so_id = h.id
ORDER BY h.id DESC
"""
    with st.expander("📋 Xem câu SQL", expanded=False):
        st.code(JOIN_SQL.strip(), language="sql")

    df, err = run_query(JOIN_SQL)
    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("Chưa có hồ sơ nào được nộp.")
    else:
        st.markdown(f"<span class='badge-ok'>✓ {len(df)} rows</span>", unsafe_allow_html=True)
        styled_dataframe(df)

        # Nút export CSV
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Xuất CSV",
            data=csv_data,
            file_name="ho_so_export.csv",
            mime="text/csv",
        )

# ── Tab: SQL THỦ CÔNG ─────────────────────────────────────────────
with tab_sql:
    st.markdown("### ⌨️ Chạy SQL tùy ý")
    st.caption("Hỗ trợ SELECT, INSERT, UPDATE, DELETE, PRAGMA... — chỉ dùng cho mục đích debug.")

    default_sql = "SELECT * FROM ho_so ORDER BY id DESC LIMIT 20;"
    sql_input = st.text_area(
        "Nhập câu SQL:",
        value=default_sql,
        height=120,
        key="custom_sql",
        label_visibility="collapsed",
    )

    run_col, clear_col, _ = st.columns([1, 1, 5])
    with run_col:
        run_btn = st.button("▶ Run", type="primary")
    with clear_col:
        if st.button("✕ Clear"):
            st.session_state["custom_sql"] = ""
            st.rerun()

    if run_btn and sql_input.strip():
        sql_upper = sql_input.strip().upper()
        # SELECT → dùng read_sql
        if sql_upper.startswith("SELECT") or sql_upper.startswith("PRAGMA"):
            df, err = run_query(sql_input)
            if err:
                st.markdown(f"<span class='badge-err'>❌ ERROR</span>", unsafe_allow_html=True)
                st.error(err)
            else:
                st.markdown(f"<span class='badge-ok'>✓ {len(df)} rows returned</span>", unsafe_allow_html=True)
                styled_dataframe(df)
        # DML → dùng execute trực tiếp
        else:
            try:
                conn = get_conn()
                cur = conn.execute(sql_input)
                conn.commit()
                affected = cur.rowcount
                conn.close()
                st.markdown(f"<span class='badge-ok'>✓ Query OK — {affected} row(s) affected</span>", unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.markdown(f"<span class='badge-err'>❌ ERROR</span>", unsafe_allow_html=True)
                st.error(str(e))

    # Gợi ý câu SQL nhanh
    st.markdown("---")
    st.markdown("**Gợi ý nhanh:**")
    quick_queries = {
        "Đếm hồ sơ theo trạng thái":  "SELECT trang_thai, COUNT(*) as so_luong FROM ho_so GROUP BY trang_thai;",
        "Hồ sơ APPROVE gần nhất":     "SELECT id, ho_ten_dem, ten, ocr_truong, nop_luc FROM ho_so WHERE ocr_status='APPROVE' ORDER BY id DESC LIMIT 10;",
        "Danh sách ngoại ngữ":         "SELECT h.ho_ten_dem, h.ten, nn.ngon_ngu, nn.chung_chi, nn.diem FROM trinh_do_ngoai_ngu nn JOIN ho_so h ON h.id = nn.ho_so_id;",
        "PRAGMA table_info(ho_so)":    "PRAGMA table_info(ho_so);",
        "Xóa toàn bộ dữ liệu test":   "DELETE FROM ho_so; DELETE FROM ung_vien;",
    }
    for label, q in quick_queries.items():
        if st.button(f"⚡ {label}", key=f"quick_{label}"):
            st.session_state["custom_sql"] = q
            st.rerun()
