import math
import os
import tempfile
from typing import Optional
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mediapipe as mp
from datetime import datetime

app = FastAPI(title="SPRINT.AI Biomechanics API")

# CORS configuration - allows frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
POSE_LMK = mp_pose.PoseLandmark

def angle_3pt(a, b, c):
    """Calculate angle at point b formed by points a-b-c"""
    ax, ay = a
    bx, by = b
    cx, cy = c
    v1 = np.array([ax - bx, ay - by])
    v2 = np.array([cx - bx, cy - by])
    denom = (np.linalg.norm(v1) * np.linalg.norm(v2)) + 1e-9
    cosang = np.clip(np.dot(v1, v2) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))

def smooth(x, k=5):
    """Smooth time series data"""
    if len(x) < 3:
        return np.array(x, dtype=float)
    k = max(1, int(k))
    kernel = np.ones(k) / k
    return np.convolve(x, kernel, mode="same")

def local_minima(y, w=3):
    """Find local minima in signal (for contact detection)"""
    mins = []
    n = len(y)
    for i in range(w, n - w):
        window = y[i - w:i + w + 1]
        if y[i] == min(window):
            mins.append(i)
    return mins

def derive_series(x, fps):
    """Calculate velocity from position"""
    v = np.diff(x) * fps
    return np.concatenate([[0.0], v])

def mid(p1, p2):
    """Calculate midpoint"""
    return ((p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5)

def extract_pose_series(video_path: str):
    """Extract pose landmarks from video using MediaPipe"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    hips_x, hips_y = [], []
    la_y, ra_y = [], []
    lknee_pts, rknee_pts = [], []
    lankle_pts, rankle_pts = [], []
    ltoe_pts, rtoe_pts = [], []
    lhip_pts, rhip_pts = [], []
    lsh_pts, rsh_pts = [], []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark

                def xy(idx):
                    return (lm[idx].x * width, lm[idx].y * height)

                lhip = xy(POSE_LMK.LEFT_HIP.value)
                rhip = xy(POSE_LMK.RIGHT_HIP.value)
                hipm = mid(lhip, rhip)
                hips_x.append(hipm[0])
                hips_y.append(hipm[1])

                lankle = xy(POSE_LMK.LEFT_ANKLE.value)
                rankle = xy(POSE_LMK.RIGHT_ANKLE.value)
                la_y.append(lankle[1])
                ra_y.append(rankle[1])

                lknee = xy(POSE_LMK.LEFT_KNEE.value)
                rknee = xy(POSE_LMK.RIGHT_KNEE.value)
                lknee_pts.append(lknee)
                rknee_pts.append(rknee)

                ltoe = xy(POSE_LMK.LEFT_FOOT_INDEX.value)
                rtoe = xy(POSE_LMK.RIGHT_FOOT_INDEX.value)
                ltoe_pts.append(ltoe)
                rtoe_pts.append(rtoe)

                lankle_pts.append(lankle)
                rankle_pts.append(rankle)
                lhip_pts.append(lhip)
                rhip_pts.append(rhip)

                lsh = xy(POSE_LMK.LEFT_SHOULDER.value)
                rsh = xy(POSE_LMK.RIGHT_SHOULDER.value)
                lsh_pts.append(lsh)
                rsh_pts.append(rsh)

            frame_count += 1

    cap.release()

    return {
        "fps": fps,
        "frames": len(hips_x),
        "width": width,
        "height": height,
        "hips_x": np.array(hips_x, dtype=float),
        "hips_y": np.array(hips_y, dtype=float),
        "la_y": np.array(la_y, dtype=float),
        "ra_y": np.array(ra_y, dtype=float),
        "lknee": np.array(lknee_pts, dtype=float),
        "rknee": np.array(rknee_pts, dtype=float),
        "lankle": np.array(lankle_pts, dtype=float),
        "rankle": np.array(rankle_pts, dtype=float),
        "ltoe": np.array(ltoe_pts, dtype=float),
        "rtoe": np.array(rtoe_pts, dtype=float),
        "lhip": np.array(lhip_pts, dtype=float),
        "rhip": np.array(rhip_pts, dtype=float),
        "lsh": np.array(lsh_pts, dtype=float),
        "rsh": np.array(rsh_pts, dtype=float),
    }

def compute_metrics(series: dict, distance_label: str, pixels_per_meter: float):
    """Compute biomechanics metrics from pose series"""
    fps = series["fps"]
    n = series["frames"]
    time_taken = n / max(fps, 1e-6)

    # Hip horizontal displacement for speed
    hx = smooth(series["hips_x"])
    vx_pixels = derive_series(hx, fps)
    vx_mps = np.abs(vx_pixels) / pixels_per_meter

    max_speed = float(np.max(vx_mps))

    # Reaction time (first significant movement)
    thr = 0.5  # m/s threshold
    rt_idx = int(np.argmax(vx_mps > thr)) if np.any(vx_mps > thr) else 0
    reaction_time = rt_idx / max(fps, 1e-6)

    # Acceleration phase (0-30m if available)
    disp_m = (hx - hx[0]) / pixels_per_meter
    idx_30 = np.where(disp_m >= 30.0)[0]
    if len(idx_30) > 0:
        t_30 = idx_30[0] / max(fps, 1e-6)
        accel_0_30 = 30.0 / t_30 if t_30 > 0 else 0.0
    else:
        accel_0_30 = None

    # Step detection from ankle minima
    la = smooth(series["la_y"])
    ra = smooth(series["ra_y"])
    l_contacts = local_minima(la, w=3)
    r_contacts = local_minima(ra, w=3)
    contacts = sorted(l_contacts + r_contacts)

    steps = max(0, len(contacts) - 1)
    cadence_sps = steps / time_taken if time_taken > 0 else 0.0
    cadence_spm = cadence_sps * 60.0

    # Stride length from consecutive toe positions
    def stride_lengths(toe):
        idxs = local_minima(smooth(toe[:,1]), w=3)
        sl = []
        for i in range(1, len(idxs)):
            i0, i1 = idxs[i-1], idxs[i]
            dx = abs(toe[i1,0] - toe[i0,0])
            sl.append(dx / pixels_per_meter)
        return sl

    sl_left = stride_lengths(series["ltoe"])
    sl_right = stride_lengths(series["rtoe"])
    all_sl = sl_left + sl_right
    stride_length = float(np.mean(all_sl)) if len(all_sl) > 0 else None

    # Ground contact and flight times
    gct_ms = None
    flight_ms = None
    if len(contacts) >= 2:
        window = 2
        contact_frames = 0
        for ci in contacts:
            start = max(0, ci - window)
            end = min(n - 1, ci + window)
            contact_frames += (end - start + 1)
        mean_contact = contact_frames / max(1, len(contacts))
        step_frames = n / max(1, steps) if steps > 0 else 0
        mean_flight = step_frames - mean_contact if step_frames > 0 else 0
        gct_ms = (mean_contact / max(fps, 1e-6)) * 1000.0
        flight_ms = (mean_flight / max(fps, 1e-6)) * 1000.0

    # Knee drive angle
    def knee_drive(lhip, lknee, lankle):
        angs = []
        for i in range(len(lhip)):
            angs.append(angle_3pt(lhip[i], lknee[i], lankle[i]))
        return float(np.nanmin(angs)) if len(angs) else None

    kd_left = knee_drive(series["lhip"], series["lknee"], series["lankle"])
    kd_right = knee_drive(series["rhip"], series["rknee"], series["rankle"])
    knee_drive_angle = float(np.nanmin([kd_left, kd_right])) if kd_left and kd_right else None

    # Torso lean
    torso_lean_deg = None
    if n > 5:
        mid_i = n // 2
        sh_mid = mid(series["lsh"][mid_i], series["rsh"][mid_i])
        hp_mid = mid(series["lhip"][mid_i], series["rhip"][mid_i])
        vx, vy = (sh_mid[0] - hp_mid[0], sh_mid[1] - hp_mid[1])
        dot = vy * (-1)
        mag = math.sqrt(vx*vx + vy*vy)
        cosang = np.clip(dot / (mag + 1e-9), -1.0, 1.0)
        torso_lean_deg = float(np.degrees(np.arccos(cosang)))

    # Fatigue index
    q = max(1, int(0.2 * n))
    s1 = np.mean(vx_mps[:q])
    s2 = np.mean(vx_mps[-q:])
    drop_speed = ((s1 - s2) / s1) * 100.0 if s1 > 1e-6 else 0.0
    fatigue_index = max(0.0, drop_speed)

    # Form score calculation
    score = 100.0
    nominal_stride = {"100m": 2.3, "400m": 2.1, "1km": 1.9, "5km": 1.75}.get(distance_label, 2.0)
    if stride_length:
        score -= min(15.0, abs(stride_length - nominal_stride) / nominal_stride * 15.0)
    if torso_lean_deg:
        score -= min(10.0, max(0.0, torso_lean_deg - 10.0) * 0.5)
    if gct_ms:
        nominal_gct = {"100m": 110, "400m": 125, "1km": 140, "5km": 160}.get(distance_label, 130)
        score -= min(15.0, abs(gct_ms - nominal_gct) / nominal_gct * 15.0)
    score -= min(20.0, fatigue_index * 0.2)
    form_score = max(0, min(100, score))

    # Generate feedback
    feedback = []
    if stride_length:
        if abs(stride_length - nominal_stride) < 0.1:
            feedback.append("Excellent stride length consistency")
        else:
            diff = stride_length - nominal_stride
            feedback.append(f"Stride length {'over' if diff > 0 else 'under'} optimal by {abs(diff):.2f}m")

    if torso_lean_deg and torso_lean_deg < 15:
        feedback.append("Good upright posture maintained")
    elif torso_lean_deg and torso_lean_deg > 20:
        feedback.append("Excessive forward lean detected - work on posture")

    if fatigue_index < 5:
        feedback.append("Strong endurance with minimal speed drop")
    elif fatigue_index > 15:
        feedback.append("Significant fatigue in final phase - improve conditioning")

    if cadence_sps > 4.5:
        feedback.append("High cadence showing good leg turnover")

    # Generate drills
    drills_map = {
        "100m": ["A-skips: 3x20m for knee drive", "Bounding: 4x30m for power", "Core planks: 3x45s"],
        "400m": ["Tempo runs: 3x300m", "Speed endurance: 4x200m", "Core circuit: 15min"],
        "1km": ["Interval training: 6x400m", "Tempo run: 2km", "Hill repeats: 8x200m"],
        "5km": ["Long intervals: 5x1km", "Tempo runs: 4km", "Easy distance: 12km"]
    }
    drills = drills_map.get(distance_label, drills_map["100m"])

    return {
        "time_taken_s": round(time_taken, 2),
        "max_speed_mps": round(max_speed, 2),
        "acceleration_0_30": round(accel_0_30, 2) if accel_0_30 else None,
        "stride_length_m": round(stride_length, 2) if stride_length else None,
        "cadence_sps": round(cadence_sps, 2),
        "cadence_spm": round(cadence_spm, 1),
        "ground_contact_ms": round(gct_ms, 1) if gct_ms else None,
        "flight_time_ms": round(flight_ms, 1) if flight_ms else None,
        "knee_drive_angle": round(knee_drive_angle, 1) if knee_drive_angle else None,
        "torso_lean_deg": round(torso_lean_deg, 1) if torso_lean_deg else None,
        "fatigue_index": round(fatigue_index, 1),
        "form_score": round(form_score, 1),
        "feedback": feedback,
        "drills": drills
    }

@app.get("/")
async def root():
    return {
        "service": "SPRINT.AI Biomechanics API",
        "status": "online",
        "version": "1.0.0"
    }

@app.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    distance: str = Form(...),
    pixels_per_meter: Optional[float] = Form(100.0)
):
    """
    Analyze running video and return biomechanics metrics

    Parameters:
    - file: Video file (mp4, mov, avi)
    - distance: Running distance (100m, 400m, 1km, 5km)
    - pixels_per_meter: Calibration value (default: 100 pixels = 1 meter)
    """
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name

        # Extract pose data
        series = extract_pose_series(temp_path)

        # Compute metrics
        metrics = compute_metrics(series, distance, pixels_per_meter)

        # Clean up
        os.unlink(temp_path)

        return {
            "success": True,
            "distance": distance,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }

    except Exception as e:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
