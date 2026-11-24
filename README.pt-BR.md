[English](README.md) · [Português (Brasil)](README.pt-BR.md)

# Achados e Perdidos

Hack com IA: Codando com Inteligência · Senac na Prática · TDS · Canoas

Um sistema web simples para registrar, descrever e encontrar objetos perdidos no campus do Senac. A foto de um item encontrado passa pela IA, que sugere uma descrição estruturada (tipo, cor, marcas visíveis). Uma pessoa revisa antes de publicar. Quem perdeu pode buscar, demonstrar interesse e retirar o item com um código de uso único, sem que telefone ou documento apareçam em uma lista pública.

## Funcionalidades (MVP)

| Requisito | Onde |
|---|---|
| Registrar item encontrado (foto, data, local aproximado, status inicial) | `POST /api/items`, aba "Achei algo" |
| Descrição por IA a partir da foto, revisada por uma pessoa | `POST /api/ai/describe`, checkbox de revisão obrigatório |
| Registrar relato de perda | `POST /api/reports`, aba "Perdi algo" |
| Buscar e filtrar por tipo, cor, local e palavras | `GET /api/items`, aba "Procurar" |
| Fluxo de interesse e devolução, sem dados de contato públicos | `POST /api/items/<id>/claims` + código de retirada |
| Atualizar status (encontrado, aguardando retirada, devolvido) | `PATCH /api/items/<id>/status` (só recepção) |
| Extra: candidatos sugeridos para um relato de perda | `GET /api/reports/<id>/matches` |
| Extra: alerta e ocultação de foto sensível | documentos, cartões e rostos ficam ocultos ao público |

## Como rodar

Requisitos: Python 3.12+ e Node 22+ (só para os testes do front-end).

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export STAFF_TOKEN="um-token-longo-e-aleatorio"   # acesso da recepção
export ANTHROPIC_API_KEY="..."                    # opcional, veja abaixo
python wsgi.py                                    # http://localhost:5000
```

O Flask serve a API e o front-end estático, então um comando sobe tudo. Sem `ANTHROPIC_API_KEY` o app continua funcionando: a etapa de IA usa um analisador local que sugere só a cor dominante, e a pessoa preenche o resto.

## Testes, lint e CI

```bash
cd backend  && python -m unittest discover -s tests -t . && ruff check .
cd frontend && npm run lint && npm test
```

O GitHub Actions (`.github/workflows/ci.yml`) roda build, lint e testes do back-end e do front-end em todo PR e na `main`, além da checagem de Conventional Commits nos PRs.

## Configuração do repositório (dia 1)

```bash
gh auth login
scripts/setup-github.sh DONO/REPO   # adiciona o professor como colaborador e protege a main
```

## Estrutura

```
backend/   API Flask, SQLite, integração com IA, cruzamento, privacidade, testes
frontend/  HTML/CSS/módulos ES estáticos, lógica pura em lib.js com testes
scripts/   Configuração do GitHub e checagem de commits
```

## Privacidade desde o projeto

- Contatos são guardados, mas nunca devolvidos por endpoints públicos. A recepção vê o contato mascarado (`a***@mail.com`, `••••-1234`).
- Códigos de retirada e tokens de relato são guardados apenas como hash SHA-256.
- As fotos são reencodadas no upload, o que remove dados EXIF como a localização GPS.
- Fotos de documentos, cartões e rostos só são entregues à recepção.
- Itens saem da busca pública após 90 dias (`VISIBILITY_DAYS`) ou quando devolvidos.
- A saída da IA é sempre uma sugestão: nada é publicado sem uma pessoa confirmar.

## Time

Preencham aqui nomes, papéis e usuários do GitHub.
