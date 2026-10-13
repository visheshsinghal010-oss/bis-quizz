# 🇮🇳 Bureau of Indian Standards (BIS) Quiz Application

A full-stack, mobile-friendly interactive quiz web application designed for conducting college and institutional competitions on the **Bureau of Indian Standards (BIS)**.

---

## 🌟 Key Features

1. **Instant QR Code Entry for Participants:**
   - The host projects or prints a generated **QR code**.
   - Students scan the QR code using their smartphone camera or Google Lens to immediately open the registration portal.
   - Form fields:
     - **Full Name**
     - **Phone Number** (10-digit mobile number)
     - **College ID / Roll Number**
     - **"Start 30 Questions Quiz"** button.

2. **30 Randomized BIS Questions:**
   - 35+ verified, authentic multiple-choice questions covering:
     - BIS Act 2016 & History of ISI (1947)
     - Quality Certification Marks: ISI Mark, Hallmarking (HUID 6-digit code), ECO Mark, CRS
     - Indian Standards (IS 456, IS 14543, IS 10500, IS 4151, IS 1893, etc.)
     - World Standards Day (14th October)
     - Standards Clubs in Colleges & Schools, BIS Care App, and Manakonline.
   - Answer keys are secured on the backend to prevent inspect-element cheating.

3. **20-Minute Countdown Timer with Speed Bonus:**
   - Exactly **20 minutes (1200 seconds)** countdown timer.
   - Visual warning pulse when under 3 minutes remain.
   - **Speed-Bonus Scoring:**
     $$\text{Total Points} = (\text{Correct Answers} \times 100) + \text{round}\left(\frac{\text{Remaining Seconds}}{1200} \times 1500 \times \frac{\text{Correct Answers}}{30}\right)$$
     - Students who answer correctly and finish faster receive significant bonus points!
     - Ties in points are broken by completion speed (less time taken ranks higher).
   - **Auto-Submit:** The exam automatically submits when the 20:00 timer reaches 00:00.

4. **Live Leaderboard:**
   - Real-time ranking with Top 3 Podium (🥇 Gold, 🥈 Silver, 🥉 Bronze).
   - Shows Participant Name, College ID, Total Points, Accuracy, Speed Bonus, and Completion Time.
   - Personal scorecard highlights the participant's own rank and breakdown upon completion.
   - Instant search filter by Name or College ID.

5. **Host Control Center & Participant File Sharing:**
   - Real-time Host Dashboard at `/host`.
   - **Automatic Local File:** Every submission automatically logs and synchronizes to:
     - `participants_scores.csv` (Opens in Excel, Google Sheets)
     - `host_summary_report.txt` (Text summary)
   - **One-Click Downloads:**
     - 📥 **Download CSV**: Direct export of full participants roster with scores.
     - 📄 **Download Text Report**: Printable summary report.
     - 📋 **Copy Formatted Summary**: Formats a WhatsApp / Email summary to clipboard with one click.
     - 🗑️ **Reset Data**: Cleans test records before the live event begins.

---

## 🚀 How to Run the Quiz

### Quick Launch on Windows:
Double-click `run_quiz.bat` inside the project folder:
```
C:\Users\Lenovo\.gemini\antigravity\scratch\bis_quiz_app\run_quiz.bat
```

### Or Launch via Terminal:
```powershell
cd C:\Users\Lenovo\.gemini\antigravity\scratch\bis_quiz_app
python app.py
```

### URLs:
- **Participant Quiz Join:** `http://<Your-LAN-IP>:5000/` (or `http://localhost:5000/`)
- **Live Leaderboard:** `http://<Your-LAN-IP>:5000/leaderboard`
- **Host Dashboard & QR Code:** `http://<Your-LAN-IP>:5000/host`

> **Note:** When conducting the quiz in a college classroom or auditorium, connect your computer and students' phones to the same Wi-Fi network or Mobile Hotspot. The Host Dashboard automatically displays your Wi-Fi IP address in the QR code!

---

## 📁 File Structure

```
bis_quiz_app/
│── app.py                    # Flask server with REST APIs & CSV exporter
│── questions.py              # 35+ verified BIS questions & scoring engine
│── test_app.py               # Unit verification suite
│── run_quiz.bat              # One-click Windows starter script
│── participants.json         # Participant storage database
│── participants_scores.csv   # Auto-generated CSV file for host/organizer
│── host_summary_report.txt   # Printable host summary text
│── templates/
│   ├── index.html            # Registration page (Name, Phone, College ID)
│   ├── quiz.html             # 20-min timed 30-question interactive exam
│   ├── leaderboard.html      # Live leaderboard & personal scorecard
│   └── host.html             # Host dashboard with QR code presentation
└── static/
    ├── css/
    │   └── style.css         # Responsive mobile-friendly UI
    └── js/
        ├── quiz.js           # Exam timer, speed tracking, navigation
        ├── leaderboard.js    # Live rankings & auto-refresh
        └── host.js           # Host real-time monitoring & export tools
```
