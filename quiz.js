let questions = [];
let currentIndex = 0;
let answers = {}; // { q_id: option_index }
let markedReviews = new Set();
let timerInterval = null;
let remainingSeconds = 1200; // 20 minutes
let totalSeconds = 1200;
let timeSpentSeconds = 0;
let isSubmitted = false;

document.addEventListener("DOMContentLoaded", async () => {
  // Load cached answers if any
  try {
    const savedAns = localStorage.getItem("bis_quiz_answers_" + PARTICIPANT_ID);
    if (savedAns) answers = JSON.parse(savedAns);
    const savedRev = localStorage.getItem("bis_quiz_review_" + PARTICIPANT_ID);
    if (savedRev) markedReviews = new Set(JSON.parse(savedRev));
  } catch (e) {
    console.error("Storage error", e);
  }

  await loadQuizData();
  setupKeyboardShortcuts();
});

async function loadQuizData() {
  try {
    const res = await fetch(`/api/quiz-data/${PARTICIPANT_ID}`);
    const data = await res.json();
    if (!data.success) {
      alert("Error loading quiz: " + (data.message || "Unknown error"));
      window.location.href = "/";
      return;
    }

    questions = data.questions || [];
    totalSeconds = data.total_time_seconds || 1200;
    remainingSeconds = data.remaining_seconds || 1200;

    renderPalette();
    renderQuestion(0);
    startTimer();
  } catch (err) {
    console.error("Fetch quiz failed", err);
    alert("Failed to connect to quiz server. Please reload.");
  }
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (remainingSeconds > 0) {
      remainingSeconds--;
      timeSpentSeconds = totalSeconds - remainingSeconds;
      updateTimerDisplay();

      // Warning when less than 3 minutes left
      const wrapper = document.getElementById("timerWrapper");
      if (remainingSeconds <= 180 && wrapper) {
        wrapper.classList.add("timer-warning");
      }
    } else {
      clearInterval(timerInterval);
      alert("⏰ Time is up! Your 20-minute exam will now be automatically submitted.");
      finalizeSubmission(true);
    }
  }, 1000);
}

function updateTimerDisplay() {
  const display = document.getElementById("timerDisplay");
  if (!display) return;
  const mins = Math.floor(remainingSeconds / 60);
  const secs = remainingSeconds % 60;
  display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function renderPalette() {
  const grid = document.getElementById("paletteGrid");
  if (!grid) return;
  grid.innerHTML = "";

  questions.forEach((q, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "palette-btn";
    btn.textContent = idx + 1;
    btn.id = `pal_btn_${idx}`;

    if (answers[q.id] !== undefined) {
      btn.classList.add("answered");
    }
    if (markedReviews.has(q.id)) {
      btn.classList.add("review");
    }
    if (idx === currentIndex) {
      btn.classList.add("active");
    }

    btn.onclick = () => jumpToQuestion(idx);
    grid.appendChild(btn);
  });

  updatePaletteCounts();
}

function updatePaletteCounts() {
  const answeredCount = Object.keys(answers).length;
  const reviewCount = markedReviews.size;
  const unansweredCount = questions.length - answeredCount;

  const aEl = document.getElementById("answeredCount");
  const rEl = document.getElementById("reviewCount");
  const uEl = document.getElementById("unansweredCount");

  if (aEl) aEl.textContent = answeredCount;
  if (rEl) rEl.textContent = reviewCount;
  if (uEl) uEl.textContent = unansweredCount;
}

function renderQuestion(idx) {
  if (!questions || questions.length === 0) return;
  if (idx < 0) idx = 0;
  if (idx >= questions.length) idx = questions.length - 1;
  currentIndex = idx;

  const q = questions[idx];
  document.getElementById("qBadge").textContent = `Question ${idx + 1} of ${questions.length}`;
  document.getElementById("qStatement").textContent = q.question;

  const optionsContainer = document.getElementById("optionsContainer");
  optionsContainer.innerHTML = "";

  const prefixes = ["A", "B", "C", "D"];
  q.options.forEach((optText, optIdx) => {
    const item = document.createElement("div");
    item.className = "option-item";
    if (answers[q.id] === optIdx) {
      item.classList.add("selected");
    }

    item.innerHTML = `
      <div class="opt-prefix">${prefixes[optIdx] || optIdx + 1}</div>
      <div class="opt-text">${optText}</div>
    `;

    item.onclick = () => selectOption(q.id, optIdx);
    optionsContainer.appendChild(item);
  });

  // Update button states
  document.getElementById("prevBtn").disabled = (currentIndex === 0);
  const nextBtn = document.getElementById("nextBtn");
  if (currentIndex === questions.length - 1) {
    nextBtn.textContent = "Review & Submit";
    nextBtn.onclick = openSubmitModal;
  } else {
    nextBtn.textContent = "Next →";
    nextBtn.onclick = nextQuestion;
  }

  // Update Review button text
  const reviewBtn = document.getElementById("reviewBtn");
  if (markedReviews.has(q.id)) {
    reviewBtn.textContent = "★ Marked (Click to Unmark)";
    reviewBtn.style.background = "#e9d5ff";
  } else {
    reviewBtn.textContent = "⭐ Mark Review";
    reviewBtn.style.background = "#fef3c7";
  }

  // Update active status on palette buttons
  document.querySelectorAll(".palette-btn").forEach((b, bIdx) => {
    b.classList.toggle("active", bIdx === currentIndex);
  });
}

function selectOption(qId, optIdx) {
  answers[qId] = optIdx;
  localStorage.setItem("bis_quiz_answers_" + PARTICIPANT_ID, JSON.stringify(answers));

  // Update palette button styling
  const palBtn = document.getElementById(`pal_btn_${currentIndex}`);
  if (palBtn) palBtn.classList.add("answered");

  renderQuestion(currentIndex);
  updatePaletteCounts();
}

function clearCurrentAnswer() {
  const q = questions[currentIndex];
  if (!q) return;
  delete answers[q.id];
  localStorage.setItem("bis_quiz_answers_" + PARTICIPANT_ID, JSON.stringify(answers));

  const palBtn = document.getElementById(`pal_btn_${currentIndex}`);
  if (palBtn) palBtn.classList.remove("answered");

  renderQuestion(currentIndex);
  updatePaletteCounts();
}

function toggleReview() {
  const q = questions[currentIndex];
  if (!q) return;

  if (markedReviews.has(q.id)) {
    markedReviews.delete(q.id);
  } else {
    markedReviews.add(q.id);
  }
  localStorage.setItem("bis_quiz_review_" + PARTICIPANT_ID, JSON.stringify(Array.from(markedReviews)));

  const palBtn = document.getElementById(`pal_btn_${currentIndex}`);
  if (palBtn) {
    palBtn.classList.toggle("review", markedReviews.has(q.id));
  }
  renderQuestion(currentIndex);
  updatePaletteCounts();
}

function jumpToQuestion(idx) {
  renderQuestion(idx);
}

function nextQuestion() {
  if (currentIndex < questions.length - 1) {
    renderQuestion(currentIndex + 1);
  }
}

function prevQuestion() {
  if (currentIndex > 0) {
    renderQuestion(currentIndex - 1);
  }
}

function setupKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    if (document.getElementById("submitModal").style.display === "flex") return;
    if (["1", "2", "3", "4"].includes(e.key)) {
      const optIdx = parseInt(e.key) - 1;
      const q = questions[currentIndex];
      if (q && q.options[optIdx] !== undefined) {
        selectOption(q.id, optIdx);
      }
    } else if (e.key.toLowerCase() === "n") {
      nextQuestion();
    } else if (e.key.toLowerCase() === "p") {
      prevQuestion();
    }
  });
}

function openSubmitModal() {
  const answeredCount = Object.keys(answers).length;
  const remaining = questions.length - answeredCount;
  const mins = Math.floor(remainingSeconds / 60);
  const secs = remainingSeconds % 60;

  document.getElementById("modalAnswered").textContent = answeredCount;
  document.getElementById("modalRemainingQuestions").textContent = remaining;
  document.getElementById("modalTimeLeft").textContent = `${mins}m ${secs}s`;

  document.getElementById("submitModal").style.display = "flex";
}

function closeSubmitModal() {
  document.getElementById("submitModal").style.display = "none";
}

async function finalizeSubmission(isAuto = false) {
  if (isSubmitted) return;
  isSubmitted = true;
  clearInterval(timerInterval);

  const confirmBtn = document.getElementById("confirmSubmitBtn");
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Calculating Score & Bonus... ⏳";
  }

  try {
    const res = await fetch("/api/submit-quiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        participant_id: PARTICIPANT_ID,
        answers: answers,
        time_spent_seconds: totalSeconds - remainingSeconds
      })
    });
    const data = await res.json();
    if (data.success) {
      // Clear localStorage for this participant
      localStorage.removeItem("bis_quiz_answers_" + PARTICIPANT_ID);
      localStorage.removeItem("bis_quiz_review_" + PARTICIPANT_ID);
      window.location.href = data.redirect_url;
    } else {
      alert("Submission error: " + (data.message || "Failed to submit."));
      isSubmitted = false;
      if (confirmBtn) confirmBtn.disabled = false;
    }
  } catch (err) {
    console.error("Submission failed", err);
    alert("Connection error while submitting. Retrying...");
    isSubmitted = false;
    if (confirmBtn) confirmBtn.disabled = false;
  }
}
