[English](DECISIONS.md) · [Português (Brasil)](DECISIONS.pt-BR.md)

# Decisões

Formato: contexto, decisão, motivo. Acrescentem uma entrada com data sempre que o time mudar de rumo.

## D1. Escopo do MVP (dia 1)

**Entra:** registrar item encontrado com foto, data, local e status; descrição por IA com revisão humana obrigatória; relatos de perda; busca com filtros; fluxo de interesse e devolução; atualização de status; painel da recepção.
**Extras incluídos por serem baratos:** cruzamento de candidatos para um relato; alerta de foto sensível.
**Fica de fora por ora:** notificações por push ou e-mail, mapa de locais, comprovante com QR, contas de usuário.
**Fora de escopo (do briefing):** logística pelos Correios, pagamento ou leilão, reconhecimento facial, boletim de ocorrência.
**Por quê:** um fluxo completo e demonstrável vale mais do que uma lista longa pela metade.

## D2. Stack

- **Back-end: Python + Flask + SQLite.** Superfície pequena, um processo, nenhuma configuração para a demo, fácil de testar com `unittest` e o cliente de teste do Flask.
- **Front-end: HTML/CSS estáticos e módulos ES, sem framework nem bundler.** Não há o que compilar, então CI e onboarding ficam simples. A lógica testável fica em `lib.js` e roda com `node --test`.
- **IA: API Messages da Anthropic com bloco de imagem, com fallback local.** A visão dá atributos úteis (tipo, marcas). O fallback mantém o produto usável sem internet ou sem chave.
- **Trade-off:** sem ORM e sem framework SPA. Se o time passar do limite, migrem primeiro a camada de dados.

## D3. Como saber que é a pessoa certa na retirada?

Demonstrar interesse gera um **código de retirada** de uso único, mostrado uma vez a quem pediu e guardado só como hash. A recepção devolve o item apenas depois de digitar esse código (e deve também conferir um documento com foto). O contato nunca aparece em público e a recepção o vê mascarado.
**Limite:** o código prova a posse do código, não a identidade. A conferência do documento no balcão é a proteção real.

## D4. Fotos com documentos, cartões ou rostos

A IA sinaliza e a pessoa também pode marcar "contém documento". Essas fotos ficam ocultas na busca pública e só são entregues com o token da recepção. Documentos e cartões são sempre tratados como sensíveis pelo tipo. As fotos são reencodadas para remover EXIF.
**Não feito:** não detectamos rostos por conta própria (fora de escopo); contamos com o alerta da IA e o checkbox humano.

## D5. Quem guarda o objeto físico?

A recepção guarda todos os itens. Quem achou é orientado a deixar lá e não tem responsabilidade depois. O status no sistema espelha o estado físico.

## D6. Por quanto tempo o item fica visível?

90 dias (`VISIBILITY_DAYS`) desde o registro, ou até ser devolvido. A recepção continua vendo os itens em aberto. O destino dos objetos não retirados depois disso é uma política do campus, fora deste software.

## D7. Busca quando a pessoa lembra pouco

Todos os filtros são opcionais, a busca por texto ignora acentos, e um relato de perda devolve **candidatos** ordenados por tipo, cor, local e palavras em comum. Candidatos são sugestões: a pessoa ainda precisa pedir o item e passar pela conferência na retirada.

## D8. Autenticação da recepção

Um único `STAFF_TOKEN` compartilhado, enviado em um header. Simples de propósito para um MVP de uma semana.
**Limite conhecido:** sem contas individuais, sem log de auditoria e sem limite de requisições. São as primeiras coisas a adicionar para produção.

## D9. Processo

Pull requests com 1 revisão, `main` protegida, Conventional Commits, CI em PRs e na `main`. Configurado por `scripts/setup-github.sh`.
