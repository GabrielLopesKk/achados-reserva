import { buildQuery, formatDate, scoreLabel, statusLabel, validateClaim } from "./lib.js";

const $ = (sel, root = document) => root.querySelector(sel);
let staffToken = sessionStorage.getItem("staffToken") || "";

/** Cria elementos com textContent (nunca innerHTML) para evitar XSS. */
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined) el.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c !== null && c !== undefined) el.append(c);
  return el;
}

async function api(path, options = {}) {
  const res = await fetch(path, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || "Algo deu errado. Tente novamente.");
  return body;
}

function notify(message) {
  const box = $("#notice");
  box.textContent = message;
  box.hidden = !message;
  if (message) box.scrollIntoView({ block: "nearest" });
}

function fillSelect(select, values, withAny) {
  select.replaceChildren(...(withAny ? [h("option", { value: "" }, "Todos")] : []),
    ...values.map((v) => h("option", { value: v }, v)));
}

// ---------- abas ----------
$("#tabs").addEventListener("click", (e) => {
  const tab = e.target.dataset.tab;
  if (!tab) return;
  for (const b of document.querySelectorAll("#tabs button")) b.setAttribute("aria-selected", String(b === e.target));
  for (const s of document.querySelectorAll("main > section")) s.hidden = s.id !== `tab-${tab}`;
  notify("");
});

// ---------- cartão do item ----------
function itemCard(item, actions = []) {
  const photo = item.photo_url
    ? h("img", { src: item.photo_url, alt: `Foto: ${item.item_type} ${item.color}`, loading: "lazy" })
    : h("div", { class: "noimg" }, "Foto oculta: contém dados pessoais");
  return h("article", { class: "tag" }, photo,
    h("h3", {}, `${item.item_type} · ${item.color}`),
    h("span", { class: `badge ${item.status}` }, statusLabel(item.status)),
    h("p", {}, item.description),
    item.marks ? h("p", { class: "hint" }, `Marcas: ${item.marks}`) : null,
    h("p", { class: "hint" }, `${item.location} · ${formatDate(item.found_date)}`),
    ...actions);
}

// ---------- busca ----------
async function search() {
  const params = Object.fromEntries(new FormData($("#search-form")));
  const { items } = await api(`/api/items${buildQuery(params)}`);
  const box = $("#results");
  if (!items.length) {
    box.replaceChildren(h("p", { class: "empty" },
      "Nada encontrado com esses filtros. Tente menos palavras ou registre o que você perdeu na aba \"Perdi algo\"."));
    return;
  }
  box.replaceChildren(...items.map((it) => itemCard(it, [
    h("button", { class: "primary", onclick: () => openClaim(it.id) }, "É meu"),
  ])));
}
$("#search-form").addEventListener("submit", (e) => { e.preventDefault(); search().catch((err) => notify(err.message)); });

// ---------- interesse ----------
let claimItemId = null;
function openClaim(id) { claimItemId = id; $("#claim-dialog").showModal(); }
$("#claim-cancel").addEventListener("click", () => $("#claim-dialog").close());
$("#claim-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  const errors = validateClaim(data);
  if (errors.length) return notify(errors.join(" "));
  try {
    const res = await api(`/api/items/${claimItemId}/claims`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    $("#claim-dialog").close();
    e.target.reset();
    $("#results").prepend(h("div", { class: "alert empty" },
      "Interesse registrado. Leve este código à recepção junto com um documento com foto:",
      h("div", { class: "code" }, res.pickup_code),
      "Guarde-o: ele não será mostrado de novo."));
    notify("");
    search();
  } catch (err) { notify(err.message); }
});

// ---------- achei algo ----------
const foundForm = $("#found-form");
let aiSource = "none";
foundForm.photo.addEventListener("change", async () => {
  const file = foundForm.photo.files[0];
  if (!file) return;
  const status = $("#ai-status");
  status.hidden = false;
  status.textContent = "A IA está analisando a foto…";
  try {
    const fd = new FormData();
    fd.append("photo", file);
    const s = await api("/api/ai/describe", { method: "POST", body: fd });
    aiSource = s.source;
    foundForm.item_type.value = s.type;
    foundForm.color.value = s.color;
    foundForm.marks.value = s.marks.join(", ");
    foundForm.description.value = s.description;
    foundForm.sensitive.checked = s.sensitive;
    $("#sensitive-alert").hidden = !s.sensitive;
    status.textContent = s.source === "anthropic"
      ? "Sugestão da IA. Revise e corrija antes de registrar."
      : "Sem IA de visão disponível: só a cor foi sugerida. Complete os campos.";
  } catch (err) { status.textContent = err.message; }
});
foundForm.sensitive.addEventListener("change", () => { $("#sensitive-alert").hidden = !foundForm.sensitive.checked; });
foundForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(foundForm);
  fd.delete("reviewed");
  fd.set("sensitive", foundForm.sensitive.checked ? "true" : "false");
  fd.set("ai_source", aiSource);
  try {
    await api("/api/items", { method: "POST", body: fd });
    foundForm.reset();
    $("#ai-status").hidden = true;
    $("#sensitive-alert").hidden = true;
    notify("Item registrado. Leve o objeto à recepção. Obrigado!");
  } catch (err) { notify(err.message); }
});

// ---------- perdi algo ----------
$("#lost-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target));
  try {
    const { id, token } = await api("/api/reports", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    e.target.reset();
    notify("Relato registrado.");
    await showMatches(id, token);
  } catch (err) { notify(err.message); }
});
async function showMatches(id, token) {
  const { candidates, note } = await api(`/api/reports/${id}/matches`, { headers: { "X-Report-Token": token } });
  const box = $("#report-result");
  if (!candidates.length) {
    box.replaceChildren(h("p", { class: "empty" }, "Nenhum item parecido por enquanto. Volte a procurar nos próximos dias."));
    return;
  }
  box.replaceChildren(h("h3", {}, "Itens que podem ser o seu"), h("p", { class: "hint" }, note),
    h("div", { class: "tags" }, candidates.map((c) => itemCard(c.item, [
      h("p", { class: "badge" }, scoreLabel(c.score)),
      h("button", { class: "primary", onclick: () => openClaim(c.item.id) }, "É meu")]))));
}

// ---------- recepção ----------
async function staffFetch(path, options = {}) {
  return api(path, { ...options, headers: { ...(options.headers || {}), "X-Staff-Token": staffToken } });
}
async function staffPhoto(img, url) {
  const res = await fetch(url, { headers: { "X-Staff-Token": staffToken } });
  if (res.ok) img.src = URL.createObjectURL(await res.blob());
}
async function loadStaff() {
  const { items } = await staffFetch("/api/staff/items");
  const box = $("#staff-list");
  if (!items.length) { box.replaceChildren(h("p", { class: "empty" }, "Nenhum item em aberto.")); return; }
  box.replaceChildren(...items.map(staffCard));
}
function staffCard(item) {
  const card = itemCard({ ...item, photo_url: null }, []);
  if (item.photo_url) {
    const img = h("img", { alt: `Foto: ${item.item_type}` });
    card.prepend(img);
    card.querySelector(".noimg")?.remove();
    staffPhoto(img, item.photo_url);
  }
  const claims = h("div", { class: "hint" });
  const code = h("input", { placeholder: "Código de retirada", "aria-label": "Código de retirada" });
  const statusSel = h("select", { "aria-label": "Status" },
    ["found", "awaiting_pickup"].map((s) => h("option", { value: s, selected: s === item.status ? "" : null }, statusLabel(s))));
  statusSel.addEventListener("change", () => setStatus(item.id, statusSel.value));
  card.append(claims, statusSel, code,
    h("button", { class: "primary", onclick: () => setStatus(item.id, "returned", code.value) }, "Confirmar devolução"));
  staffFetch(`/api/staff/items/${item.id}/claims`).then(({ claims: list }) => {
    claims.textContent = list.length
      ? list.map((c) => `${c.name} (${c.contact_masked})`).join("; ")
      : "Sem interessados ainda.";
  }).catch(() => {});
  return card;
}
async function setStatus(id, status, codeValue) {
  try {
    await staffFetch(`/api/items/${id}/status`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, code: codeValue }) });
    notify(status === "returned" ? "Devolução registrada." : "Status atualizado.");
    await loadStaff();
  } catch (err) { notify(err.message); }
}
$("#staff-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  staffToken = new FormData(e.target).get("token");
  try { await loadStaff(); sessionStorage.setItem("staffToken", staffToken); notify(""); }
  catch (err) { staffToken = ""; notify(err.message); }
});

// ---------- início ----------
(async function init() {
  const meta = await api("/api/meta");
  for (const form of document.querySelectorAll("form")) {
    const any = form.id === "search-form";
    if (form.type) fillSelect(form.type, meta.types, any);
    if (form.item_type) fillSelect(form.item_type, meta.types, false);
    if (form.color) fillSelect(form.color, meta.colors, any);
    if (form.location) fillSelect(form.location, meta.locations, any);
  }
  const today = new Date().toISOString().slice(0, 10);
  for (const input of document.querySelectorAll("input[type=date]")) { input.value = today; input.max = today; }
  if (staffToken) loadStaff().catch(() => { staffToken = ""; });
  search().catch((err) => notify(err.message));
})();
