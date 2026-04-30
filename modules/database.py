import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cryptostego.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS riwayat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fitur TEXT NOT NULL,
            nama_file TEXT,
            waktu TEXT NOT NULL,
            psnr REAL,
            ssim REAL
        );
    """)
    conn.commit()
    conn.close()

def tambah_riwayat(fitur, nama_file="-", psnr=None, ssim=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO riwayat (fitur, nama_file, waktu, psnr, ssim) VALUES (?, ?, ?, ?, ?)",
        (fitur, nama_file, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), psnr, ssim)
    )
    conn.commit()
    conn.close()

def ambil_riwayat():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM riwayat ORDER BY id DESC").fetchall()
    conn.close()
    return rows