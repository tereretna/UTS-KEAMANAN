import io
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr_func
from skimage.metrics import structural_similarity as ssim_func

DELIMITER = b'\x00\xFF\xAA\x55\xDE\xAD\xBE\xEF'

def _text_to_bits(data_bytes):
    return [(b >> i) & 1 for b in data_bytes for i in range(7, -1, -1)]

def _bits_to_bytes(bits):
    result = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8: break
        val = 0
        for b in chunk: val = (val << 1) | b
        result.append(val)
    return bytes(result)

def calculate_metrics(img1, img2):
    psnr_val = psnr_func(img1, img2, data_range=255)
    ssim_val = ssim_func(img1, img2, channel_axis=-1, data_range=255)
    return round(psnr_val, 2), round(ssim_val, 4)

def encode_stego(img_bytes: bytes, payload_str: str) -> tuple:
    payload = payload_str.encode('utf-8') + DELIMITER
    bits = _text_to_bits(payload)
    
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    arr_orig = np.array(img, dtype=np.uint8)
    arr = arr_orig.copy()
    h, w, c = arr.shape
    
    if len(bits) > (h * w * 3):
        raise ValueError("Kapasitas gambar tidak cukup untuk pesan ini.")
        
    idx = 0
    for i in range(h):
        for j in range(w):
            for ch in range(3):
                if idx < len(bits):
                    arr[i, j, ch] = (arr[i, j, ch] & 254) | bits[idx]
                    idx += 1
                    
    psnr, ssim = calculate_metrics(arr_orig, arr)
    
    out_img = Image.fromarray(arr)
    buf = io.BytesIO()
    out_img.save(buf, format='PNG', optimize=False, compress_level=1)
    return buf.getvalue(), psnr, ssim

def decode_stego(stego_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(stego_bytes)).convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    h, w, c = arr.shape
    
    bits = [int(arr[i, j, ch] & 1) for i in range(h) for j in range(w) for ch in range(3)]
    raw_bytes = _bits_to_bytes(bits)
    
    pos = raw_bytes.find(DELIMITER)
    if pos == -1: raise ValueError("Tidak ditemukan pesan tersembunyi pada gambar ini.")
    return raw_bytes[:pos].decode('utf-8')