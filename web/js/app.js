(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);

  const statusEl = $("#status");
  const resultsEl = $("#results");

  function showStatus(message, isError = false) {
    statusEl.hidden = false;
    statusEl.textContent = message;
    statusEl.classList.toggle("is-error", isError);
  }

  function hideStatus() {
    statusEl.hidden = true;
    statusEl.textContent = "";
    statusEl.classList.remove("is-error");
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderReferences(refs, totalHint) {
    resultsEl.innerHTML = "";
    if (!refs.length) {
      resultsEl.innerHTML = '<p class="hint">未返回条目。</p>';
      return;
    }
    if (typeof totalHint === "number" && totalHint > refs.length) {
      showStatus(`约 ${totalHint.toLocaleString()} 条命中，当前展示前 ${refs.length} 条。`);
    } else {
      hideStatus();
    }

    const frag = document.createDocumentFragment();
    for (const r of refs) {
      const authors = Array.isArray(r.authors) ? r.authors.join("；") : "";
      const year = r.year != null ? String(r.year) : "年份未知";
      const venue = r.venue ? escapeHtml(r.venue) : "";
      const doi = r.doi ? escapeHtml(r.doi) : "";
      const url = r.url ? escapeHtml(r.url) : "";
      const title = escapeHtml(r.title || "");
      const card = document.createElement("article");
      card.className = "ref-card";
      card.innerHTML = `
        <header>
          <span class="ref-id">#${escapeHtml(String(r.id))}</span>
        </header>
        <h4 class="ref-title">${title}</h4>
        <p class="ref-authors">${escapeHtml(authors)}</p>
        <p class="ref-meta">
          <span>${escapeHtml(year)}</span>
          ${venue ? `<span>${venue}</span>` : ""}
          ${doi ? `<span>DOI: ${doi}</span>` : ""}
        </p>
        <div class="ref-actions">
          ${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer">打开链接</a>` : ""}
        </div>
      `;
      frag.appendChild(card);
    }
    resultsEl.appendChild(frag);
  }

  async function apiSearch(query, rows) {
    const u = new URL("/api/crossref/search", window.location.origin);
    u.searchParams.set("query", query);
    u.searchParams.set("rows", String(rows));
    const res = await fetch(u.toString(), { headers: { Accept: "application/json" } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.error?.message || res.statusText || "请求失败");
    return data;
  }

  async function apiDoi(doi) {
    const u = new URL("/api/crossref/doi", window.location.origin);
    u.searchParams.set("doi", doi);
    const res = await fetch(u.toString(), { headers: { Accept: "application/json" } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.error?.message || res.statusText || "请求失败");
    return data;
  }

  $("#form-search").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    hideStatus();
    resultsEl.innerHTML = "";
    const query = $("#q").value.trim();
    const rows = parseInt($("#rows").value, 10) || 10;
    showStatus("检索中…");
    try {
      const data = await apiSearch(query, rows);
      renderReferences(data.references || [], data.total_results);
      if (!data.references || !data.references.length) {
        showStatus("未找到匹配的文献条目。");
      }
    } catch (e) {
      showStatus(e.message || String(e), true);
      resultsEl.innerHTML = "";
    }
  });

  $("#form-doi").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    hideStatus();
    resultsEl.innerHTML = "";
    const doi = $("#doi").value.trim();
    showStatus("解析 DOI…");
    try {
      const data = await apiDoi(doi);
      renderReferences(data.references || []);
      hideStatus();
      if (!data.references || !data.references.length) {
        showStatus("未解析到文献。");
      }
    } catch (e) {
      showStatus(e.message || String(e), true);
      resultsEl.innerHTML = "";
    }
  });

  /** Tabs */
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panelId = btn.getAttribute("data-panel");
      document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("is-active", b === btn));
      document.querySelectorAll(".panel").forEach((p) => {
        const show = p.id === panelId;
        p.classList.toggle("is-visible", show);
        p.hidden = !show;
      });
    });
  });

  /** Draft area: load .txt into textarea */
  const draftText = $("#draft-text");
  const draftFile = $("#draft-file");
  const draftMeta = $("#draft-meta");

  draftFile.addEventListener("change", () => {
    const file = draftFile.files && draftFile.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      draftText.value = String(reader.result || "");
      draftMeta.textContent = `已载入「${file.name}」，${draftText.value.length} 字`;
    };
    reader.onerror = () => {
      draftMeta.textContent = "读取文件失败";
    };
    reader.readAsText(file, "UTF-8");
    draftFile.value = "";
  });

  draftText.addEventListener("input", () => {
    if (!draftMeta.textContent.startsWith("已载入")) draftMeta.textContent = "";
  });
})();
