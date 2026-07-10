const grid = document.getElementById("grid");
const statusEl = document.getElementById("status");
const loadMoreBtn = document.getElementById("load-more");
const qInput = document.getElementById("q");
const noteInput = document.getElementById("note");
const dialog = document.getElementById("detail-dialog");
const detailContent = document.getElementById("detail-content");

const PAGE_SIZE = 24;
let offset = 0;
let total = 0;
let debounceTimer = null;

function currentParams() {
  return { q: qInput.value.trim(), note: noteInput.value.trim() };
}

async function search(reset) {
  if (reset) {
    offset = 0;
    grid.innerHTML = "";
  }
  const params = new URLSearchParams({
    ...currentParams(),
    limit: PAGE_SIZE,
    offset,
  });
  statusEl.textContent = "Loading…";
  const res = await fetch(`/api/search?${params}`);
  const data = await res.json();
  total = data.total;
  offset += data.results.length;
  data.results.forEach(renderCard);
  statusEl.textContent = `${total.toLocaleString()} fragrance${total === 1 ? "" : "s"} found`;
  loadMoreBtn.hidden = offset >= total;
}

function renderCard(frag) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <h3>${escapeHtml(frag.name)}</h3>
    <div class="brand">${escapeHtml(frag.brand || "Unknown brand")}${
      frag.release_year ? " · " + frag.release_year : ""
    }</div>
    ${
      frag.rating_value
        ? `<div class="rating">★ ${frag.rating_value.toFixed(2)} <span class="rating-count">(${(frag.rating_count ?? 0).toLocaleString()})</span></div>`
        : `<div class="rating placeholder">No rating yet</div>`
    }
    ${frag.price_avg ? `<div class="price">avg $${frag.price_avg.toFixed(2)}</div>` : ""}
    <div class="pills">
      ${frag.main_accords
        .slice(0, 4)
        .map((a) => `<span class="pill">${escapeHtml(a)}</span>`)
        .join("")}
    </div>
  `;
  card.addEventListener("click", () => openDetail(frag.id));
  grid.appendChild(card);
}

async function openDetail(id) {
  const res = await fetch(`/api/fragrance/${id}`);
  const f = await res.json();

  const noteSection = (title, notes) => `
    <div class="note-section">
      <h4>${title}</h4>
      ${
        notes.length
          ? `<div class="pills">${notes
              .map((n) => `<span class="pill">${escapeHtml(n)}</span>`)
              .join("")}</div>`
          : `<div class="placeholder">Not available</div>`
      }
    </div>
  `;

  const seasonHtml = f.season
    ? `<div class="pills"><span class="pill">${escapeHtml(f.season)}</span></div>`
    : `<div class="placeholder">Not yet available</div>`;

  const priceHtml = f.price_avg
    ? `<div>Avg: $${f.price_avg.toFixed(2)} <span class="rating-count">(low $${f.price_low.toFixed(2)} · high $${f.price_high.toFixed(2)})</span></div>`
    : `<div class="placeholder">Not yet available</div>`;

  detailContent.innerHTML = `
    <h2>${escapeHtml(f.name)}</h2>
    <div class="brand">${escapeHtml(f.brand || "Unknown brand")}${
      f.release_year ? " · " + f.release_year : ""
    }${f.concentration ? " · " + escapeHtml(f.concentration) : ""}</div>
    ${
      f.rating_value
        ? `<div>Rating: ${f.rating_value.toFixed(2)} (${f.rating_count ?? 0} votes)</div>`
        : ""
    }
    ${noteSection("Main accords", f.main_accords)}
    ${noteSection("Top notes", f.top_notes)}
    ${noteSection("Middle notes", f.middle_notes)}
    ${noteSection("Base notes", f.base_notes)}
    <div class="note-section">
      <h4>Best seasons</h4>
      ${seasonHtml}
    </div>
    <div class="note-section">
      <h4>Price (low / avg / high)</h4>
      ${priceHtml}
    </div>
    ${
      f.perfumers.length
        ? `<div class="note-section"><h4>Perfumer(s)</h4><div>${escapeHtml(f.perfumers.join(", "))}</div></div>`
        : ""
    }
    ${f.url ? `<div class="note-section"><a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">View on Parfumo →</a></div>` : ""}
  `;
  dialog.showModal();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => search(true), 250);
}

qInput.addEventListener("input", debouncedSearch);
noteInput.addEventListener("input", debouncedSearch);
loadMoreBtn.addEventListener("click", () => search(false));
document.getElementById("close-dialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (e) => {
  if (e.target === dialog) dialog.close();
});

search(true);
