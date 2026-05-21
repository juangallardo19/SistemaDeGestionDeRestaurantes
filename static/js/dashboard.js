'use strict';

/* =========================================================
   RestaurApp — Dashboard JS
   Requiere: Chart.js 4, DASH_CONFIG global (definido en el template)
   ========================================================= */

/* ---------------------------------------------------------
   Paleta de colores del restaurante
   --------------------------------------------------------- */
const WARM = {
  naranja:    '#D4700A',
  dorado:     '#E8892A',
  tostado:    '#B85D08',
  terracota:  '#C17A3A',
  ocre:       '#F0A050',
  marron:     '#8B4513',
  crema:      '#D4A96A',
};

const WARM_LIST = [
  WARM.naranja, WARM.dorado, WARM.tostado,
  WARM.terracota, WARM.ocre, WARM.marron, WARM.crema,
];

const ESTADO_COLORS = {
  Pendiente:        '#F59E0B',
  'En preparación': '#3B82F6',
  Listo:            '#10B981',
  Entregado:        '#9CA3AF',
  Cancelado:        '#EF4444',
};

/* ---------------------------------------------------------
   Detectar tema activo y obtener colores para Chart.js
   --------------------------------------------------------- */
function getThemeColors() {
  const dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
  return {
    grid:    dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)',
    tick:    dark ? '#B8946A' : '#6B5444',
    text:    dark ? '#F5EDE0' : '#1A0F08',
    bg:      dark ? '#2C1A0E' : '#FFFFFF',
    tooltip: dark ? '#3A2215' : '#FFFFFF',
  };
}

/* ---------------------------------------------------------
   Registro de gráficos para re-renderizado al cambiar tema
   --------------------------------------------------------- */
const chartRegistry = {};

/**
 * Crear o recrear un gráfico.
 * @param {string}   canvasId
 * @param {string}   type       - 'bar' | 'line' | 'doughnut'
 * @param {string[]} labels
 * @param {object[]} datasets   - array de datasets Chart.js
 * @param {object}   extraOpts  - opciones adicionales (merge profundo simple)
 * @returns {Chart|null}
 */
function initChart(canvasId, type, labels, datasets, extraOpts = {}) {
  const existing = chartRegistry[canvasId];
  if (existing?.instance) {
    existing.instance.destroy();
  }

  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const t = getThemeColors();

  const defaultOpts = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500 },
    plugins: {
      legend: {
        labels: {
          color: t.tick,
          font: { family: "'DM Sans', system-ui, sans-serif", size: 12 },
          boxWidth: 14,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: t.tooltip,
        titleColor: t.text,
        bodyColor: t.tick,
        borderColor: 'rgba(212,112,10,0.3)',
        borderWidth: 1,
        padding: 10,
        callbacks: {},
      },
    },
    scales: type !== 'doughnut' ? {
      x: {
        grid:  { color: t.grid },
        ticks: { color: t.tick, font: { size: 11 } },
      },
      y: {
        grid:  { color: t.grid },
        ticks: { color: t.tick, font: { size: 11 } },
        beginAtZero: true,
      },
    } : undefined,
  };

  // Merge superficial de opciones extra sobre defaults
  const mergedOpts = deepMerge(defaultOpts, extraOpts);

  const config = { type, data: { labels, datasets }, options: mergedOpts };
  const instance = new Chart(canvas, config);

  // Guardar en registro para recrear al cambiar tema
  chartRegistry[canvasId] = {
    instance,
    recreate: () => initChart(canvasId, type, labels, datasets, extraOpts),
  };

  return instance;
}

/**
 * Merge profundo simple (2 niveles).
 */
function deepMerge(target, source) {
  const out = Object.assign({}, target);
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      out[key] = deepMerge(target[key] || {}, source[key]);
    } else {
      out[key] = source[key];
    }
  }
  return out;
}

/* ---------------------------------------------------------
   Overlay spinner helpers
   --------------------------------------------------------- */
function showOverlay(overlayId) {
  const el = document.getElementById(overlayId);
  if (el) { el.classList.remove('hidden'); el.hidden = false; }
}

function hideOverlay(overlayId) {
  const el = document.getElementById(overlayId);
  if (el) el.classList.add('hidden');
}

function showChartError(overlayId, msg) {
  const el = document.getElementById(overlayId);
  if (!el) return;
  el.innerHTML = `<div class="chart-error">
    <i class="bi bi-wifi-off d-block fs-2 mb-2"></i>${msg}
  </div>`;
  el.classList.remove('hidden');
  el.hidden = false;
}

/* ---------------------------------------------------------
   Fetch genérico con async/await
   --------------------------------------------------------- */
async function fetchJSON(url) {
  const response = await fetch(url, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/* ---------------------------------------------------------
   Formatear moneda local (COP / ARS — sin decimales)
   --------------------------------------------------------- */
function formatearMoneda(valor) {
  return new Intl.NumberFormat('es-CO', {
    style:    'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(valor);
}

/* ---------------------------------------------------------
   Gráfico 1: Barras horizontales — platos más vendidos
   --------------------------------------------------------- */
async function cargarPlatosVendidos() {
  try {
    const data = await fetchJSON(DASH_CONFIG.urls.platos);
    hideOverlay('overlay-platos');

    const labels  = data.labels  || [];
    const valores = data.valores || data.values || [];

    initChart('grafico-platos', 'bar', labels, [{
      label:           'Unidades vendidas',
      data:            valores,
      backgroundColor: WARM_LIST.slice(0, labels.length),
      borderRadius:    6,
      borderSkipped:   false,
    }], {
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.x} unidades`,
          },
        },
      },
      scales: {
        x: { grid: { color: getThemeColors().grid }, ticks: { color: getThemeColors().tick } },
        y: { grid: { display: false }, ticks: { color: getThemeColors().tick, font: { size: 12 } } },
      },
    });
  } catch (err) {
    showChartError('overlay-platos', 'No se pudieron cargar los platos vendidos.');
    console.error('[Dashboard] platos:', err);
  }
}

/* ---------------------------------------------------------
   Gráfico 2: Línea suavizada — ingresos por mes
   --------------------------------------------------------- */
async function cargarIngresosMes() {
  try {
    const data = await fetchJSON(DASH_CONFIG.urls.ingresos);
    hideOverlay('overlay-ingresos');

    const labels  = data.labels  || [];
    const valores = data.valores || data.values || [];
    const t = getThemeColors();

    initChart('grafico-ingresos', 'line', labels, [{
      label:           'Ingresos',
      data:            valores,
      borderColor:     WARM.naranja,
      backgroundColor: 'rgba(212,112,10,0.12)',
      pointBackgroundColor: WARM.naranja,
      pointBorderColor:     '#fff',
      pointBorderWidth:     2,
      pointRadius:          4,
      fill:      true,
      tension:   0.4,
    }], {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ' ' + formatearMoneda(ctx.parsed.y),
          },
        },
      },
      scales: {
        x: { grid: { color: t.grid }, ticks: { color: t.tick } },
        y: {
          grid:  { color: t.grid },
          ticks: { color: t.tick, callback: v => formatearMoneda(v) },
        },
      },
    });
  } catch (err) {
    showChartError('overlay-ingresos', 'No se pudieron cargar los ingresos.');
    console.error('[Dashboard] ingresos:', err);
  }
}

/* ---------------------------------------------------------
   Gráfico 3: Doughnut — pedidos por estado
   --------------------------------------------------------- */
async function cargarPedidosEstado() {
  try {
    const data = await fetchJSON(DASH_CONFIG.urls.estados);
    hideOverlay('overlay-estados');

    const labels  = data.labels  || [];
    const valores = data.valores || data.values || [];

    const colors = labels.map(
      l => ESTADO_COLORS[l] || WARM_LIST[labels.indexOf(l) % WARM_LIST.length]
    );

    initChart('grafico-estados', 'doughnut', labels, [{
      data:            valores,
      backgroundColor: colors,
      borderWidth:     2,
      borderColor:     getThemeColors().bg,
      hoverOffset:     6,
    }], {
      cutout: '62%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: getThemeColors().tick, padding: 12, boxWidth: 12 },
        },
      },
    });
  } catch (err) {
    showChartError('overlay-estados', 'No se pudieron cargar los estados.');
    console.error('[Dashboard] estados:', err);
  }
}

/* ---------------------------------------------------------
   Gráfico 4: Barras verticales — reservas por mes
   --------------------------------------------------------- */
async function cargarReservasMes() {
  try {
    const data = await fetchJSON(DASH_CONFIG.urls.reservas);
    hideOverlay('overlay-reservas');

    const labels  = data.labels  || [];
    const valores = data.valores || data.values || [];
    const t = getThemeColors();

    initChart('grafico-reservas', 'bar', labels, [{
      label:           'Reservas',
      data:            valores,
      backgroundColor: 'rgba(212,112,10,0.75)',
      borderColor:     WARM.naranja,
      borderWidth:     1,
      borderRadius:    4,
    }], {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: t.tick } },
        y: { grid: { color: t.grid }, ticks: { color: t.tick, stepSize: 1 } },
      },
    });
  } catch (err) {
    showChartError('overlay-reservas', 'No se pudieron cargar las reservas.');
    console.error('[Dashboard] reservas:', err);
  }
}

/* ---------------------------------------------------------
   Tabla de ocupación de mesas
   --------------------------------------------------------- */
async function cargarOcupacion() {
  const spinner   = document.getElementById('ocupacion-spinner');
  const container = document.getElementById('ocupacion-container');
  const errorEl   = document.getElementById('ocupacion-error');
  const tbody     = document.getElementById('ocupacion-tbody');

  try {
    const data = await fetchJSON(DASH_CONFIG.urls.ocupacion);

    if (spinner)   spinner.hidden = true;
    if (container) container.hidden = false;

    const mesas = data.mesas || [];

    if (!tbody) return;
    tbody.innerHTML = '';

    if (mesas.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No hay datos de ocupación.</td></tr>';
      return;
    }

    mesas.forEach(mesa => {
      const pct      = Math.min(parseFloat(mesa.porcentaje) || 0, 100);
      const pctInt   = Math.round(pct);
      let barClass   = 'bg-success';
      if (pct < 30) barClass = 'bg-danger';
      else if (pct < 70) barClass = 'bg-warning';

      const tr = document.createElement('tr');
      tr.className = 'mesa-row';
      tr.innerHTML = `
        <td class="px-3 fw-semibold">Mesa ${mesa.numero}</td>
        <td class="text-muted small">${mesa.ubicacion || '—'}</td>
        <td class="text-center">${mesa.capacidad || '—'}</td>
        <td class="text-center fw-medium">${mesa.pedidos_mes ?? '—'}</td>
        <td>
          <div class="progress rounded-pill" style="height:8px;" title="${pctInt}%">
            <div class="progress-bar ${barClass}"
                 role="progressbar"
                 style="width:${pct}%;transition:width .8s var(--ease-out);"
                 aria-valuenow="${pctInt}" aria-valuemin="0" aria-valuemax="100">
            </div>
          </div>
        </td>
        <td class="text-end pe-3 fw-semibold small">${pctInt}%</td>`;
      tbody.appendChild(tr);
    });

  } catch (err) {
    if (spinner)   spinner.hidden = true;
    if (errorEl)   errorEl.hidden = false;
    console.error('[Dashboard] ocupacion:', err);
  }
}

/* ---------------------------------------------------------
   Modal de exportación
   --------------------------------------------------------- */
function initExportModal() {
  const modal        = document.getElementById('exportModal');
  const modalTitle   = document.getElementById('exportModalTitle');
  const desdeInput   = document.getElementById('exportFechaDesde');
  const hastaInput   = document.getElementById('exportFechaHasta');
  const errorEl      = document.getElementById('exportError');
  const confirmarBtn = document.getElementById('exportConfirmarBtn');

  let currentUrl = '';

  // Botones de exportación
  document.querySelectorAll('[data-export-url]').forEach(btn => {
    btn.addEventListener('click', () => {
      currentUrl = btn.dataset.exportUrl;
      const label = btn.dataset.exportLabel || 'Exportar reporte';
      if (modalTitle) modalTitle.textContent = label;
      if (errorEl)    errorEl.hidden = true;

      // Presetear fechas (mes actual)
      const hoy = new Date();
      const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
      if (desdeInput) desdeInput.value = primerDia.toISOString().split('T')[0];
      if (hastaInput) hastaInput.value = hoy.toISOString().split('T')[0];

      bootstrap.Modal.getOrCreateInstance(modal).show();
    });
  });

  // Confirmar descarga
  if (confirmarBtn) {
    confirmarBtn.addEventListener('click', () => {
      const desde = desdeInput?.value;
      const hasta = hastaInput?.value;

      if (!desde || !hasta) {
        if (errorEl) errorEl.hidden = false;
        return;
      }
      if (errorEl) errorEl.hidden = true;

      const url = `${currentUrl}?fecha_desde=${desde}&fecha_hasta=${hasta}`;
      window.location.href = url;
      bootstrap.Modal.getInstance(modal)?.hide();
    });
  }
}

/* ---------------------------------------------------------
   Re-renderizar gráficos cuando cambia el tema
   --------------------------------------------------------- */
function updateChartsTheme() {
  Object.values(chartRegistry).forEach(entry => {
    if (typeof entry.recreate === 'function') entry.recreate();
  });
}

/* ---------------------------------------------------------
   Inicialización al cargar el DOM
   --------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {

  // Escuchar el botón de toggle de tema (definido en main.js)
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      // Esperar a que main.js aplique el nuevo atributo data-bs-theme
      setTimeout(updateChartsTheme, 60);
    });
  }

  // Cargar todos los gráficos en paralelo
  Promise.allSettled([
    cargarPlatosVendidos(),
    cargarIngresosMes(),
    cargarPedidosEstado(),
    cargarReservasMes(),
    cargarOcupacion(),
  ]);

  // Inicializar modal de exportación
  initExportModal();
});
