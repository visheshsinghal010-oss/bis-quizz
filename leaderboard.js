let allParticipants = [];
let refreshInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchLeaderboard();
  refreshInterval = setInterval(fetchLeaderboard, 6000);
});

async function fetchLeaderboard() {
  try {
    const res = await fetch("/api/leaderboard");
    const data = await res.json();
    if (data.success) {
      allParticipants = data.leaderboard || [];
      renderLeaderboardTable(allParticipants);
      checkPersonalScore(allParticipants);
      const countEl = document.getElementById("totalCountBadge");
      if (countEl) countEl.textContent = `(${allParticipants.length} Completed)`;
    }
  } catch (err) {
    console.error("Leaderboard fetch error", err);
  }
}

function checkPersonalScore(list) {
  if (!HIGHLIGHT_ID) return;
  const me = list.find(p => p.id === HIGHLIGHT_ID);
  if (!me) return;

  const card = document.getElementById("personalScoreCard");
  if (!card) return;

  document.getElementById("myGreeting").textContent = `🎉 Well done, ${me.name}!`;
  document.getElementById("mySubtext").textContent = `College ID: ${me.college_id} • Score details below:`;
  document.getElementById("myRank").textContent = `#${me.rank}`;
  document.getElementById("myTotalPoints").textContent = me.total_points;
  document.getElementById("myAccuracy").textContent = `${me.correct_count}/${me.total_questions}`;
  document.getElementById("mySpeedBonus").textContent = `+${me.speed_bonus}`;
  document.getElementById("myTimeTaken").textContent = me.time_taken_formatted;

  card.style.display = "flex";
}

function renderLeaderboardTable(list) {
  const tbody = document.getElementById("leaderboardBody");
  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align:center; padding:36px; color:var(--text-muted);">
          No participants have submitted yet. Scan the QR code to be the first!
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = "";
  list.forEach(p => {
    const tr = document.createElement("tr");
    if (HIGHLIGHT_ID && p.id === HIGHLIGHT_ID) {
      tr.className = "highlight-row";
    }

    let rankBadgeClass = "rank-other";
    let rankLabel = `#${p.rank}`;
    if (p.rank === 1) {
      rankBadgeClass = "rank-1";
      rankLabel = "🥇 1";
    } else if (p.rank === 2) {
      rankBadgeClass = "rank-2";
      rankLabel = "🥈 2";
    } else if (p.rank === 3) {
      rankBadgeClass = "rank-3";
      rankLabel = "🥉 3";
    }

    tr.innerHTML = `
      <td>
        <span class="rank-badge ${rankBadgeClass}">${rankLabel}</span>
      </td>
      <td>
        <strong style="color:var(--text-main); font-size:15px;">${escapeHtml(p.name)}</strong>
        ${(HIGHLIGHT_ID && p.id === HIGHLIGHT_ID) ? ' <span style="background:#10b981; color:#fff; font-size:10px; font-weight:700; padding:2px 6px; border-radius:10px;">YOU</span>' : ''}
      </td>
      <td style="color:#475569; font-weight:500;">${escapeHtml(p.college_id)}</td>
      <td>
        <span style="font-weight:800; font-size:16px; color:var(--primary);">${p.total_points}</span>
        <span style="font-size:11px; color:#64748b;"> pts</span>
      </td>
      <td>
        <span style="font-weight:600; color:#059669;">${p.correct_count}</span>
        <span style="color:#94a3b8; font-size:12px;"> / ${p.total_questions}</span>
      </td>
      <td>
        <span style="color:#d97706; font-weight:700;">+${p.speed_bonus}</span>
      </td>
      <td style="font-family:monospace; font-size:13px; color:#475569;">${p.time_taken_formatted}</td>
      <td style="font-size:12px; color:#64748b;">${p.submitted_at || "-"}</td>
    `;

    tbody.appendChild(tr);
  });
}

function filterTable() {
  const query = (document.getElementById("searchInput").value || "").toLowerCase().trim();
  if (!query) {
    renderLeaderboardTable(allParticipants);
    return;
  }

  const filtered = allParticipants.filter(p => 
    p.name.toLowerCase().includes(query) ||
    p.college_id.toLowerCase().includes(query)
  );

  renderLeaderboardTable(filtered);
}

function escapeHtml(text) {
  if (!text) return "";
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}
