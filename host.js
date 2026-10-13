let hostParticipants = [];
let hostStats = {};
let pollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchHostData();
  pollInterval = setInterval(fetchHostData, 5000);
});

async function fetchHostData() {
  try {
    const res = await fetch("/api/host-data");
    const data = await res.json();
    if (data.success) {
      hostStats = data.stats || {};
      hostParticipants = data.participants || [];

      // Update counters
      document.getElementById("statTotalReg").textContent = hostStats.total_registered || 0;
      document.getElementById("statTotalComp").textContent = hostStats.total_completed || 0;
      document.getElementById("statInProgress").textContent = hostStats.in_progress || 0;
      document.getElementById("statTopScore").textContent = hostStats.top_score || 0;
      document.getElementById("statAvgScore").textContent = (hostStats.avg_score || 0) + " pts";

      const countBadge = document.getElementById("tableCountBadge");
      if (countBadge) countBadge.textContent = `(${hostParticipants.length} Completed)`;

      renderHostTable(hostParticipants);
    }
  } catch (err) {
    console.error("Failed to fetch host data", err);
  }
}

function renderHostTable(list) {
  const tbody = document.getElementById("hostTableBody");
  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align:center; padding:30px; color:var(--text-muted);">
          No participant submissions yet. Have students scan the QR code to participate.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = "";
  list.forEach(p => {
    const tr = document.createElement("tr");

    let rankLabel = `#${p.rank}`;
    let rankClass = "rank-other";
    if (p.rank === 1) { rankLabel = "🥇 1"; rankClass = "rank-1"; }
    else if (p.rank === 2) { rankLabel = "🥈 2"; rankClass = "rank-2"; }
    else if (p.rank === 3) { rankLabel = "🥉 3"; rankClass = "rank-3"; }

    tr.innerHTML = `
      <td><span class="rank-badge ${rankClass}">${rankLabel}</span></td>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td style="font-family:monospace; color:#334155;">${escapeHtml(p.phone)}</td>
      <td style="font-weight:600; color:#475569;">${escapeHtml(p.college_id)}</td>
      <td><strong style="color:var(--primary); font-size:15px;">${p.total_points}</strong> pts</td>
      <td><span style="color:#059669; font-weight:600;">${p.correct_count}</span> / 30</td>
      <td><span style="color:#d97706; font-weight:700;">+${p.speed_bonus}</span></td>
      <td style="font-family:monospace;">${p.time_taken}</td>
      <td style="font-size:12px; color:#64748b;">${p.submitted_at}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterHostTable() {
  const query = (document.getElementById("hostSearchInput").value || "").toLowerCase().trim();
  if (!query) {
    renderHostTable(hostParticipants);
    return;
  }
  const filtered = hostParticipants.filter(p =>
    p.name.toLowerCase().includes(query) ||
    p.phone.includes(query) ||
    p.college_id.toLowerCase().includes(query)
  );
  renderHostTable(filtered);
}

function copyJoinLink() {
  const link = document.getElementById("joinUrlLink").href;
  navigator.clipboard.writeText(link).then(() => {
    alert("Copied join link to clipboard: " + link);
  }).catch(() => {
    prompt("Copy participant link:", link);
  });
}

function showLargeQR() {
  const modal = document.getElementById("largeQrModal");
  if (modal) modal.style.display = "flex";
}

function closeLargeQR() {
  const modal = document.getElementById("largeQrModal");
  if (modal) modal.style.display = "none";
}

function copyPublicHostLink() {
  const link = document.getElementById("publicHostUrlLink").href;
  navigator.clipboard.writeText(link).then(() => {
    alert("✅ Copied Public Host Dashboard Link to clipboard!\n\nYou can now send this link to anyone you want to make a Co-Host / Organizer.");
  }).catch(() => {
    prompt("Copy Co-Host Dashboard link:", link);
  });
}

function showCoHostQR() {
  const modal = document.getElementById("coHostQrModal");
  if (modal) modal.style.display = "flex";
}

function closeCoHostQR() {
  const modal = document.getElementById("coHostQrModal");
  if (modal) modal.style.display = "none";
}

async function updateCustomUrl() {
  const customUrl = document.getElementById("customUrlInput").value.trim();
  if (!customUrl) return;

  try {
    const res = await fetch("/api/update-join-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: customUrl })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("qrCodeImg").src = data.qr_data_url;
      document.getElementById("modalQrImg").src = data.qr_data_url;
      const linkEl = document.getElementById("joinUrlLink");
      linkEl.href = data.url;
      linkEl.textContent = data.url;
      alert("QR code regenerated successfully for: " + data.url);
    }
  } catch (err) {
    alert("Failed to regenerate QR code");
  }
}

async function copyHostSummaryText() {
  try {
    const res = await fetch("/api/export-summary");
    const text = await res.text();
    navigator.clipboard.writeText(text).then(() => {
      alert("✅ Full Host Summary report copied to clipboard! You can paste it in WhatsApp or Email.");
    }).catch(() => {
      prompt("Copy summary report:", text);
    });
  } catch (err) {
    alert("Could not copy summary");
  }
}

function emailReportToHost() {
  const subject = encodeURIComponent("Bureau of Indian Standards (BIS) Quiz Results Report");
  let body = `Dear Host,\n\nHere are the latest results for the BIS Quiz:\nTotal Registered: ${hostStats.total_registered || 0}\nCompleted Exams: ${hostStats.total_completed || 0}\nHighest Score: ${hostStats.top_score || 0}\n\nPlease find the attached scores or download them directly from the Host Control Center.\n`;
  window.open(`mailto:?subject=${subject}&body=${encodeURIComponent(body)}`);
}

async function confirmResetData() {
  const pass = confirm("⚠️ Are you sure you want to reset all participant responses and start a fresh quiz session? This action cannot be undone.");
  if (!pass) return;

  try {
    const res = await fetch("/api/reset-data", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      alert("All participant data reset successfully.");
      fetchHostData();
    }
  } catch (err) {
    alert("Failed to reset data.");
  }
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
