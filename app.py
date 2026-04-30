from flask import Flask, render_template, request, flash, send_file
import os, io, uuid
from modules.database import init_db, tambah_riwayat, ambil_riwayat
from modules.crypto import encrypt_aes, decrypt_aes
from modules.stego import encode_stego, decode_stego

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "kunci_rahasia_udayana")

# ── Upload folder ──────────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Init DB saat startup ───────────────────────────────────────────────────────
with app.app_context():
    init_db()

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# --- 1. HYBRID ENCODE ---
@app.route('/hybrid/encode', methods=['GET', 'POST'])
def hybrid_encode():
    if request.method == 'POST':
        msg  = request.form.get('message')
        pwd  = request.form.get('password')
        file = request.files.get('image')
        try:
            cipher = encrypt_aes(msg, pwd)
            stego_img, psnr, ssim = encode_stego(file.read(), cipher)
            filename = f"hybrid_{uuid.uuid4().hex[:6]}.png"
            tambah_riwayat("Hybrid Encode", filename, psnr, ssim)
            flash(f"Berhasil! PSNR: {psnr} dB | SSIM: {ssim}", "success")
            return send_file(
                io.BytesIO(stego_img),
                mimetype='image/png',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            flash(str(e), "danger")
    return render_template('hybrid_encode.html')

# --- 2. HYBRID DECODE ---
@app.route('/hybrid/decode', methods=['GET', 'POST'])
def hybrid_decode():
    result = None
    if request.method == 'POST':
        pwd  = request.form.get('password')
        file = request.files.get('image')
        try:
            cipher = decode_stego(file.read())
            result = decrypt_aes(cipher, pwd)
            tambah_riwayat("Hybrid Decode", file.filename)
            flash("Pesan rahasia berhasil didekripsi!", "success")
        except Exception as e:
            flash(str(e), "danger")
    return render_template('hybrid_decode.html', result=result)

# --- 3. CRYPTO ENCODE ---
@app.route('/crypto/encode', methods=['GET', 'POST'])
def crypto_encode():
    result = None
    if request.method == 'POST':
        try:
            result = encrypt_aes(
                request.form.get('message'),
                request.form.get('password')
            )
            tambah_riwayat("Crypto Encode")
        except Exception as e:
            flash(str(e), "danger")
    return render_template('crypto_encode.html', result=result)

# --- 4. CRYPTO DECODE ---
@app.route('/crypto/decode', methods=['GET', 'POST'])
def crypto_decode():
    result = None
    if request.method == 'POST':
        try:
            result = decrypt_aes(
                request.form.get('ciphertext'),
                request.form.get('password')
            )
            tambah_riwayat("Crypto Decode")
        except Exception as e:
            flash(str(e), "danger")
    return render_template('crypto_decode.html', result=result)

# --- 5. STEGO ENCODE ---
@app.route('/stego/encode', methods=['GET', 'POST'])
def stego_encode():
    if request.method == 'POST':
        try:
            stego_img, psnr, ssim = encode_stego(
                request.files.get('image').read(),
                request.form.get('message')
            )
            filename = f"stego_{uuid.uuid4().hex[:6]}.png"
            tambah_riwayat("Stego Encode", filename, psnr, ssim)
            flash(f"Berhasil menyisipkan pesan! PSNR: {psnr} dB | SSIM: {ssim}", "success")
            return send_file(
                io.BytesIO(stego_img),
                mimetype='image/png',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            flash(str(e), "danger")
    return render_template('stego_encode.html')

# --- 6. STEGO DECODE ---
@app.route('/stego/decode', methods=['GET', 'POST'])
def stego_decode():
    result = None
    if request.method == 'POST':
        try:
            file = request.files.get('image')
            result = decode_stego(file.read())
            tambah_riwayat("Stego Decode", file.filename)
        except Exception as e:
            flash(str(e), "danger")
    return render_template('stego_decode.html', result=result)

# --- RIWAYAT ---
@app.route('/riwayat')
def riwayat():
    return render_template('riwayat.html', data=ambil_riwayat())

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=False)