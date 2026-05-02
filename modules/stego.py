import io
import numpy as np
from PIL import Image
from scipy.fft import dctn, idctn

try:
    from skimage.metrics import peak_signal_noise_ratio as psnr_func # type: ignore
    from skimage.metrics import structural_similarity as ssim_func # type: ignore
    SKIMAGE_OK = True
except ImportError:
    SKIMAGE_OK = False

DELIMITER = b'\x00\xFF\xAA\x55\xDE\xAD\xBE\xEF'

def _text_to_bits(data: bytes) -> list:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def _bits_to_bytes(bits: list) -> bytes:
    result = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        byte = 0
        for b in chunk:
            byte = (byte << 1) | b
        result.append(byte)
    return bytes(result)

def calculate_metrics(original: np.ndarray, stego: np.ndarray) -> tuple:
    if not SKIMAGE_OK:
        return 0.0, 0.0
    
    psnr_val = psnr_func(original, stego, data_range=255)
    try:
        ssim_val = ssim_func(original, stego, channel_axis=-1, data_range=255)
    except TypeError:
        try:
            ssim_val = ssim_func(original, stego, multichannel=True, data_range=255)
        except Exception:
            ssim_val = 0.0
            
    return round(float(psnr_val), 2), round(float(ssim_val), 4)

def _embed_dct_marker(arr: np.ndarray, bits_marker: list) -> np.ndarray:
    """Menyisipkan marker DCT pada koefisien mid-frequency statis (4,4)."""
    arr_f = arr.copy().astype(np.float64)
    h, w = arr_f.shape[:2]
    bit_idx = 0
    max_bits = min(len(bits_marker), 64) 

    for bi in range(0, h - 7, 8):
        for bj in range(0, w - 7, 8):
            if bit_idx >= max_bits:
                break
            # Operasi DCT pada blok 8x8 (Channel 0 / Red)
            block = arr_f[bi:bi+8, bj:bj+8, 0].copy()
            dct_block = dctn(block, norm='ortho')
            
            # Ubah koefisien (4,4) secara aman
            val = int(dct_block[4, 4])
            if bits_marker[bit_idx] == 1:
                dct_block[4, 4] = (val & ~1) | 1
            else:
                dct_block[4, 4] = (val & ~1)
                
            # Kembalikan ke spasial
            arr_f[bi:bi+8, bj:bj+8, 0] = idctn(dct_block, norm='ortho')
            bit_idx += 1
            
    # Pastikan nilai kembali ke rentang valid piksel
    return np.clip(np.round(arr_f), 0, 255).astype(np.uint8)

def encode_stego(img_bytes: bytes, payload_str: str) -> tuple:
    payload = payload_str.encode('utf-8') + DELIMITER
    bits = _text_to_bits(payload)

    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    arr_original = np.array(img, dtype=np.uint8)
    arr = arr_original.copy()

    h, w, _ = arr.shape
    max_bits = h * w * 3 

    if len(bits) > max_bits:
        raise ValueError(f"Kapasitas gambar penuh! Butuh {len(bits)//8} byte, tersedia {max_bits//8} byte.")

    # 1. Lapisan DCT (Marker statis)
    dct_marker_bits = _text_to_bits(DELIMITER[:4]) 
    arr = _embed_dct_marker(arr, dct_marker_bits)

    # 2. Lapisan LSB (Sequential Spasial)
    bit_idx = 0
    for i in range(h):
        for j in range(w):
            for ch in range(3): 
                if bit_idx >= len(bits):
                    break
                arr[i, j, ch] = (int(arr[i, j, ch]) & 254) | bits[bit_idx]
                bit_idx += 1

    psnr, ssim = calculate_metrics(arr_original, arr)

    # Simpan Lossless (Wajib PNG)
    stego_img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    stego_img.save(buf, format='PNG', optimize=False, compress_level=1)
    return buf.getvalue(), psnr, ssim

def decode_stego(stego_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(stego_bytes)).convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    h, w, _ = arr.shape

    # Ekstrak berurutan (Sequential Spasial)
    bits = []
    for i in range(h):
        for j in range(w):
            for ch in range(3):
                bits.append(int(arr[i, j, ch] & 1))

    raw_bytes = _bits_to_bytes(bits)
    delim_pos = raw_bytes.find(DELIMITER)

    if delim_pos == -1:
        raise ValueError("Tidak ada pesan tersembunyi. Pastikan password benar dan gambar tidak dikompres ke JPG.")

    return raw_bytes[:delim_pos].decode('utf-8')