let trendChart;
let genderChart;
let premiumChart;

function createOrUpdateLineChart(payload) {
  const chartData = {
    labels: payload.labels,
    datasets: [
      {
        label: "Number of users",
        data: payload.number_of_users,
        borderColor: "#2a93df",
        backgroundColor: "rgba(42, 147, 223, 0.08)",
        fill: false,
        tension: 0.32,
        pointRadius: 3,
      },
      {
        label: "New users",
        data: payload.new_users,
        borderColor: "#4ec2c5",
        backgroundColor: "rgba(78, 194, 197, 0.12)",
        fill: false,
        tension: 0.32,
        pointRadius: 3,
      },
      {
        label: "Departed users",
        data: payload.departed_users,
        borderColor: "#f16486",
        backgroundColor: "rgba(241, 100, 134, 0.1)",
        fill: false,
        tension: 0.32,
        pointRadius: 3,
      },
    ],
  };

  if (!trendChart) {
    const ctx = document.getElementById("trendChart");
    trendChart = new Chart(ctx, {
      type: "line",
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: {
          x: { ticks: { maxRotation: 55, minRotation: 45 } },
          y: { beginAtZero: true, grid: { color: "rgba(70, 93, 127, 0.12)" } },
        },
      },
    });
  } else {
    trendChart.data = chartData;
    trendChart.update();
  }
}

function createOrUpdatePieChart(refName, elementId, labels, values, colors) {
  if (!window[refName]) {
    const ctx = document.getElementById(elementId);
    window[refName] = new Chart(ctx, {
      type: "pie",
      data: {
        labels,
        datasets: [{ data: values, backgroundColor: colors, borderColor: "#fff", borderWidth: 2 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
      },
    });
  } else {
    window[refName].data = {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderColor: "#fff", borderWidth: 2 }],
    };
    window[refName].update();
  }
}

function renderTableRows(tableBodyId, rows, columns) {
  const tbody = document.getElementById(tableBodyId);
  tbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((key) => {
      const td = document.createElement("td");
      td.textContent = row[key];
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function updateCards(overview) {
  document.getElementById("sessionsToday").textContent = overview.sessions_today;
  document.getElementById("totalUsers").textContent = overview.total_users;
  document.getElementById("messagesToday").textContent = overview.messages_today;
  document.getElementById("revenueToday").textContent = overview.revenue_today;
}

async function fetchDashboardData() {
  const response = await fetch("/api/v1/dashboard/data");
  if (!response.ok) {
    throw new Error(`Failed to load dashboard data: ${response.status}`);
  }
  return response.json();
}

async function renderDashboard() {
  try {
    const payload = await fetchDashboardData();
    updateCards(payload.overview);
    createOrUpdateLineChart(payload.trends);
    createOrUpdatePieChart(
      "genderChart",
      "genderChart",
      payload.gender.labels,
      payload.gender.values,
      ["#9aa4b2", "#47a3e9", "#f46d90", "#6ec8b5", "#f5c84d"]
    );
    createOrUpdatePieChart(
      "premiumChart",
      "premiumChart",
      payload.premium.labels,
      payload.premium.values,
      ["#4db8ba", "#f3c957"]
    );
    renderTableRows("achievementsBody", payload.recent_achievements, [
      "timestamp",
      "user",
      "conversion",
      "value",
    ]);
    renderTableRows("popularBody", payload.popular_habits, [
      "team",
      "number",
      "unique",
      "per_user",
      "sessions",
    ]);
  } catch (error) {
    console.error(error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const refreshSeconds = Number(document.body.dataset.refreshSeconds || "60");
  renderDashboard();
  setInterval(renderDashboard, refreshSeconds * 1000);
});
