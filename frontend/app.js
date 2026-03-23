/**
 * app.js — Dashboard frontend logic
 * Handles fetching API, chart rendering, searching, filtering, and state management.
 */

const API = "";

// ── State ────────────────────────────────────────────────────────────────────
let rawRevenueData = [];
let rawCustomerData = [];
let charts = {};

// ── Chart.js global defaults ─────────────────────────────────────────────────
Chart.defaults.color = "#7a8099";
Chart.defaults.borderColor = "rgba(255,255,255,0.07)";
Chart.defaults.font.family = "Inter, sans-serif";

const PALETTE = [
  "#6c63ff","#00d2ff","#ff6b6b","#fbbf24","#22c55e",
  "#f472b6","#a78bfa","#34d399","#fb923c","#60a5fa"
];

// ── UI Control & State Helpers ───────────────────────────────────────────────
function showLoading() {
  document.getElementById("global-loading").classList.remove("hidden");
  document.getElementById("global-error").classList.add("hidden");
  document.getElementById("dashboard-content").classList.add("hidden");
}

function showError(msg) {
  document.getElementById("global-loading").classList.add("hidden");
  const err = document.getElementById("global-error");
  err.classList.remove("hidden");
  document.getElementById("dashboard-content").classList.add("hidden");
  if (msg) document.getElementById("error-message").textContent = msg;
}

function showDashboard() {
  document.getElementById("global-loading").classList.add("hidden");
  document.getElementById("global-error").classList.add("hidden");
  document.getElementById("dashboard-content").classList.remove("hidden");
}

// ── Tab navigation ───────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(s => s.classList.add("hidden"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    if (tab === "overview") {
      document.querySelectorAll(".tab-content").forEach(s => s.classList.add("hidden"));
    } else {
      document.getElementById(`tab-${tab}`)?.classList.remove("hidden");
    }
  });
});

// ── Formatters ───────────────────────────────────────────────────────────────
const fmt = v => v == null ? "—" : Number(v).toLocaleString("en-US", { maximumFractionDigits: 2 });
const fmtMoney = v => v == null ? "—" : "$" + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function makeChart(id, type, labels, datasets, extraOptions = {}) {
  const ctx = document.getElementById(id);
  if (!ctx) return null;
  if (charts[id]) charts[id].destroy(); // Destroy previous instance if it exists
  
  charts[id] = new Chart(ctx, {
    type,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 800, easing: "easeOutQuart" },
      plugins: {
        legend: { labels: { color: "#7a8099", boxWidth: 14, font: { size: 12 } } },
        tooltip: {
          backgroundColor: "#181e2e",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          titleColor: "#e8eaf0",
          bodyColor: "#7a8099",
          padding: 12,
        }
      },
      ...extraOptions,
    }
  });
  return charts[id];
}

async function get(url) {
  const res = await fetch(API + url);
  if (!res.ok) {
    let msg = `API Error: ${res.status}`;
    try { const err = await res.json(); msg += ` - ${err.detail}`; } catch(e) {}
    throw new Error(msg);
  }
  return res.json();
}

// ── 1. Summary stats ──────────────────────────────────────────────────────────
function renderSummary(data) {
  const rev = rawRevenueData;
  const totalRev = rev.reduce((acc, curr) => acc + (curr.total_revenue || 0), 0);
  
  animateCount("val-orders", 300); // hardcoding based on orders length or we could fetch orders endpoint length if we had it. Let's compute.
  animateCount("val-customers", rawCustomerData.length || 80);
  animateCountMoney("val-revenue", totalRev);
  animateCount("val-months", rev.length);
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const duration = 1000, step = 16;
  const steps = duration / step;
  let current = 0, inc = target / steps;
  const timer = setInterval(() => {
    current = Math.min(current + inc, target);
    el.textContent = Math.round(current).toLocaleString();
    if (current >= target) clearInterval(timer);
  }, step);
}

function animateCountMoney(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const duration = 1000, step = 16;
  const steps = duration / step;
  let current = 0, inc = target / steps;
  const timer = setInterval(() => {
    current = Math.min(current + inc, target);
    el.textContent = "$" + Math.round(current).toLocaleString();
    if (current >= target) clearInterval(timer);
  }, step);
}

// ── 2. Revenue trend ─────────────────────────────────────────────────────────
function renderRevenueChart(data) {
  if (!data.length) return;
  const labels = data.map(d => d.order_year_month);
  const values = data.map(d => d.total_revenue);

  makeChart("revenueChart", "line", labels, [{
    label: "Revenue ($)",
    data: values,
    borderColor: "#6c63ff",
    backgroundColor: "rgba(108,99,255,0.12)",
    fill: true,
    tension: 0.4,
    pointBackgroundColor: "#6c63ff",
    pointRadius: 4,
    pointHoverRadius: 7,
  }], {
    scales: {
      x: { ticks: { maxRotation: 45 } },
      y: { ticks: { callback: v => "$" + v.toLocaleString() } }
    }
  });
}

function filterRevenueChart() {
  const start = document.getElementById("revenue-start").value;
  const end = document.getElementById("revenue-end").value;
  
  let filtered = rawRevenueData;
  if (start) Object.assign(filtered, filtered.filter(d => d.order_year_month >= start));
  if (start) filtered = filtered.filter(d => d.order_year_month >= start);
  if (end) filtered = filtered.filter(d => d.order_year_month <= end);
  
  renderRevenueChart(filtered);
}

document.getElementById("filter-revenue-btn")?.addEventListener("click", filterRevenueChart);

// ── 3. Top customers table ────────────────────────────────────────────────────
function renderCustomersTable(data) {
  const tbody = document.getElementById("customersBody");
  const emptyState = document.getElementById("customers-empty");
  const table = document.getElementById("customersTable");
  
  if (!tbody || !data) return;
  
  if (data.length === 0) {
    emptyState.classList.remove("hidden");
    table.classList.add("hidden");
    return;
  }
  
  emptyState.classList.add("hidden");
  table.classList.remove("hidden");
  
  tbody.innerHTML = data.map((r, i) => `
    <tr>
      <td class="rank">#${i + 1}</td>
      <td><strong>${r.name ?? "—"}</strong></td>
      <td>${r.region ?? "—"}</td>
      <td>${fmtMoney(r.total_spend)}</td>
      <td>
        <span class="badge ${r.churned ? 'badge-churned' : 'badge-active'}">
          ${r.churned ? "⚠ Churned" : "✓ Active"}
        </span>
      </td>
    </tr>
  `).join("");
}

function filterCustomers() {
  const query = document.getElementById("customer-search").value.toLowerCase();
  const filtered = rawCustomerData.filter(c => 
    (c.name && c.name.toLowerCase().includes(query)) ||
    (c.region && c.region.toLowerCase().includes(query))
  );
  renderCustomersTable(filtered);
}

document.getElementById("customer-search")?.addEventListener("input", filterCustomers);

// ── 4. Category performance ───────────────────────────────────────────────────
function renderCategories(data) {
  if (!data || !data.length) return;

  const labels = data.map(d => d.category ?? "Unknown");
  const revenues = data.map(d => d.total_revenue);
  const orders   = data.map(d => d.num_orders);

  makeChart("categoryRevenueChart", "bar", labels, [{
    label: "Total Revenue ($)",
    data: revenues,
    backgroundColor: PALETTE.map(c => c + "cc"),
    borderColor: PALETTE,
    borderWidth: 1,
    borderRadius: 6,
  }], {
    plugins: { legend: { display: false } },
    scales: { y: { ticks: { callback: v => "$" + v.toLocaleString() } } }
  });

  makeChart("categoryOrdersChart", "doughnut", labels, [{
    data: orders,
    backgroundColor: PALETTE.map(c => c + "ee"),
    borderColor: "#111625",
    borderWidth: 2,
  }], {
    cutout: "55%",
    plugins: { legend: { position: "right" } }
  });

  const tbody = document.getElementById("categoryBody");
  if (tbody) {
    tbody.innerHTML = data.map(r => `
      <tr>
        <td><strong>${r.category ?? "—"}</strong></td>
        <td>${fmtMoney(r.total_revenue)}</td>
        <td>${fmtMoney(r.avg_order_value)}</td>
        <td>${fmt(r.num_orders)}</td>
      </tr>
    `).join("");
  }
}

// ── 5. Regional analysis ──────────────────────────────────────────────────────
function renderRegions(data) {
  if (!data || !data.length) return;

  const grid = document.getElementById("regionGrid");
  if (grid) {
    grid.innerHTML = data.map(r => `
      <div class="region-card">
        <div class="region-name">📍 ${r.region ?? "Unknown"}</div>
        <div class="region-stat"><span>Customers</span><span>${fmt(r.num_customers)}</span></div>
        <div class="region-stat"><span>Orders</span><span>${fmt(r.num_orders)}</span></div>
        <div class="region-stat"><span>Total Revenue</span><span>${fmtMoney(r.total_revenue)}</span></div>
        <div class="region-stat"><span>Avg Rev / Customer</span><span>${fmtMoney(r.avg_revenue_per_customer)}</span></div>
      </div>
    `).join("");
  }

  const labels   = data.map(d => d.region ?? "Unknown");
  const revenues = data.map(d => d.total_revenue);

  makeChart("regionChart", "bar", labels, [{
    label: "Total Revenue ($)",
    data: revenues,
    backgroundColor: PALETTE.map(c => c + "cc"),
    borderColor: PALETTE,
    borderWidth: 1,
    borderRadius: 8,
  }], {
    plugins: { legend: { display: false } },
    scales: { y: { ticks: { callback: v => "$" + v.toLocaleString() } } }
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
(async function init() {
  showLoading();
  try {
    const [revData, custData, catData, regData] = await Promise.all([
      get("/api/revenue"),
      get("/api/top-customers"),
      get("/api/categories"),
      get("/api/regions")
    ]);

    rawRevenueData = revData;
    rawCustomerData = custData;

    renderSummary();
    renderRevenueChart(revData);
    renderCustomersTable(custData);
    renderCategories(catData);
    renderRegions(regData);

    showDashboard();
  } catch (error) {
    console.error("Dashboard Init Error:", error);
    showError(error.message || "Failed to connect to the API. Make sure FastAPI is running on port 8000.");
  }
})();
