/**
 * Report Framework Components
 * Vanilla JS components for rendering report sections
 */

// ── Utility Functions ───────────────────────────────────
export function fmtN(n) {
  return new Intl.NumberFormat('ru-RU').format(n);
}

export function fmtP(pct) {
  return (pct ?? 0).toFixed(2) + '%';
}

export function fmtMs(ms) {
  if (ms == null) return '—';
  return ms < 1 ? ms.toFixed(2) + ' ms' : ms.toFixed(0) + ' ms';
}

export function getColorClass(score) {
  if (score >= 0.8) return 'sc-hi';
  if (score >= 0.5) return 'sc-md';
  return 'sc-lo';
}

// ── KPI Card Component ──────────────────────────────────
export function renderKPI(label, value, subtext = '', colorClass = 'g') {
  return `
    <div class="kpi ${colorClass}">
      <div class="kpi-l">${label}</div>
      <div class="kpi-v">${value}</div>
      ${subtext ? `<div class="kpi-s">${subtext}</div>` : ''}
    </div>
  `;
}

// ── KPI Grid Component ──────────────────────────────────
export function renderKPIGrid(kpis) {
  return `
    <div class="g4">
      ${kpis.map(kpi => renderKPI(kpi.label, kpi.value, kpi.subtext, kpi.color)).join('')}
    </div>
  `;
}

// ── Progress Bar Row Component ──────────────────────────
export function renderBarRow(label, pct, value, color = '#21A038') {
  const safePct = Math.min(100, Math.max(0, pct || 0));
  return `
    <div class="br">
      <div class="br-l">${label}</div>
      <div class="br-t"><div class="br-f" style="width:${safePct}%;background:${color}"></div></div>
      <div class="br-v">${value}</div>
    </div>
  `;
}

// ── Fill Section Component ──────────────────────────────
export function renderFillSection(fillSummary) {
  const { key, category, synonyms } = fillSummary || {};
  
  let html = '<div class="g3">';
  
  // Key field
  if (key) {
    html += `
      <div class="card">
        <div class="card-h">Ключевое поле</div>
        <div class="card-b">
          ${renderBarRow('Заполнено', key.filled_pct, fmtN(key.filled), '#21A038')}
          ${renderBarRow('Пустые', key.empty / (key.filled + key.empty) * 100 || 0, fmtN(key.empty), '#d0021b')}
        </div>
      </div>
    `;
  }
  
  // Synonyms
  if (synonyms) {
    html += `
      <div class="card">
        <div class="card-h">Синонимы</div>
        <div class="card-b">
          ${renderBarRow('Много синонимов', synonyms.many_pct, fmtN(synonyms.many_synonyms), '#21A038')}
          ${renderBarRow('1 синоним', synonyms.one_pct, fmtN(synonyms.one_synonym), '#f5a623')}
          ${renderBarRow('Нет синонимов', synonyms.missing_pct, fmtN(synonyms.missing), '#d0021b')}
        </div>
      </div>
    `;
  }
  
  // Stats
  if (synonyms?.length_stats) {
    const stats = synonyms.length_stats;
    html += `
      <div class="card">
        <div class="card-h">Статистика</div>
        <div class="card-b">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
            <div><strong>Min:</strong> ${stats.min}</div>
            <div><strong>Max:</strong> ${stats.max}</div>
            <div><strong>Avg:</strong> ${stats.avg?.toFixed(2)}</div>
            <div><strong>P50:</strong> ${stats.p50}</div>
          </div>
        </div>
      </div>
    `;
  }
  
  html += '</div>';
  return html;
}

// ── Category Stats Component ────────────────────────────
export function renderCategoryStats(categoryStats) {
  if (!categoryStats) return '<div>Нет данных</div>';
  
  const categories = Object.entries(categoryStats);
  
  return categories.map(([catName, data]) => {
    const count = data.count || 0;
    const avgSyn = data.syn_length_stats?.avg?.toFixed(2) || 0;
    
    return `
      <div class="card">
        <div class="card-h">${catName}</div>
        <div class="card-b">
          <div class="kpi g" style="margin-bottom:12px">
            <div class="kpi-l">Записей</div>
            <div class="kpi-v">${fmtN(count)}</div>
          </div>
          <div style="font-size:12px;color:var(--mu)">
            <div>Среднее кол-во синонимов: <strong>${avgSyn}</strong></div>
            <div>Без синонимов: <strong>${data.no_synonyms || 0}</strong></div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ── Synonym Distribution Component ──────────────────────
export function renderSynonymDistribution(dist) {
  if (!dist || dist.length === 0) return '<div>Нет данных</div>';
  
  const maxVal = Math.max(...dist.map(d => d.entries));
  
  return dist.map(d => {
    const label = d.count === 0 ? '0 синонимов' 
              : d.count === 1 ? '1 синоним' 
              : `${d.count} синонимов`;
    const color = d.count === 0 ? '#d0021b' 
              : d.count === 1 ? '#f5a623' 
              : '#21A038';
    const pct = maxVal > 0 ? (d.entries / maxVal * 100) : 0;
    
    return renderBarRow(label, pct, `${fmtN(d.entries)} (${fmtP(d.pct)})`, color);
  }).join('');
}

// ── Entry Card Component ────────────────────────────────
export function renderEntryCard(entry, accentColor = '#21A038') {
  const synonyms = entry.synonyms || [];
  const displaySyns = synonyms.slice(0, 8);
  
  return `
    <div class="sq" style="margin-bottom:10px">
      <div class="sq-body">
        <div class="sq-r" style="border-left:3px solid ${accentColor}">
          <div style="font-weight:600;font-size:13px;margin-bottom:4px">${entry.key}</div>
          <div style="font-size:11px;color:var(--mu);margin-bottom:6px">
            <span class="bdg bdg-ci">${entry.category}</span>
            <span style="margin-left:8px">${synonyms.length} синонимов</span>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:4px">
            ${displaySyns.map(s => `<span class="syn-tag" style="background:var(--wh);border:1px solid var(--br);border-radius:14px;padding:2px 9px;font-size:12px">${s}</span>`).join('')}
            ${synonyms.length > 8 ? `<span style="font-size:11px;color:var(--lt)">+ещё ${synonyms.length - 8}</span>` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

// ── Search Results Component ────────────────────────────
export function renderSearchResults(vectorSearchData) {
  const { aggregate_metrics, queries } = vectorSearchData || {};
  const agg = aggregate_metrics || {};
  const lat = agg.latency || {};
  const sc = agg.top1_score || {};
  
  let html = '';
  
  // Aggregate metrics card
  html += `
    <div class="card" style="margin-bottom:16px">
      <div class="card-h">Агрегированные метрики</div>
      <div class="card-b">
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--br);font-size:12px">
          <span>Avg latency</span>
          <span style="font-weight:600">${fmtMs(lat.avg_ms)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--br);font-size:12px">
          <span>P50</span>
          <span style="font-weight:600">${fmtMs(lat.p50_ms)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--br);font-size:12px">
          <span>P90</span>
          <span style="font-weight:600">${fmtMs(lat.p90_ms)}</span>
        </div>
        ${sc.avg != null ? `
        <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px">
          <span>Avg top1 score</span>
          <span style="font-weight:600">${sc.avg.toFixed(4)}</span>
        </div>` : ''}
      </div>
    </div>
  `;
  
  // Query cards
  if (queries && queries.length > 0) {
    html += queries.map(q => {
      const ms = q.metrics || {};
      const results = q.top_results || [];
      
      return `
        <div class="sq" style="margin-bottom:10px">
          <div class="sq-h">
            <div class="sq-n">${q.query_num}</div>
            <div class="sq-t">${q.query_text}</div>
            <div class="sq-ms">
              <div class="sq-m">embed <strong>${fmtMs(ms.embed_ms)}</strong></div>
              <div class="sq-m">search <strong>${fmtMs(ms.search_ms)}</strong></div>
              ${ms.top1_score != null ? `<div class="sq-m">top1 <strong style="color:var(--g)">${ms.top1_score.toFixed(4)}</strong></div>` : ''}
            </div>
          </div>
          <div class="sq-body">
            ${results.map((r, j) => `
              <div class="sq-r">
                <div class="sq-r-top">
                  <div class="sq-rk">${j + 1}.</div>
                  <div class="sq-nm">${r.key}</div>
                  <span class="bdg bdg-ci">${r.category}</span>
                  ${r.score != null ? `<div class="sq-sc ${getColorClass(r.score)}">${r.score.toFixed(4)}</div>` : ''}
                </div>
                <div style="font-family:monospace;font-size:10px;color:var(--lt);margin-top:3px">${r.id}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');
  }
  
  return html;
}

// ── Table Component ─────────────────────────────────────
export function renderTable(columns, rows) {
  return `
    <table>
      <thead>
        <tr>
          ${columns.map(col => `<th>${col.header}</th>`).join('')}
        </tr>
      </thead>
      <tbody>
        ${rows.map(row => `
          <tr>
            ${columns.map(col => `<td>${row[col.key]}</td>`).join('')}
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// ── Chart Helper (Chart.js wrapper) ─────────────────────
export function initChart(canvasId, config) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded');
    return null;
  }
  
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  
  return new Chart(ctx, {
    type: config.type || 'bar',
    data: config.data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: config.showLegend !== false
        }
      },
      ...config.options
    }
  });
}

// ── Navigation Handler ──────────────────────────────────
export function initNavigation() {
  document.querySelectorAll('.nav-a').forEach(a => {
    a.addEventListener('click', function(e) {
      e.preventDefault();
      const el = document.getElementById(this.dataset.sec);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
      document.querySelectorAll('.nav-a').forEach(x => x.classList.remove('on'));
      this.classList.add('on');
    });
  });
}

// ── Animate Bars ────────────────────────────────────────
export function animateBars() {
  setTimeout(() => {
    document.querySelectorAll('.br-f, .fg-bar').forEach(el => {
      const w = el.style.width;
      el.style.width = '0';
      requestAnimationFrame(() => {
        el.style.transition = 'width .7s cubic-bezier(.4,0,.2,1)';
        el.style.width = w;
      });
    });
  }, 100);
}
