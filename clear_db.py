import sqlite3

conn = sqlite3.connect("demo_hr.db")
cur = conn.cursor()

cur.execute("DELETE FROM trinh_do_ngoai_ngu")
cur.execute("DELETE FROM trinh_do_chuyen_mon")
cur.execute("DELETE FROM ho_so")
cur.execute("DELETE FROM ung_vien")
cur.execute("""
    DELETE FROM sqlite_sequence
    WHERE name IN ('ung_vien','ho_so','trinh_do_chuyen_mon','trinh_do_ngoai_ngu')
""")

conn.commit()
conn.close()
print("Đã xóa sạch toàn bộ ứng viên cũ.")