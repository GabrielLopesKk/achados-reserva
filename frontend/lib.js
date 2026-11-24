// Funções puras do front-end (testáveis sem navegador).

export const STATUS_LABELS = {
  found: "Encontrado",
  awaiting_pickup: "Aguardando retirada",
  returned: "Devolvido",
};

export function statusLabel(status) {
  return STATUS_LABELS[status] ?? status;
}

/** Monta a query string ignorando filtros vazios. */
export function buildQuery(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    const clean = String(value ?? "").trim();
    if (clean) search.set(key, clean);
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export function scoreLabel(score) {
  const pct = Math.round(score * 100);
  if (pct >= 70) return `${pct}% — muito provável`;
  if (pct >= 50) return `${pct}% — provável`;
  return `${pct}% — possível`;
}

/** Valida o formulário de interesse antes de enviar. Retorna lista de erros. */
export function validateClaim({ name, contact }) {
  const errors = [];
  if (String(name ?? "").trim().length < 2) errors.push("Informe seu nome.");
  if (String(contact ?? "").trim().length < 5) errors.push("Informe um e-mail ou telefone.");
  return errors;
}

export function formatDate(iso) {
  const [y, m, d] = String(iso).slice(0, 10).split("-");
  return d && m && y ? `${d}/${m}/${y}` : String(iso);
}
