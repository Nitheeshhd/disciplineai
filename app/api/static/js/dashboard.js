let trendChart;
let genderChart;
let premiumChart;

async function fetchDashboard() {
  const response = await fetch("/api/v1/dashboard/data");
  if (!response.ok) {
    throw new Error(`Dashboard API failed: ${response.status}`);
  }
  return response.json();
}

function setCardValues(summary) {
  document.getElementById("sessions").textContent = summary.sessions_today;
  document.getElementById("users").textContent = summary.total_users;
  document.getElementById("messages").textContent = summary.messages_today;
  document.getElementById("revenue").textContent = summary.revenue_today;
}

function renderTrend(points) {
  const labels = points.map((point) => point.date.slice(5));
  const values = points.map((point) => point.value);
  const data = {
    labels,
    datasets: [
      {
        label: "Productivity",
        data: values,
        borderColor: "#2f94df",
        backgroundColor: "rgba(47,148,223,0.12)",
        fill: true,
        tension: 0.28,
        pointRadius: 2.5,
      },
    ],
  };
  if (!trendChart) {
    trendChart = new Chart(document.getElementById("trendChart"), {
      type: "line",
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: { y: { beginAtZero: true } },
      },
    });
  } else {
    trendChart.data = data;
    trendChart.update();
  }
}

function renderPie(ref, elementId, labels, values, colors) {
  const dataset = { labels, datasets: [{ data: values, backgroundColor: colors }] };
  if (!window[ref]) {
    window[ref] = new Chart(document.getElementById(elementId), {
      type: "pie",
      data: dataset,
      options: { responsive: true, maintainAspectRatio: false },
    });
  } else {
    window[ref].data = dataset;
    window[ref].update();
  }
}

function renderTable(tableId, rows, columns) {
  const tbody = document.getElementById(tableId);
  tbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col];
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

async function loadDashboard() {
  try {
    const data = await fetchDashboard();
    setCardValues(data.summary);
    renderTrend(data.productivity_trend);
    renderPie("genderChart", "genderChart", data.gender_breakdown.labels, data.gender_breakdown.values, [
      "#57abeb",
      "#f06388",
      "#9aa4b2",
      "#6ed3c7",
    ]);
    renderPie("premiumChart", "premiumChart", data.premium_breakdown.labels, data.premium_breakdown.values, [
      "#4eb9bc",
      "#f3c956",
    ]);
    renderTable("recentBody", data.recent_goal_achievements, ["date", "user", "conversion", "value"]);
    renderTable("popularBody", data.popular_teams, ["team", "number", "unique", "per_user", "sessions"]);
  } catch (error) {
    console.error(error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  setInterval(loadDashboard, 60000);
});
