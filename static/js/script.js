// =============================================================
// NEXUS ANALYTICS — Core Frontend Script
// =============================================================

document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle (mobile)
  const sidebar = document.getElementById("sidebar");
  const toggleBtn = document.getElementById("sidebarToggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  document.addEventListener("click", function (e) {
    if (window.innerWidth < 992 && sidebar && sidebar.classList.contains("open")) {
      if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove("open");
      }
    }
  });

  // Render all Plotly charts.
  // Each chart's figure JSON lives in a <script type="application/json"
  // data-for="targetDivId"> tag rather than an HTML attribute. Attributes
  // are delimited by quote characters, and real chart data (JSON keys,
  // hover templates, city/category names with apostrophes, etc.) is full
  // of quote characters, so embedding JSON directly as an attribute value
  // is fundamentally unsafe. A <script> tag's text content has no such
  // restriction (the parser only looks for the closing tag), which is why
  // this is the standard, robust way to hand server-rendered JSON to
  // client-side JS.
  const renderedChartIds = [];
  document.querySelectorAll('script[type="application/json"][data-for]').forEach(function (scriptEl) {
    const targetId = scriptEl.getAttribute("data-for");
    const container = document.getElementById(targetId);
    if (!container) {
      console.error("Chart container not found for", targetId);
      return;
    }
    try {
      const chartData = JSON.parse(scriptEl.textContent);
      const config = {
        responsive: true,
        displayModeBar: false,
        displaylogo: false,
      };
      Plotly.newPlot(container, chartData.data, chartData.layout, config);
      renderedChartIds.push(targetId);
    } catch (err) {
      console.error("Chart render error for", targetId, err);
    }
  });

  // Resize charts on sidebar breakpoint / window changes
  window.addEventListener("resize", function () {
    renderedChartIds.forEach(function (id) {
      Plotly.Plots.resize(id);
    });
  });

  // Animate KPI numbers count-up
  document.querySelectorAll(".kpi-count").forEach(function (el) {
    const target = parseFloat(el.getAttribute("data-value"));
    const isDecimal = el.getAttribute("data-decimal") === "true";
    const prefix = el.getAttribute("data-prefix") || "";
    const suffix = el.getAttribute("data-suffix") || "";
    if (isNaN(target)) return;

    let start = 0;
    const duration = 900;
    const startTime = performance.now();

    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = start + (target - start) * eased;
      el.textContent = prefix + (isDecimal ? value.toFixed(2) : Math.round(value).toLocaleString("en-IN")) + suffix;
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
});
