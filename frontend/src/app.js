const API = "/api";

const state = { fileA: null, fileB: null, jobId: null };

function bindDropzone(zoneId, inputId, key) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => setFile(zone, input.files[0], key));
  zone.addEventListener("dragover", (e) => e.preventDefault());
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) setFile(zone, e.dataTransfer.files[0], key);
  });
}

function setFile(zone, file, key) {
  if (!file) return;
  state[key] = file;
  zone.classList.add("hasfile");
  zone.innerHTML = `<b>${file.name}</b><br><small>${(file.size / 1024 / 1024).toFixed(1)} MB</small>`;
  document.getElementById("compare-btn").disabled = !(state.fileA && state.fileB);
}

bindDropzone("drop-a", "file-a", "fileA");
bindDropzone("drop-b", "file-b", "fileB");

const statusEl = document.getElementById("status");

document.getElementById("compare-btn").addEventListener("click", async () => {
  const btn = document.getElementById("compare-btn");
  btn.disabled = true;
  statusEl.textContent = "Uploading…";
  try {
    const form = new FormData();
    form.append("file_a", state.fileA);
    form.append("file_b", state.fileB);
    const up = await fetch(`${API}/upload`, { method: "POST", body: form });
    if (!up.ok) throw new Error((await up.json()).detail || "upload failed");
    const { job_id } = await up.json();
    state.jobId = job_id;

    statusEl.textContent = "Comparing… (extracting entities and matching)";
    const cmp = await fetch(`${API}/compare/${job_id}`, { method: "POST" });
    if (!cmp.ok) throw new Error((await cmp.json()).detail || "compare failed");
    const job = await cmp.json();
    if (job.status === "failed") throw new Error(job.error || "comparison failed");

    statusEl.textContent = "Done.";
    renderResults(job);
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
});

function renderResults(job) {
  for (const id of ["viz-card", "stats-card", "summary-card"])
    document.getElementById(id).classList.remove("hidden");

  setVizMode("bbox");

  const s = job.stats;
  document.getElementById("stat-tiles").innerHTML = `
    <div class="stat"><b>${s.total_regions}</b><span>total changes</span></div>
    <div class="stat"><b>${s.added_count}</b><span>added</span></div>
    <div class="stat"><b>${s.removed_count}</b><span>removed</span></div>
    <div class="stat"><b>${s.moved_count}</b><span>moved</span></div>
    <div class="stat"><b>${s.modified_count}</b><span>modified</span></div>
    <div class="stat"><b>${(s.total_changed_area_fraction * 100).toFixed(1)}%</b><span>area changed</span></div>`;

  document.getElementById("region-rows").innerHTML = s.per_region
    .slice(0, 100)
    .map(
      (r) => `<tr>
        <td><span class="chip ${r.change_type}">${r.change_type}</span></td>
        <td>${r.kind}</td>
        <td>${r.location}</td>
        <td>${(r.area_fraction * 100).toFixed(2)}%</td>
        <td>${r.detail || r.label || ""}</td>
      </tr>`
    )
    .join("");

  document.getElementById("summary-text").textContent = job.summary;
  document.getElementById("notes").innerHTML = (job.diff_result.notes || [])
    .map((n) => `<div class="note">⚠ ${n}</div>`)
    .join("");
}

document.getElementById("viz-tabs").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-mode]");
  if (btn) setVizMode(btn.dataset.mode);
});

function setVizMode(mode) {
  document
    .querySelectorAll("#viz-tabs button")
    .forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  document.getElementById("viz-img").src =
    `${API}/jobs/${state.jobId}/visualization?mode=${mode}&t=${Date.now()}`;
}
