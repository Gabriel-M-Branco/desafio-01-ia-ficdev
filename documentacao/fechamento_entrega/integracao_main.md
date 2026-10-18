# Integração final da main — 18/10/2026

Base preservada: `3e3038869c3c2e0717fd5191dde7bb9eb977e480`.
Main analisada: `a61a3a42766884451a3c1c78f864f5e74384f0fb`, incluindo os cinco
commits f530926, b332b20, 443a07b, dadfd30 e a61a3a4 ainda ausentes da branch.

## Resolução por conteúdo

- `.env.example` e `.gitignore`: mantidos provedores validados, chave OpenRouter
  exclusiva, fallback explícito e exclusões das pastas privadas. Rejeitados STT
  OpenRouter padrão, TTS remoto padrão e aliases de chave/host que contrariavam a documentação.
- `src/main.py`: preservados schema estrito, reparação limitada, conferência das
  fontes, snapshots e arquivos únicos. Incorporadas rotas/favicon sem cache e
  identificação do provedor de imagem. Nenhuma habilitação administrativa RF10.
- `src/llm_client.py`: preservados autenticação, métricas nativas e erros seguros;
  incorporado Content-Type explícito. Timeout configurado em 60 s, com limite real.
- `src/pdf_generator.py`: mantida paginação testada, fontes e ausência de defaults
  inventados. Aproveitada normalização tipográfica; rejeitadas substituição semântica
  da instituição, remoção automática de conteúdo e paginação por altura estimada.
- Relatório técnico: preservada versão auditada; não incorporadas declarações de
  alucinação zero/completude ou novos resultados sem evidência verificável.
- Frontend: aproveitados favicon e agrupamento responsivo do topo, com escape dos
  valores dinâmicos. Tabela RF02 continua sem notas/tempos fixos e RF10 continua bloqueado.
- Testes: nome neutro `test_integracao_main.py`, conservando mocks completos da auditoria
  e isolamento de prompts da main. Runner offline e cobertura STT removidos na main
  foram preservados; imports e gerador da matriz apontam para o nome neutro.
- Prompts: aproveitada orientação de minimização, sem inventar documentos obrigatórios,
  frequência, datas ou autoridades. Isso não torna anônimo o payload enviado ao LLM.

## Mudanças rejeitadas por segurança e rastreabilidade

Não incorporados STT por API OpenRouter, comparação com entidades fixas caso falte
gabarito, criação de execução fictícia ao revisar ID inexistente, exclusão de OCRs/
transcrições anteriores, sobrescrita de matriz/saídas de experimento e orientações
institucionais fixas no RF10. O histórico continua distinguindo falha, pendência e aprovação.

Gabaritos anteriores foram conservados: a nova referência STT e mudanças em município/
assinatura OCR precisam conferência independente da equipe, não ajuste automático de
acurácia. Os números históricos 3/6, 0/23 e 22/23 não foram recalculados para esta integração.

Arquivos históricos rastreados foram retidos pelos blobs do commit anterior, sem
adicionar as alterações locais de audit_trail/teste_minuta nem registros privados.
Backups, inventário e worktree de integração permanecem locais e ignorados pelo Git.
Nenhuma chamada de IA ou aprovação real é necessária para validar este merge.

Validação isolada: 363 testes aprovados, 2 cenários OCR reais opt-in ignorados;
dois validadores DOM, Edge/ASGI com mocks em 390/1366 e `pip check` aprovados.
Esses testes não representam novas inferências nem decisões humanas reais.
