# 🎬 AI Based Smart Video Player with Face & Eye Recognition

An AI-powered video player built with **Flask** and **OpenCV** that automatically **pauses video playback when the viewer looks away or closes their eyes**, and **resumes playback** when the viewer looks back at the screen with their eyes open.

This project is based on the academic project *"AI Based Smart Video Player With Face Recognition"* (Kings College of Engineering, Anna University) and re-implemented as a working web application.

---

## ✨ Features

- 🔐 **Login system** — secure access with username & password
- 📂 **Upload videos** directly from your laptop
- 🎥 **Play videos** with a normal HTML5 video player (play, pause, seek, volume)
- 👁️ **Real-time face & eye detection** using OpenCV Haar Cascades via webcam
- ⏸️ **Auto-pause** when:
  - The viewer looks away (no face detected)
  - The viewer's eyes are closed
- ▶️ **Auto-resume** when the viewer looks back with eyes open
- 🖥️ Live webcam monitor preview with face/eye bounding boxes

---

## 🛠️ Tech Stack

| Component        | Technology            |
|-------------------|------------------------|
| Backend           | Python, Flask          |
| Computer Vision   | OpenCV (Haar Cascades) |
| Frontend          | HTML, CSS, Bootstrap 5 |
| Video Streaming   | MJPEG (webcam), HTML5 `<video>` |

---

## 📁 Folder Structure
smart_video_player/
├── app.py # Main Flask application
├── requirements.txt # Python dependencies
├── static/
│ ├── css/
│ │ └── style.css
│ └── uploads/ # Uploaded videos are stored here
└── templates/
├── login.html
├── upload.html
└── player.html

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/smart-video-player-face-recognition.git
cd smart-video-player-face-recognition
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
```
Activate it:
```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

### 5. Open in browser
http://127.0.0.1:5000

---

## 🔑 Login Credentials

| Username | Password  |
|----------|-----------|
| suresh   | suresh123 |

---

## ▶️ How to Use

1. Log in with the credentials above.
2. Click **Choose File** to select a video from your laptop and click **Upload**.
3. Click on the uploaded video name to open the player.
4. Allow camera access when prompted (needed for face/eye monitoring).
5. Click the native **Play** button on the video.
6. Try closing your eyes or looking away — the video will automatically pause.
7. Look back at the screen with eyes open — the video will resume automatically.

---

## 🧠 How It Works

1. The webcam continuously captures frames.
2. Each frame is processed with **Haar Cascade Classifiers**:
   - `haarcascade_frontalface_default.xml` → detects the face
   - `haarcascade_eye_tree_eyeglasses.xml` → detects eyes within the face region
3. Based on several consecutive frames (to avoid flickering), the system decides whether the viewer is:
   - **Watching** (face + eyes visible) → video plays
   - **Eyes closed** → video pauses
   - **Looking away / no face** → video pauses
4. The browser polls a `/status` API endpoint every 0.5 seconds and calls the video's native `play()`/`pause()` methods accordingly.

---

## 📌 Notes

- The webcam must not be in use by another application (Zoom, Google Meet, etc.) while running this project.
- Works best in good lighting with the face reasonably facing the camera.
- All face/eye detection runs **locally** — no external APIs or internet connection required at runtime.

---

## 🚀 Future Enhancements

- Emotion detection based content recommendations
- Gesture-based playback control
- Age/gender based content filtering
- Cloud deployment with user accounts

---

## 👨‍💻 Author

**Suresh Karthik J**
B.E. Computer Science and Engineering, Kings College of Engineering, Anna University

---

## 📄 License

This project is for educational purposes.
