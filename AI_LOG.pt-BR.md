[English](AI_LOG.md) · [Português (Brasil)](AI_LOG.pt-BR.md)

# Registro de uso de IA

Regra: registrem o que a IA gerou, o que conferimos e o que corrigimos. Ninguém apresenta código que não consegue explicar.

## IA no produto

| Onde | O que a IA faz | Proteção |
|---|---|---|
| `POST /api/ai/describe` | Olha a foto e sugere tipo, cor, marcas, uma frase de descrição e um alerta de dado sensível | Sempre devolvida com `needs_review: true`. O formulário exige o checkbox "Revisei" antes de salvar. A saída é validada contra listas fixas (valores desconhecidos viram `outro` / `outra`). |
| Alerta de foto sensível | A IA sinaliza documentos, cartões ou rostos | Fotos sinalizadas ficam ocultas ao público. O prompt proíbe identificar pessoas ou transcrever números e nomes. |
| `matching.py` (não é LLM) | Ordena candidatos para um relato de perda | Pontuação determinística, só sugestões. O dono ainda passa pelo código de retirada e pela conferência no balcão. |
| Sem chave de API ou erro na API | Cai para um analisador local de cor | A interface avisa que só a cor foi sugerida. |

## IA no processo

| Data | Ferramenta | Objetivo | O que gerou | O que conferimos ou corrigimos | Revisado por |
|---|---|---|---|---|---|
| 23/11/2026 | Claude (Anthropic) | Primeira estrutura a partir do briefing | API Flask, esquema SQLite, cruzamento, privacidade, front-end estático, workflow de CI, scripts, docs (EN e pt-BR) | Rodou 19 testes do back-end e 5 do front-end, um smoke test do servidor e `node --check`. Corrigido na geração: o comando de teste do Node (`node --test tests/` falhava, agora `node --test`), um parâmetro sem uso e o nome de um teste. | _time: preencham_ |

### Ainda não verificado (lista honesta)

- O `ruff check` e o workflow do GitHub Actions foram escritos, mas **não foram executados** no ambiente que os gerou. Rodem no primeiro PR e corrijam o que aparecer.
- A chamada à API da Anthropic **não foi testada com a API real**. Testem com uma chave e algumas fotos reais, conferindo o parse do JSON e o alerta de sensível.
- A interface não foi testada em navegador pelo gerador. Naveguem pelas quatro abas no desktop e no celular.
- O `setup-github.sh` não foi executado. Confiram a proteção da `main` e o acesso do professor nas configurações do repositório.

### Modelo para novas entradas

| Data | Ferramenta | Objetivo | O que gerou | O que conferimos ou corrigimos | Revisado por |
|---|---|---|---|---|---|
| | | | | | |

## Aprendizados (preencham antes da demo)

- Onde a IA nos poupou tempo?
- Onde ela errou ou foi confiante demais, e como percebemos?
