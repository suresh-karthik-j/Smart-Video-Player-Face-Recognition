"""
Smart Video Player with Face/Eye Monitoring
--------------------------------------------
- Login page (username: suresh / password: suresh123)
- Upload page: pick a video from your laptop, see list of uploaded videos
- Player page: plays the chosen video. A hidden webcam monitor watches your
  face. If your eyes are closed OR you look away from the screen (no face
  detected) for a short moment, the video pauses automatically. It resumes
  automatically when you look back with your eyes open.

Run:
    pip install -r requirements.txt
    python app.py

Then open: http://127.0.0.1:5000
"""

import os
import time
import threading
from functools import wraps

import cv2
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, Response, jsonify, flash
)
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------------
# Basic config
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB max upload

USERNAME = "suresh"
PASSWORD = "suresh123"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped


# --------------------------------------------------------------------------
# Face / Eye monitor (runs on the webcam, shared across requests)
# --------------------------------------------------------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
)


class Monitor:
    """Owns the webcam and continuously decides whether the video should
    be paused (eyes closed / face not visible) or playing (face + eyes
    visible)."""

    def __init__(self):
        self.cap = None
        self.lock = threading.Lock()
        self.running = False
        self.pause = True          # start paused until a face is confirmed
        self.reason = "starting"
        self.last_frame = None

        # debounce counters so a single missed frame doesn't cause flicker
        self.away_streak = 0
        self.closed_streak = 0
        self.ok_streak = 0
        self.AWAY_THRESHOLD = 8     # ~ frames of no-face before pausing
        self.CLOSED_THRESHOLD = 6   # ~ frames of closed-eyes before pausing
        self.RESUME_THRESHOLD = 4   # ~ frames of good state before resuming

    def start(self):
        with self.lock:
            if self.running:
                return
            self.cap = cv2.VideoCapture(0)
            self.running = True
            self.away_streak = 0
            self.closed_streak = 0
            self.ok_streak = 0
            self.pause = True
            self.reason = "starting"

    def stop(self):
        with self.lock:
            self.running = False
            if self.cap is not None:
                self.cap.release()
                self.cap = None

    def _process(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
        )

        if len(faces) == 0:
            # no face -> looking away / left the screen
            self.away_streak += 1
            self.closed_streak = 0
            self.ok_streak = 0
            if self.away_streak >= self.AWAY_THRESHOLD:
                self.pause = True
                self.reason = "Looking away / no face detected"
            return frame

        # take the largest face
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]

        eyes = eye_cascade.detectMultiScale(
            roi_gray, scaleFactor=1.1, minNeighbors=8, minSize=(20, 20)
        )
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 2)

        self.away_streak = 0

        if len(eyes) == 0:
            self.closed_streak += 1
            self.ok_streak = 0
            if self.closed_streak >= self.CLOSED_THRESHOLD:
                self.pause = True
                self.reason = "Eyes closed"
        else:
            self.ok_streak += 1
            self.closed_streak = 0
            if self.ok_streak >= self.RESUME_THRESHOLD:
                self.pause = False
                self.reason = "Watching"

        return frame

    def frames(self):
        """Generator that yields MJPEG-encoded frames for the /video_feed
        route, updating self.pause as it goes."""
        self.start()
        while self.running:
            with self.lock:
                if self.cap is None:
                    break
                ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            frame = self._process(frame)

            label = "PLAY" if not self.pause else "PAUSE"
            color = (0, 200, 0) if not self.pause else (0, 0, 255)
            cv2.putText(frame, f"{label}: {self.reason}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            ret, buf = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            self.last_frame = buf.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + self.last_frame + b"\r\n")
            time.sleep(0.03)  # ~30 fps cap


monitor = Monitor()


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("upload"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        uname = request.form.get("username", "")
        pwd = request.form.get("password", "")
        if uname == USERNAME and pwd == PASSWORD:
            session["logged_in"] = True
            session["username"] = uname
            return redirect(url_for("upload"))
        error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    monitor.stop()
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("video_file")
        if file is None or file.filename == "":
            flash("Please choose a video file first.")
            return redirect(url_for("upload"))
        if not allowed_file(file.filename):
            flash("Unsupported file type. Allowed: mp4, avi, mov, mkv, webm")
            return redirect(url_for("upload"))
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        flash(f"Uploaded '{filename}' successfully.")
        return redirect(url_for("upload"))

    videos = sorted(os.listdir(app.config["UPLOAD_FOLDER"]))
    videos = [v for v in videos if allowed_file(v)]
    return render_template("upload.html", videos=videos, username=session.get("username"))


@app.route("/player/<path:filename>")
@login_required
def player(filename):
    safe_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(safe_path):
        flash("Video not found.")
        return redirect(url_for("upload"))
    monitor.start()
    return render_template("player.html", filename=filename)


@app.route("/video_feed")
@login_required
def video_feed():
    return Response(monitor.frames(),
                     mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
@login_required
def status():
    return jsonify({"pause": monitor.pause, "reason": monitor.reason})


@app.route("/stop_monitor", methods=["POST"])
@login_required
def stop_monitor():
    monitor.stop()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
