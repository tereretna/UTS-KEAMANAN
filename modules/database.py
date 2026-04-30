import sqlite3
import os
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH  = os.path.join(ROOT_DIR, 'cryptostego.db')


def get_connection() -> sqlite3.Connection:
    """Buka koneksi ke cryptostego.db dan aktifkan row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Buat tabel riwayat jika belum ada.
    Dipanggil SEKALI saat aplikasi pertama kali start (lihat app.py).
    File DB akan dibuat otomatis oleh sqlite3.connect() jika belum ada.
    """
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS riwayat (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fitur     TEXT    NOT NULL,
            nama_file TEXT    DEFAULT '-',
            waktu     TEXT    NOT NULL,
            psnr      REAL,
            ssim      REAL
        );
    """)
    conn.commit()
    conn.close()


def tambah_riwayat(fitur: str, nama_file: str = "-",
                   psnr: float = None, ssim: float = None) -> None:
    """Simpan satu baris riwayat operasi ke database."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO riwayat (fitur, nama_file, waktu, psnr, ssim) VALUES (?, ?, ?, ?, ?)",
        (fitur, nama_file,
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         psnr, ssim)
    )
    conn.commit()
    conn.close()


def ambil_riwayat() -> list:
    """Ambil semua baris riwayat, urut terbaru dulu."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM riwayat ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows