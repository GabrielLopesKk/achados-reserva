#!/usr/bin/env bash
# Configura o repositório no GitHub: professor como colaborador e proteção da main.
# Uso: scripts/setup-github.sh DONO/REPO   (requer GitHub CLI autenticado: gh auth login)
set -euo pipefail
repo="${1:?Informe DONO/REPO}"

gh api -X PUT "repos/$repo/collaborators/adrianoanschau@gmail.com" -f permission=push \
  || echo "Se falhar por e-mail, convide o professor pelo nome de usuário no GitHub."

gh api -X PUT "repos/$repo/branches/main/protection" --input - <<JSON
{
  "required_status_checks": {"strict": true, "contexts": [
    "Back-end (build, lint, testes)", "Front-end (build, lint, testes)"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 1},
  "restrictions": null
}
JSON
echo "main protegida: PR com 1 aprovação e CI verde obrigatórios."
