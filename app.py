import os
import json
import uuid
import csv
import socket
import io
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session

from questions import get_quiz_questions, grade_answers, BIS_QUESTIONS

app = Flask(__name__)
app.secret_key = "bis_quiz_secret_key_2026_super_secure"

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PARTICIPANTS_FILE = os.path.join(DATA_DIR, "participants.json")
CSV_EXPORT_FILE = os.path.join(DATA_DIR, "participants_scores.csv")
HOST_SUMMARY_FILE = os.path.join(DATA_DIR, "host_summary_report.txt")

# In-memory storage with file backup
def load_participants():
    if os.path.exists(PARTICIPANTS_FILE):
        try:
            with open(PARTICIPANTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_participants(data):
    with open(PARTICIPANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Always keep CSV and Host Summary synchronized!
    export_csv(data)
    generate_host_summary(data)

def format_seconds(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}m {secs:02d}s"

def export_csv(participants_dict):
    # Sort participants by total_points DESC, time_spent_seconds ASC
    completed = [p for p in participants_dict.values() if p.get("status") == "Completed"]
    completed.sort(key=lambda x: (-x.get("total_points", 0), x.get("time_spent_seconds", 9999)))

    fieldnames = [
        "Rank",
        "Participant Name",
        "Phone Number",
        "College ID",
        "Total Points",
        "Correct Answers (out of 30)",
        "Base Points",
        "Speed Bonus Points",
        "Time Taken",
        "Time Taken (Seconds)",
        "Submitted At"
    ]

    with open(CSV_EXPORT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        for rank, p in enumerate(completed, 1):
            writer.writerow([
                rank,
                p.get("name", ""),
                p.get("phone", ""),
                p.get("college_id", ""),
                p.get("total_points", 0),
                f"{p.get('correct_count', 0)} / {p.get('total_questions', 30)}",
                p.get("base_points", 0),
                p.get("speed_bonus", 0),
                p.get("time_taken_formatted", ""),
                p.get("time_spent_seconds", 0),
                p.get("submitted_at_formatted", "")
            ])

def generate_host_summary(participants_dict):
    completed = [p for p in participants_dict.values() if p.get("status") == "Completed"]
    completed.sort(key=lambda x: (-x.get("total_points", 0), x.get("time_spent_seconds", 9999)))
    
    total_reg = len(participants_dict)
    total_comp = len(completed)
    avg_score = (sum(p.get("total_points", 0) for p in completed) / total_comp) if total_comp else 0

    lines = []
    lines.append("==========================================================")
    lines.append("        BUREAU OF INDIAN STANDARDS (BIS) QUIZ REPORT      ")
    lines.append("==========================================================")
    lines.append(f"Generated On       : {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    lines.append(f"Total Participants : {total_reg}")
    lines.append(f"Completed Exams    : {total_comp}")
    lines.append(f"Average Score      : {avg_score:.1f} pts")
    if completed:
        top = completed[0]
        lines.append(f"Top Scorer         : {top.get('name')} ({top.get('college_id')}) - {top.get('total_points')} pts")
    lines.append("----------------------------------------------------------")
    lines.append(f"{'RANK':<6}{'NAME':<24}{'COLLEGE ID':<16}{'SCORE':<8}{'CORRECT':<10}{'TIME TAKEN'}")
    lines.append("----------------------------------------------------------")

    for rank, p in enumerate(completed, 1):
        name = p.get('name', '')[:22]
        cid = p.get('college_id', '')[:14]
        pts = p.get('total_points', 0)
        corr = f"{p.get('correct_count', 0)}/30"
        time_str = p.get('time_taken_formatted', '')
        lines.append(f"{rank:<6}{name:<24}{cid:<16}{pts:<8}{corr:<10}{time_str}")

    lines.append("==========================================================")
    
    with open(HOST_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

PUBLIC_URL_FILE = os.path.join(DATA_DIR, "public_url.txt")

def get_public_url():
    """Reads active Cloudflare Tunnel public URL if present"""
    if os.path.exists(PUBLIC_URL_FILE):
        try:
            with open(PUBLIC_URL_FILE, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url.startswith("http"):
                    return url
        except Exception:
            pass
    return None

def ensure_tunnel():
    """Starts cloudflared tunnel in background if not already started"""
    import threading
    import subprocess
    import re
    import time

    def _worker():
        bin_path = os.path.join(DATA_DIR, "cloudflared.exe")
        if not os.path.exists(bin_path):
            return
        # Test if public url is already valid
        curr = get_public_url()
        if curr:
            try:
                import requests
                r = requests.get(curr, timeout=3)
                if r.status_code == 200:
                    return # Already working!
            except Exception:
                pass

        cmd = [bin_path, "tunnel", "--url", "http://127.0.0.1:5000"]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            while True:
                line = proc.stderr.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                match = url_pattern.search(line)
                if match:
                    found_url = match.group(0)
                    with open(PUBLIC_URL_FILE, "w", encoding="utf-8") as f:
                        f.write(found_url)
                    print(f"\n[UNIVERSAL TUNNEL ONLINE] {found_url}\n")
                    break
        except Exception as e:
            print("Tunnel launch notice:", e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

ensure_tunnel()

def get_local_ip():
    """Detects primary local network IP address for mobile devices to connect via QR code"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def get_qr_base64(url):
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        return ""

# Initialize files
participants_db = load_participants()
export_csv(participants_db)
generate_host_summary(participants_db)

# ----------------- ROUTES ----------------- #

@app.route("/")
def index():
    """Participant landing & registration page"""
    return render_template("index.html")

@app.route("/api/register", methods=["POST"])
def register():
    """Registers participant with Name, Phone, and College ID"""
    data = request.json or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    college_id = data.get("college_id", "").strip()

    if not name or not phone or not college_id:
        return jsonify({"success": False, "message": "All fields (Name, Phone Number, College ID) are required."}), 400

    participants = load_participants()

    # Create participant session
    participant_id = str(uuid.uuid4())
    questions, question_ids = get_quiz_questions(30)

    now_iso = datetime.now().isoformat()
    now_formatted = datetime.now().strftime("%I:%M:%S %p")

    participant_record = {
        "id": participant_id,
        "name": name,
        "phone": phone,
        "college_id": college_id,
        "registered_at": now_iso,
        "registered_at_formatted": now_formatted,
        "status": "In Progress",
        "question_ids": question_ids,
        "sanitized_questions": questions,
        "total_questions": len(questions),
        "total_time_seconds": 1200, # 20 minutes
        "start_timestamp": datetime.now().timestamp(),
        "total_points": 0,
        "correct_count": 0,
        "speed_bonus": 0,
        "time_spent_seconds": 0
    }

    participants[participant_id] = participant_record
    save_participants(participants)

    session["participant_id"] = participant_id

    return jsonify({
        "success": True,
        "participant_id": participant_id,
        "redirect_url": url_for("quiz_page")
    })

@app.route("/quiz")
def quiz_page():
    """The 20-minute 30-question interactive quiz exam page"""
    participant_id = session.get("participant_id") or request.args.get("id")
    if not participant_id:
        return redirect(url_for("index"))

    participants = load_participants()
    participant = participants.get(participant_id)
    if not participant:
        return redirect(url_for("index"))

    if participant.get("status") == "Completed":
        return redirect(url_for("leaderboard_page", id=participant_id))

    return render_template("quiz.html", participant=participant)

@app.route("/api/quiz-data/<participant_id>")
def get_quiz_data(participant_id):
    """Returns the 30 randomized questions for this participant session"""
    participants = load_participants()
    participant = participants.get(participant_id)
    if not participant:
        return jsonify({"success": False, "message": "Participant not found"}), 404

    # Calculate remaining time in seconds based on server start time
    elapsed = int(datetime.now().timestamp() - participant.get("start_timestamp", datetime.now().timestamp()))
    total_time = participant.get("total_time_seconds", 1200)
    remaining = max(0, total_time - elapsed)

    return jsonify({
        "success": True,
        "participant": {
            "name": participant["name"],
            "college_id": participant["college_id"]
        },
        "questions": participant["sanitized_questions"],
        "total_questions": len(participant["sanitized_questions"]),
        "total_time_seconds": total_time,
        "remaining_seconds": remaining
    })

@app.route("/api/submit-quiz", methods=["POST"])
def submit_quiz():
    """Submits the exam, calculates points with speed bonus, and updates leaderboard"""
    data = request.json or {}
    participant_id = data.get("participant_id")
    answers = data.get("answers", {}) # { "q_id": option_index }
    time_spent_client = data.get("time_spent_seconds", 0)

    participants = load_participants()
    participant = participants.get(participant_id)
    if not participant:
        return jsonify({"success": False, "message": "Participant record not found"}), 404

    if participant.get("status") == "Completed":
        return jsonify({
            "success": True,
            "message": "Quiz was already submitted",
            "redirect_url": url_for("leaderboard_page", id=participant_id)
        })

    # Calculate time spent on server
    start_ts = participant.get("start_timestamp", datetime.now().timestamp())
    server_time_spent = int(datetime.now().timestamp() - start_ts)
    # Clamp time between 0 and 1200
    actual_time_spent = min(1200, max(0, min(server_time_spent, int(time_spent_client))))

    # Grade the exam
    question_ids = participant.get("question_ids", [])
    result = grade_answers(question_ids, answers, actual_time_spent, max_time_seconds=1200)

    now = datetime.now()
    participant["status"] = "Completed"
    participant["submitted_at"] = now.isoformat()
    participant["submitted_at_formatted"] = now.strftime("%I:%M:%S %p")
    participant["time_spent_seconds"] = actual_time_spent
    participant["time_taken_formatted"] = format_seconds(actual_time_spent)
    participant["correct_count"] = result["correct_count"]
    participant["base_points"] = result["base_points"]
    participant["speed_bonus"] = result["speed_bonus"]
    participant["total_points"] = result["total_points"]
    participant["result_details"] = result["details"]

    participants[participant_id] = participant
    save_participants(participants)

    return jsonify({
        "success": True,
        "result": {
            "total_points": result["total_points"],
            "base_points": result["base_points"],
            "speed_bonus": result["speed_bonus"],
            "correct_count": result["correct_count"],
            "total_questions": result["total_questions"],
            "time_taken": format_seconds(actual_time_spent)
        },
        "redirect_url": url_for("leaderboard_page", id=participant_id)
    })

@app.route("/leaderboard")
def leaderboard_page():
    """Displays the live Leaderboard with ranks, points, and participant highlights"""
    participant_id = request.args.get("id") or session.get("participant_id", "")
    return render_template("leaderboard.html", highlight_id=participant_id)

@app.route("/api/leaderboard")
def api_leaderboard():
    """API endpoint providing current sorted leaderboard and statistics"""
    participants = load_participants()
    completed = [p for p in participants.values() if p.get("status") == "Completed"]
    # Sort by total points DESC, then by time taken ASC (faster gets higher rank on tie)
    completed.sort(key=lambda x: (-x.get("total_points", 0), x.get("time_spent_seconds", 9999)))

    leaderboard = []
    for rank, p in enumerate(completed, 1):
        leaderboard.append({
            "rank": rank,
            "id": p.get("id"),
            "name": p.get("name"),
            "college_id": p.get("college_id"),
            "total_points": p.get("total_points", 0),
            "base_points": p.get("base_points", 0),
            "speed_bonus": p.get("speed_bonus", 0),
            "correct_count": p.get("correct_count", 0),
            "total_questions": p.get("total_questions", 30),
            "time_taken_formatted": p.get("time_taken_formatted", "00m 00s"),
            "submitted_at": p.get("submitted_at_formatted", "")
        })

    return jsonify({
        "success": True,
        "total_participants": len(participants),
        "total_completed": len(completed),
        "leaderboard": leaderboard
    })

@app.route("/host")
def host_dashboard():
    """Host / Administrator Dashboard with QR Code, live controls & export options"""
    local_ip = get_local_ip()
    port = 5000
    public_url = get_public_url()
    
    # Candidate Quiz Join URL
    host_join_url = public_url if public_url else f"http://{local_ip}:{port}/"
    qr_data_url = get_qr_base64(host_join_url)

    # Public Host Dashboard URL (for co-hosts / organizers)
    if public_url:
        public_host_url = f"{public_url.rstrip('/')}/host"
    else:
        public_host_url = f"http://{local_ip}:{port}/host"
    host_qr_data_url = get_qr_base64(public_host_url)

    return render_template(
        "host.html",
        local_ip=local_ip,
        port=port,
        host_join_url=host_join_url,
        public_host_url=public_host_url,
        public_url=public_url,
        qr_data_url=qr_data_url,
        host_qr_data_url=host_qr_data_url
    )

@app.route("/api/host-data")
def api_host_data():
    """Returns comprehensive host dashboard real-time data"""
    participants = load_participants()
    completed = [p for p in participants.values() if p.get("status") == "Completed"]
    in_progress = [p for p in participants.values() if p.get("status") == "In Progress"]
    completed.sort(key=lambda x: (-x.get("total_points", 0), x.get("time_spent_seconds", 9999)))

    avg_score = (sum(p.get("total_points", 0) for p in completed) / len(completed)) if completed else 0
    top_score = completed[0].get("total_points", 0) if completed else 0

    return jsonify({
        "success": True,
        "stats": {
            "total_registered": len(participants),
            "total_completed": len(completed),
            "in_progress": len(in_progress),
            "avg_score": round(avg_score, 1),
            "top_score": top_score
        },
        "participants": [
            {
                "rank": idx + 1,
                "id": p.get("id"),
                "name": p.get("name"),
                "phone": p.get("phone"),
                "college_id": p.get("college_id"),
                "status": p.get("status"),
                "total_points": p.get("total_points", 0),
                "correct_count": p.get("correct_count", 0),
                "speed_bonus": p.get("speed_bonus", 0),
                "time_taken": p.get("time_taken_formatted", "-"),
                "submitted_at": p.get("submitted_at_formatted", "-")
            }
            for idx, p in enumerate(completed)
        ]
    })

@app.route("/api/export-csv")
def download_csv():
    """Direct CSV download route for Host"""
    participants = load_participants()
    export_csv(participants)
    return send_file(
        CSV_EXPORT_FILE,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"bis_quiz_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

@app.route("/api/export-summary")
def download_summary():
    """Direct Host text summary download route"""
    participants = load_participants()
    generate_host_summary(participants)
    return send_file(
        HOST_SUMMARY_FILE,
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"bis_quiz_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )

@app.route("/api/reset-data", methods=["POST"])
def reset_data():
    """Allows host to clear test entries before launching live quiz"""
    save_participants({})
    return jsonify({"success": True, "message": "All participant data has been reset."})

@app.route("/api/update-join-url", methods=["POST"])
def update_join_url():
    """Allows host to generate QR code for a custom URL (e.g. ngrok / custom domain)"""
    data = request.json or {}
    custom_url = data.get("url", "").strip()
    if not custom_url:
        return jsonify({"success": False, "message": "URL cannot be empty"}), 400
    
    qr_data = get_qr_base64(custom_url)
    return jsonify({"success": True, "qr_data_url": qr_data, "url": custom_url})

if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 60)
    print(" BUREAU OF INDIAN STANDARDS (BIS) QUIZ WEB APP")
    print("=" * 60)
    print(f" Participant Join URL : http://{ip}:5000/")
    print(f" Host Dashboard URL   : http://{ip}:5000/host")
    print(f" Localhost Access     : http://127.0.0.1:5000/")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
