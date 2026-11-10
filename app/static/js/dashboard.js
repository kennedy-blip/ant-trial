/**
 * Polars CSV Analytics Dashboard Frontend
 * Handles file uploads, sample selection, summary table rendering,
 * sorting, filtering, and Plotly.js interactive visualization.
 */

let currentAnalysis = null;
let currentSortColumn = "column";
let currentSortDirection = "asc";

document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadSampleFileList();
});

/**
 * Initialize all DOM event listeners.
 */
function initEventListeners() {
  const dropzone = document.getElementById("dropzoneContainer");
  const fileInput = document.getElementById("csvFileInput");
  const sampleSelect = document.getElementById("sampleSelect");
  const loadSampleBtn = document.getElementById("loadSampleBtn");
  const reanalyzeBtn = document.getElementById("reanalyzeBtn");
  const statsFilterInput = document.getElementById("statsFilterInput");
  const typeFilterSelect = document.getElementById("typeFilterSelect");
  const studioRenderBtn = document.getElementById("studioRenderBtn");
  const exportCsvBtn = document.getElementById("exportCsvBtn");
  const exportJsonBtn = document.getElementById("exportJsonBtn");

  if (exportCsvBtn) exportCsvBtn.addEventListener("click", exportSummaryCsv);
  if (exportJsonBtn) exportJsonBtn.addEventListener("click", exportSummaryJson);

  // Dropzone click & drag-and-drop
  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  // Sample dataset loading
  loadSampleBtn.addEventListener("click", () => {
    const selected = sampleSelect.value;
    if (selected) {
      loadSample(selected);
    }
  });

  sampleSelect.addEventListener("change", () => {
    loadSampleBtn.disabled = !sampleSelect.value;
  });

  // Re-analyze button
  reanalyzeBtn.addEventListener("click", () => {
    if (currentAnalysis && currentAnalysis.file_name) {
      const sampleVal = sampleSelect.value;
      if (sampleVal) {
        loadSample(sampleVal);
      }
    }
  });

  // Filter input and select for Summary Table
  statsFilterInput.addEventListener("input", renderSummaryTable);
  typeFilterSelect.addEventListener("change", renderSummaryTable);

  // Table header sorting
  document.querySelectorAll("th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.getAttribute("data-sort");
      if (currentSortColumn === col) {
        currentSortDirection = currentSortDirection === "asc" ? "desc" : "asc";
      } else {
        currentSortColumn = col;
        currentSortDirection = "asc";
      }
      updateSortHeaders();
      renderSummaryTable();
    });
  });

  // Tabs switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Interactive Chart Studio
  studioRenderBtn.addEventListener("click", renderStudioChart);
}

/**
 * Switch active dashboard tab.
 */
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
    btn.classList.remove("border-sky-600", "text-sky-600");
    btn.classList.add("border-transparent", "text-slate-500");
  });

  const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  if (activeBtn) {
    activeBtn.classList.add("active");
    activeBtn.classList.add("border-sky-600", "text-sky-600");
    activeBtn.classList.remove("border-transparent", "text-slate-500");
  }

  document.querySelectorAll(".tab-content").forEach((c) => c.classList.add("hidden"));
  const targetContent = document.getElementById(tabId);
  if (targetContent) {
    targetContent.classList.remove("hidden");
  }

  // Trigger Plotly relayout to fit resized tabs
  if (tabId === "tabCorrelation") {
    setTimeout(() => {
      const corrDiv = document.getElementById("correlationChart");
      if (corrDiv && corrDiv.data) {
        Plotly.Plots.resize(corrDiv);
      }
    }, 50);
  } else if (tabId === "tabCharts") {
    setTimeout(() => {
      document.querySelectorAll("#numericChartsGrid > div, #categoricalChartsGrid > div").forEach((card) => {
        const plotEl = card.querySelector(".plotly-graph-div");
        if (plotEl) Plotly.Plots.resize(plotEl);
      });
    }, 50);
  }
}

/**
 * Fetch available sample files from server.
 */
async function loadSampleFileList() {
  try {
    const res = await fetch("/api/sample-files");
    if (!res.ok) return;
    const files = await res.json();
    const select = document.getElementById("sampleSelect");
    select.innerHTML = '<option value="" disabled selected>Select a sample CSV...</option>';

    files.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.filename;
      opt.textContent = `${f.filename} (${f.size_kb} KB)`;
      select.appendChild(opt);
    });

    // Automatically load the first sample if available for instant demonstration
    if (files.length > 0) {
      select.value = files[0].filename;
      document.getElementById("loadSampleBtn").disabled = false;
      loadSample(files[0].filename);
    }
  } catch (err) {
    console.warn("Could not load sample file list:", err);
  }
}

/**
 * Load a sample file by filename.
 */
async function loadSample(filename) {
  showLoading("Loading and analyzing with Polars...");
  try {
    const res = await fetch(`/api/load-sample/${encodeURIComponent(filename)}`);
    const data = await res.json();
    if (!res.ok) {
      alert(`Error: ${data.detail || "Failed to load sample dataset"}`);
      return;
    }
    applyAnalysis(data);
  } catch (err) {
    alert("Connection error: " + err.message);
  } finally {
    hideLoading();
  }
}

/**
 * Upload a CSV file directly to the backend.
 */
async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    alert("Please upload a valid .csv file.");
    return;
  }

  showLoading(`Analyzing '${file.name}' using Polars...`);
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      alert(`Error: ${data.detail || "Failed to parse CSV"}`);
      return;
    }
    applyAnalysis(data);
  } catch (err) {
    alert("Error uploading file: " + err.message);
  } finally {
    hideLoading();
  }
}

function showLoading(msg) {
  const badge = document.getElementById("parsingTime");
  if (badge) badge.textContent = "Processing...";
}

function hideLoading() {}

/**
 * Master method to render analysis data onto the dashboard.
 */
function applyAnalysis(data) {
  currentAnalysis = data;

  // Unhide main containers
  document.getElementById("emptyState").classList.add("hidden");
  document.getElementById("statusBanner").classList.remove("hidden");
  document.getElementById("statusBanner").classList.add("flex");
  document.getElementById("kpiGrid").classList.remove("hidden");
  document.getElementById("dashboardTabsContainer").classList.remove("hidden");

  // Update Status Banner
  document.getElementById("activeFileName").textContent = data.file_name;
  document.getElementById("parsingTime").textContent = `${data.processing_time_ms}ms`;

  // Update KPI Cards
  const k = data.kpis;
  document.getElementById("kpiRows").textContent = Number(k.total_rows).toLocaleString();
  document.getElementById("kpiCols").textContent = k.total_columns;
  document.getElementById("kpiColBreakdown").textContent = `${k.numeric_columns_count} Numeric / ${k.categorical_columns_count} Categorical`;
  document.getElementById("kpiNulls").textContent = Number(k.total_null_cells).toLocaleString();
  document.getElementById("kpiNullPct").textContent = `${k.null_percentage}% missing cell rate`;
  document.getElementById("kpiNumeric").textContent = k.numeric_columns_count;
  document.getElementById("kpiMemory").textContent = `${k.memory_usage_mb} MB`;

  document.getElementById("tabBadgeCols").textContent = k.total_columns;

  // Render Sub-Views
  renderSummaryTable();
  renderAutomatedCharts(data);
  renderCorrelationMatrix(data);
  setupStudioSelectors(data);
  renderPreviewTable(data);

  if (window.lucide) {
    lucide.createIcons();
  }
}

/**
 * Render the Summary Statistics Table.
 */
function renderSummaryTable() {
  if (!currentAnalysis) return;

  const tbody = document.getElementById("summaryTableBody");
  tbody.innerHTML = "";

  const filterText = (document.getElementById("statsFilterInput").value || "").toLowerCase();
  const typeFilter = document.getElementById("typeFilterSelect").value;

  let stats = [...currentAnalysis.summary_statistics];

  // Apply filters
  if (filterText) {
    stats = stats.filter((s) => s.column.toLowerCase().includes(filterText));
  }
  if (typeFilter === "numeric") {
    stats = stats.filter((s) => s.is_numeric);
  } else if (typeFilter === "categorical") {
    stats = stats.filter((s) => !s.is_numeric);
  }

  // Apply sorting
  stats.sort((a, b) => {
    let va = a[currentSortColumn];
    let vb = b[currentSortColumn];

    if (va === null || va === undefined) return 1;
    if (vb === null || vb === undefined) return -1;

    if (typeof va === "string") {
      return currentSortDirection === "asc"
        ? va.localeCompare(vb)
        : vb.localeCompare(va);
    }
    return currentSortDirection === "asc" ? va - vb : vb - va;
  });

  if (stats.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" class="text-center py-6 text-slate-400">No columns matching filter</td></tr>`;
    return;
  }

  stats.forEach((s) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 transition border-b border-slate-100";

    // Format skewness badge
    let skewBadge = `<span class="text-slate-400">-</span>`;
    if (s.skewness !== null && s.skewness !== undefined) {
      let badgeClass = "badge-symmetric";
      if (s.skewness > 0.5) badgeClass = "badge-positive-skew";
      else if (s.skewness < -0.5) badgeClass = "badge-negative-skew";

      skewBadge = `
        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${badgeClass}" title="${s.skewness_desc}">
          ${s.skewness.toFixed(3)}
        </span>
      `;
    }

    // Format null cell
    const nullCell = s.null_count > 0
      ? `<span class="text-amber-600 font-semibold">${s.null_count.toLocaleString()} (${s.null_pct}%)</span>`
      : `<span class="text-slate-400">0 (0%)</span>`;

    // Format notes or top values
    let notes = "";
    if (s.is_numeric) {
      notes = `<span class="text-[11px] text-slate-500 font-sans">Q25: ${s.q25 ?? '-'} | Q75: ${s.q75 ?? '-'}</span>`;
    } else if (s.top_values && s.top_values.length > 0) {
      notes = `<span class="text-[11px] text-slate-500 font-sans truncate max-w-xs block" title="${s.top_values.join(', ')}">${s.top_values.join(', ')}</span>`;
    }

    tr.innerHTML = `
      <td class="px-4 py-2.5 font-bold text-slate-900">${s.column}</td>
      <td class="px-3 py-2.5"><span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">${s.dtype}</span></td>
      <td class="px-3 py-2.5 text-right font-mono-numbers">${s.count.toLocaleString()}</td>
      <td class="px-3 py-2.5 text-right font-mono-numbers">${nullCell}</td>
      <td class="px-3 py-2.5 text-right font-mono-numbers font-semibold text-slate-800">${s.mean !== null ? s.mean.toLocaleString() : "-"}</td>
      <td class="px-3 py-2.5 text-right font-mono-numbers text-slate-800">${s.median !== null ? s.median.toLocaleString() : "-"}</td>
      <td class="px-3 py-2.5 text-right">${skewBadge}</td>
      <td class="px-3 py-2.5 text-right font-mono-numbers">${s.min !== null ? s.min.toLocaleString() : "-"}</td>
      <td class="px-3 py-2.5 text-right font-mono-numbers">${s.max !== null ? s.max.toLocaleString() : "-"}</td>
      <td class="px-3 py-2.5 text-right font-mono-numbers">${s.std !== null ? s.std.toLocaleString() : "-"}</td>
      <td class="px-4 py-2.5">${notes}</td>
    `;
    tbody.appendChild(tr);
  });
}

function updateSortHeaders() {
  document.querySelectorAll("th[data-sort]").forEach((th) => {
    th.classList.remove("sort-asc", "sort-desc");
    if (th.getAttribute("data-sort") === currentSortColumn) {
      th.classList.add(currentSortDirection === "asc" ? "sort-asc" : "sort-desc");
    }
  });
}

/**
 * Automatically generates interactive charts for numeric and categorical columns.
 */
function renderAutomatedCharts(data) {
  const numGrid = document.getElementById("numericChartsGrid");
  const catGrid = document.getElementById("categoricalChartsGrid");
  numGrid.innerHTML = "";
  catGrid.innerHTML = "";

  const chartPayloads = data.chart_data;

  // 1. Numeric Histograms
  const numEntries = Object.entries(chartPayloads.histograms || {});
  if (numEntries.length === 0) {
    numGrid.innerHTML = `<div class="col-span-2 text-center py-8 text-slate-400">No numeric columns found for distribution charts.</div>`;
  } else {
    numEntries.forEach(([col, hist]) => {
      const card = document.createElement("div");
      card.className = "chart-card bg-white rounded-xl border border-slate-200 p-4 shadow-sm";
      const chartId = `chart_hist_${col.replace(/[^a-zA-Z0-9]/g, "_")}`;

      const statItem = data.summary_statistics.find((s) => s.column === col);
      const skewTxt = statItem && statItem.skewness !== null ? `Skewness: ${statItem.skewness}` : "";

      card.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <div class="font-bold text-sm text-slate-800 flex items-center space-x-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block"></span>
            <span>${col}</span>
          </div>
          <span class="text-xs font-mono font-medium text-slate-500">${skewTxt}</span>
        </div>
        <div id="${chartId}" class="w-full h-64"></div>
      `;
      numGrid.appendChild(card);

      const trace = {
        x: hist.labels,
        y: hist.counts,
        type: "bar",
        marker: {
          color: "#0284c7",
          line: { color: "#0369a1", width: 1 },
        },
        hovertemplate: "Range: %{x}<br>Count: %{y:,}<extra></extra>",
      };

      const layout = {
        margin: { t: 15, r: 15, l: 45, b: 65 },
        xaxis: {
          tickangle: -30,
          tickfont: { size: 9, color: "#64748b" },
        },
        yaxis: {
          title: "Frequency",
          titlefont: { size: 10, color: "#64748b" },
          tickfont: { size: 9, color: "#64748b" },
        },
        bargap: 0.1,
        plot_bgcolor: "#ffffff",
        paper_bgcolor: "#ffffff",
      };

      Plotly.newPlot(chartId, [trace], layout, { responsive: true, displayModeBar: false });
    });
  }

  // 2. Categorical Frequencies
  const catEntries = Object.entries(chartPayloads.categorical_bars || {});
  if (catEntries.length === 0) {
    catGrid.innerHTML = `<div class="col-span-2 text-center py-8 text-slate-400">No categorical columns found.</div>`;
  } else {
    catEntries.forEach(([col, cat]) => {
      const card = document.createElement("div");
      card.className = "chart-card bg-white rounded-xl border border-slate-200 p-4 shadow-sm";
      const chartId = `chart_cat_${col.replace(/[^a-zA-Z0-9]/g, "_")}`;

      card.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <div class="font-bold text-sm text-slate-800 flex items-center space-x-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block"></span>
            <span>${col}</span>
          </div>
          <span class="text-xs text-slate-400">Top Categories</span>
        </div>
        <div id="${chartId}" class="w-full h-64"></div>
      `;
      catGrid.appendChild(card);

      const trace = {
        x: cat.counts.slice().reverse(),
        y: cat.labels.slice().reverse(),
        type: "bar",
        orientation: "h",
        marker: {
          color: "#6366f1",
          line: { color: "#4f46e5", width: 1 },
        },
        hovertemplate: "Category: %{y}<br>Count: %{x:,}<extra></extra>",
      };

      const layout = {
        margin: { t: 15, r: 20, l: 110, b: 35 },
        xaxis: {
          title: "Count",
          titlefont: { size: 10, color: "#64748b" },
          tickfont: { size: 9, color: "#64748b" },
        },
        yaxis: {
          tickfont: { size: 10, color: "#475569" },
        },
        bargap: 0.15,
        plot_bgcolor: "#ffffff",
        paper_bgcolor: "#ffffff",
      };

      Plotly.newPlot(chartId, [trace], layout, { responsive: true, displayModeBar: false });
    });
  }
}

/**
 * Render Pearson Correlation Matrix as an interactive heatmap.
 */
function renderCorrelationMatrix(data) {
  const corrData = data.chart_data ? data.chart_data.correlation_matrix : null;
  const container = document.getElementById("correlationChart");

  if (!corrData || !corrData.columns || corrData.columns.length < 2) {
    container.innerHTML = `
      <div class="flex items-center justify-center h-full text-slate-400 text-xs">
        At least 2 numeric columns are required to compute a correlation matrix.
      </div>
    `;
    return;
  }

  const trace = {
    z: corrData.matrix,
    x: corrData.columns,
    y: corrData.columns,
    type: "heatmap",
    colorscale: "Viridis",
    zmin: -1.0,
    zmax: 1.0,
    hoverongaps: false,
    hovertemplate: "Variable X: %{x}<br>Variable Y: %{y}<br>Pearson r: %{z:.3f}<extra></extra>",
  };

  const layout = {
    margin: { t: 40, r: 40, l: 120, b: 120 },
    xaxis: { tickangle: -35, tickfont: { size: 10, color: "#475569" } },
    yaxis: { tickfont: { size: 10, color: "#475569" } },
    plot_bgcolor: "#ffffff",
    paper_bgcolor: "#ffffff",
  };

  Plotly.newPlot("correlationChart", [trace], layout, { responsive: true, displayModeBar: true });
}

/**
 * Populate selectors for custom Chart Studio tab.
 */
function setupStudioSelectors(data) {
  const xSelect = document.getElementById("studioXSelect");
  const ySelect = document.getElementById("studioYSelect");
  xSelect.innerHTML = "";
  ySelect.innerHTML = "";

  const allCols = data.column_categories.all;
  const numCols = data.column_categories.numeric;

  allCols.forEach((col, idx) => {
    const optX = document.createElement("option");
    optX.value = col;
    optX.textContent = col;
    xSelect.appendChild(optX);

    const optY = document.createElement("option");
    optY.value = col;
    optY.textContent = col;
    ySelect.appendChild(optY);
  });

  // Default selection: pick numeric columns if possible
  if (numCols.length >= 2) {
    xSelect.value = numCols[0];
    ySelect.value = numCols[1];
  } else if (allCols.length >= 2) {
    xSelect.value = allCols[0];
    ySelect.value = allCols[1];
  }

  renderStudioChart();
}

/**
 * Render dynamic user-selected chart in Chart Studio.
 */
function renderStudioChart() {
  if (!currentAnalysis || !currentAnalysis.preview) return;

  const xCol = document.getElementById("studioXSelect").value;
  const yCol = document.getElementById("studioYSelect").value;
  const chartType = document.getElementById("studioChartType").value;
  const container = document.getElementById("studioChartContainer");

  const cols = currentAnalysis.preview.columns;
  const xIdx = cols.indexOf(xCol);
  const yIdx = cols.indexOf(yCol);

  if (xIdx === -1 || yIdx === -1) return;

  const rows = currentAnalysis.preview.rows;
  const xVals = [];
  const yVals = [];

  rows.forEach((r) => {
    if (r[xIdx] !== "" && r[yIdx] !== "") {
      xVals.push(r[xIdx]);
      yVals.push(r[yIdx]);
    }
  });

  container.innerHTML = "";
  const plotDiv = document.createElement("div");
  plotDiv.className = "w-full h-full";
  container.appendChild(plotDiv);

  let trace;
  if (chartType === "scatter") {
    trace = {
      x: xVals,
      y: yVals,
      mode: "markers",
      type: "scatter",
      marker: {
        color: "#0284c7",
        size: 7,
        opacity: 0.75,
        line: { color: "#0369a1", width: 1 },
      },
      hovertemplate: `${xCol}: %{x}<br>${yCol}: %{y}<extra></extra>`,
    };
  } else if (chartType === "bar") {
    trace = {
      x: xVals,
      y: yVals,
      type: "bar",
      marker: { color: "#6366f1" },
    };
  } else if (chartType === "box") {
    trace = {
      y: yVals,
      x: xVals,
      type: "box",
      marker: { color: "#059669" },
    };
  }

  const layout = {
    title: {
      text: `${yCol} vs. ${xCol}`,
      font: { size: 14, color: "#1e293b", weight: "bold" },
    },
    margin: { t: 40, r: 25, l: 60, b: 60 },
    xaxis: { title: xCol, tickfont: { size: 10, color: "#64748b" } },
    yaxis: { title: yCol, tickfont: { size: 10, color: "#64748b" } },
    plot_bgcolor: "#ffffff",
    paper_bgcolor: "#ffffff",
  };

  Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}

/**
 * Export computed summary statistics to CSV file.
 */
function exportSummaryCsv() {
  if (!currentAnalysis || !currentAnalysis.summary_statistics) return;
  const stats = currentAnalysis.summary_statistics;
  const headers = ["column", "dtype", "count", "null_count", "null_pct", "mean", "median", "skewness", "min", "max", "std", "q25", "q75"];
  
  let csvContent = headers.join(",") + "\n";
  stats.forEach((s) => {
    const row = headers.map((h) => {
      let v = s[h];
      if (v === null || v === undefined) return "";
      if (typeof v === "string" && v.includes(",")) return `"${v}"`;
      return v;
    });
    csvContent += row.join(",") + "\n";
  });

  downloadBlob(csvContent, `${currentAnalysis.file_name || 'dataset'}_summary_stats.csv`, "text/csv;charset=utf-8;");
}

/**
 * Export computed summary statistics to JSON file.
 */
function exportSummaryJson() {
  if (!currentAnalysis || !currentAnalysis.summary_statistics) return;
  const jsonContent = JSON.stringify(currentAnalysis.summary_statistics, null, 2);
  downloadBlob(jsonContent, `${currentAnalysis.file_name || 'dataset'}_summary_stats.json`, "application/json;charset=utf-8;");
}

function downloadBlob(content, fileName, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Render raw preview table (first 50 rows).
 */
function renderPreviewTable(data) {
  const thead = document.getElementById("previewTableHead");
  const tbody = document.getElementById("previewTableBody");
  const preview = data.preview;

  thead.innerHTML = "";
  tbody.innerHTML = "";

  document.getElementById("previewCountBadge").textContent = `${preview.preview_count} of ${data.kpis.total_rows.toLocaleString()} rows`;

  const headTr = document.createElement("tr");
  preview.columns.forEach((c) => {
    const th = document.createElement("th");
    th.className = "px-3 py-2.5 whitespace-nowrap bg-slate-100 text-slate-700 font-bold border-b border-slate-200";
    th.textContent = c;
    headTr.appendChild(th);
  });
  thead.appendChild(headTr);

  preview.rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 transition border-b border-slate-100";
    row.forEach((val) => {
      const td = document.createElement("td");
      td.className = "px-3 py-1.5 whitespace-nowrap";
      td.textContent = val;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}
