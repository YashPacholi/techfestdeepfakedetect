from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Scan
import cv2
import numpy as np
from datetime import datetime
import io
import os
import base64

detection_bp = Blueprint('detection', __name__)

@detection_bp.route('/detect')
@login_required
def detect():
    return render_template('detect.html')

@detection_bp.route('/api/analyze_image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image'}), 400
    file = request.files['image']
    img_bytes = file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({'error': 'Invalid image'}), 400
    result = run_analysis(img, img_bytes)
    if current_user.is_authenticated:
        try:
            scan = Scan(
                user_id=current_user.id,
                filename=file.filename,
                scan_type='image',
                verdict=result['verdict'],
                score=result['deepfake_score'],
                details=str(result.get('flags', '')),
                created_at=datetime.utcnow()
            )
            db.session.add(scan)
            db.session.commit()
        except:
            pass
    return jsonify(result)


@detection_bp.route('/api/analyze_frame', methods=['POST'])
def analyze_frame():
    data = request.get_json()
    if not data or 'frame' not in data:
        return jsonify({'error': 'No frame'}), 400
    img_data = data['frame'].split(',')[1]
    img_bytes = base64.b64decode(img_data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({'error': 'Invalid frame'}), 400
    result = run_analysis(img, None)
    return jsonify(result)


@detection_bp.route('/api/analyze_video', methods=['POST'])
def analyze_video():
    import time
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    file = request.files['video']
    os.makedirs('static/uploads', exist_ok=True)
    temp_path = f'static/uploads/temp_{int(time.time())}.mp4'
    file.save(temp_path)
    cap = cv2.VideoCapture(temp_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25)
    duration = round(total_frames / fps, 1)
    sample_interval = max(1, total_frames // 15)
    frame_results = []
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % sample_interval == 0:
            r = run_analysis(frame, None)
            frame_results.append({
                'frame':     int(frame_count),
                'timestamp': float(round(frame_count / fps, 2)),
                'score':     float(r['deepfake_score']),
                'faces':     int(r['faces_detected'])
            })
        frame_count += 1
    cap.release()
    try:
        os.remove(temp_path)
    except:
        pass
    if not frame_results:
        return jsonify({'error': 'Could not process video'}), 400
    avg_score = float(sum(r['score'] for r in frame_results) / len(frame_results))
    max_score = float(max(r['score'] for r in frame_results))
    verdict = 'DEEPFAKE DETECTED' if avg_score > 42 else 'LIKELY AUTHENTIC'
    risk = 'HIGH' if avg_score > 65 else 'MEDIUM' if avg_score > 28 else 'LOW'
    if current_user.is_authenticated:
        try:
            scan = Scan(
                user_id=current_user.id,
                filename=file.filename,
                scan_type='video',
                verdict='FAKE' if avg_score > 42 else 'REAL',
                score=float(round(avg_score, 1)),
                details='video analysis',
                created_at=datetime.utcnow()
            )
            db.session.add(scan)
            db.session.commit()
        except:
            pass
    return jsonify({
        'verdict':         verdict,
        'risk_level':      risk,
        'average_score':   float(round(avg_score, 1)),
        'max_score':       float(round(max_score, 1)),
        'frames_analyzed': int(len(frame_results)),
        'total_frames':    int(total_frames),
        'duration':        float(duration),
        'frame_data':      frame_results
    })


# ══════════════════════════════════════════════════════
#  CORE DETECTION ENGINE
#  Real photo   → score  0 - 27%  → REAL
#  Suspicious   → score 28 - 41%  → SUSPICIOUS
#  AI/Deepfake  → score 42 - 100% → FAKE
# ══════════════════════════════════════════════════════

def run_analysis(img, img_bytes=None):
    score   = 0.0
    flags   = []
    details = {}

    h, w = img.shape[:2]
    if w > 900:
        img = cv2.resize(img, (900, int(h * 900 / w)))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Face Detection
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    faces = cascade.detectMultiScale(gray, 1.05, 4, minSize=(40, 40))
    faces_detected = int(len(faces))

    if faces_detected > 0:
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        pad = 20
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(w, x + fw + pad), min(h, y + fh + pad)
        face_region = img[y1:y2, x1:x2]
        face_gray   = gray[y1:y2, x1:x2]
    else:
        face_region = img
        face_gray   = gray

    fh_r, fw_r = face_gray.shape

    # CHECK 1: TEXTURE SMOOTHNESS
    lap_var = float(cv2.Laplacian(face_gray, cv2.CV_64F).var())
    blurred = cv2.GaussianBlur(face_gray, (5, 5), 0)
    local_texture = float(cv2.absdiff(face_gray, blurred).mean())

    if lap_var < 28:
        score += 38
        flags.append(f'Extremely smooth texture (var={lap_var:.0f}) — AI generated')
    elif lap_var < 65:
        score += 22
        flags.append(f'Low texture variance (var={lap_var:.0f}) — possibly AI')
    elif lap_var < 110 and local_texture < 3.2:
        score += 15
        flags.append(f'Unnaturally uniform local texture')
    elif lap_var > 1000:
        score += 16
        flags.append(f'Unusual high-frequency noise (var={lap_var:.0f})')

    details['texture_variance'] = float(round(lap_var, 1))
    details['local_texture']    = float(round(local_texture, 2))

    # CHECK 2: FACIAL SYMMETRY
    if fw_r > 40:
        hw    = fw_r // 2
        left  = face_gray[:, :hw]
        right = cv2.flip(face_gray[:, hw:hw * 2], 1)
        mw    = min(left.shape[1], right.shape[1])
        asym  = float(cv2.absdiff(left[:, :mw], right[:, :mw]).mean())
        if asym < 2.0:
            score += 42
            flags.append(f'Perfect facial symmetry (score={asym:.2f}) — strong AI indicator')
        elif asym < 4.5:
            score += 24
            flags.append(f'Very high symmetry (score={asym:.2f}) — AI indicator')
        elif asym < 7.0:
            score += 10
            flags.append(f'Slightly high symmetry (score={asym:.2f})')
        details['facial_symmetry'] = float(round(asym, 2))
    else:
        details['facial_symmetry'] = 0.0

    # CHECK 3: GRADIENT SMOOTHNESS
    sobelx = cv2.Sobel(face_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(face_gray, cv2.CV_64F, 0, 1, ksize=3)
    grad   = np.sqrt(sobelx ** 2 + sobely ** 2)
    g_mean = float(grad.mean())
    g_std  = float(grad.std())
    g_cv   = g_std / max(g_mean, 1.0)

    if g_cv < 0.72:
        score += 30
        flags.append(f'Unnaturally smooth gradients (cv={g_cv:.2f}) — AI art signature')
    elif g_cv < 1.05:
        score += 15
        flags.append(f'Low gradient variation (cv={g_cv:.2f})')

    details['gradient_cv'] = float(round(g_cv, 3))

    # CHECK 4: COLOR SATURATION
    hsv      = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
    sat      = hsv[:, :, 1].astype(np.float32)
    sat_mean = float(sat.mean())
    sat_std  = float(sat.std())

    if sat_mean > 140 and sat_std < 50:
        score += 28
        flags.append(f'Oversaturated uniform colors (sat={sat_mean:.0f}) — AI art')
    elif sat_mean > 115 and sat_std < 38:
        score += 14
        flags.append(f'High uniform saturation (sat={sat_mean:.0f})')

    details['saturation_mean'] = float(round(sat_mean, 1))
    details['saturation_std']  = float(round(sat_std, 1))

    # CHECK 5: SKIN NATURALNESS
    skin_mask  = cv2.inRange(hsv,
        np.array([0, 15, 60]),
        np.array([35, 200, 255])
    )
    skin_ratio = float(skin_mask.sum() / 255 / max(skin_mask.size, 1))

    if faces_detected > 0 and skin_ratio < 0.04:
        score += 15
        flags.append(f'Abnormal skin distribution ({skin_ratio * 100:.1f}%)')
    elif skin_ratio > 0.88:
        score += 18
        flags.append(f'Unnaturally uniform skin ({skin_ratio * 100:.1f}%)')

    details['skin_ratio'] = float(round(skin_ratio * 100, 1))

    # CHECK 6: DCT FREQUENCY
    try:
        dct_img    = cv2.dct(np.float32(gray))
        hf         = float(np.abs(dct_img[h // 2:, w // 2:]).mean())
        lf         = float(np.abs(dct_img[:h // 4, :w // 4]).mean())
        freq_ratio = hf / (lf + 1e-6)
        if freq_ratio > 0.075:
            score += 15
            flags.append(f'DCT frequency anomaly (ratio={freq_ratio:.3f})')
        elif freq_ratio > 0.045:
            score += 7
        details['dct_ratio'] = float(round(freq_ratio, 4))
    except:
        details['dct_ratio'] = 0.0

    # CHECK 7: ELA
    ela_score_val   = 0.0
    ela_heatmap_b64 = ''

    if img_bytes is not None:
        try:
            from PIL import Image, ImageChops
            pil_orig = Image.open(io.BytesIO(img_bytes)).convert('RGB')
            buf90 = io.BytesIO()
            pil_orig.save(buf90, 'JPEG', quality=90)
            buf90.seek(0)
            pil_90 = Image.open(buf90).convert('RGB')
            if pil_orig.size != pil_90.size:
                pil_90 = pil_90.resize(pil_orig.size)
            ela_diff = ImageChops.difference(pil_orig, pil_90)
            ela_arr  = np.array(ela_diff, dtype=np.float32)
            ela_mean = float(ela_arr.mean())
            ela_std  = float(ela_arr.std())
            ela_score_val = float(round(ela_mean * 12, 1))

            if ela_mean > 2.8 and ela_std > 3.5:
                score += 22
                flags.append(f'High ELA — manipulation detected (mean={ela_mean:.1f})')
            elif ela_mean > 1.6:
                score += 10
                flags.append(f'Moderate ELA anomaly (mean={ela_mean:.1f})')

            amplified = np.clip(ela_arr * 20, 0, 255).astype(np.uint8)
            if len(amplified.shape) == 3:
                gray_amp = cv2.cvtColor(amplified, cv2.COLOR_RGB2GRAY)
            else:
                gray_amp = amplified
            heatmap = cv2.applyColorMap(gray_amp, cv2.COLORMAP_JET)
            _, hm_buf = cv2.imencode('.jpg', heatmap, [cv2.IMWRITE_JPEG_QUALITY, 85])
            ela_heatmap_b64 = base64.b64encode(hm_buf).decode('utf-8')

            details['ela_mean'] = float(round(ela_mean, 2))
            details['ela_std']  = float(round(ela_std, 2))
        except Exception as e:
            details['ela_error'] = str(e)[:50]

    # FINAL SCORE
    score = float(min(100.0, score))

    if score >= 42:
        verdict = 'FAKE'
        risk    = 'HIGH' if score >= 65 else 'MEDIUM'
    elif score >= 28:
        verdict = 'SUSPICIOUS'
        risk    = 'MEDIUM'
    else:
        verdict = 'REAL'
        risk    = 'LOW'

    confidence = float(round(score if verdict != 'REAL' else 100 - score, 1))
    dna = compute_phash(gray)

    # Ensure all values are JSON serializable
    clean_details = {}
    for k, v in details.items():
        if isinstance(v, (np.floating, np.integer)):
            clean_details[k] = float(v)
        else:
            clean_details[k] = v

    return {
        'verdict':         verdict,
        'deepfake_score':  float(round(score, 1)),
        'faces_detected':  faces_detected,
        'confidence':      confidence,
        'risk_level':      risk,
        'ela_score':       ela_score_val,
        'dna_fingerprint': dna,
        'ela_heatmap':     ela_heatmap_b64,
        'flags':           flags,
        'details':         clean_details
    }


def compute_phash(gray):
    try:
        resized  = cv2.resize(gray, (32, 32))
        dct      = cv2.dct(np.float32(resized))
        dct_low  = dct[:8, :8]
        med      = float(np.median(dct_low))
        bits     = (dct_low > med).flatten().tolist()
        hash_int = int(''.join(['1' if b else '0' for b in bits]), 2)
        return hex(hash_int)[2:18].upper().zfill(16)
    except:
        return 'N/A'