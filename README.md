# Central Inteligente de Atendimento — GOV.MT

Protótipo para demonstração local, com provedores reais configuráveis e revisão humana obrigatória.

## Execução
Dependências: requirements.txt. Usar Python com as dependências da .venv existente.
Interface local: `.\.venv\Scripts\python.exe -m src.main --host 127.0.0.1 --port 8000`
Abrir http://127.0.0.1:8000. O badge consulta os provedores configurados no backend.
Testes offline: python -B testes/executar_offline.py
O executor usa arquivos temporários e bloqueia provedores externos; mocks são exclusivos dos testes.
DOM offline: `node testes/validar_interface_offline.cjs` e `node testes/validar_fluxos_web.cjs`.
Navegador real, sem APIs: `.\.venv\Scripts\python.exe -m testes.validar_navegador_local --executar`.
Esse teste usa Edge, viewport móvel/desktop e arquivos/aprovações fictícios em pasta temporária; não inicia a aplicação de produção.
Na interface: processar solicitação, conferir/editar minuta, informar justificativa e aprovar.
Só então gerar TTS; qualquer edição posterior exige nova aprovação. Salvar correções não equivale a aprovar.
Erros de API aparecem com status HTTP; falhas de geração nunca produzem respostas fictícias.

## Funcionalidades e limites reais
- RF06: faster-whisper small/CPU/int8/pt ou HF; bruto/revisado, metadados, referência e auditoria. Sem fallback fictício.
- RF07: SAPI5/Microsoft Maria no Windows; edge-tts opcional. Texto aprovado por hash, áudio verdadeiro e validação de saída.
- RF08: PyMuPDF/Tesseract português, alternativas Pillow/PSM e regiões. Preserva versões, divergências e JSON; ausentes permanecem “não localizado”. PDF oficial de baixa qualidade exige revisão humana.
- RF10: Cloudflare Workers AI/HF/endpoint compatível. Pillow somente compõe/corrige, sem substituir IA. Preservados bruto, prompt, hashes, fonte Unicode, brasão, tarja e auditoria.
- Texto: parser local dinâmico é extração regex, distinto da geração real de LLM. Sem credencial, timeout ou resposta inválida não há minuta simulada.
- Avaliação: fidelidade compara referência; conformidade verifica presença/formato. Gabaritos prévios da equipe preservados.
- Interface: painel de conferência, filtros, responsividade. Correções exigem valor conferido pelo humano, não copiam descrições de formato.

## Segurança
Não existe autenticação de usuários do grupo. Geração/revisão/download administrativo RF10 desabilitados por padrão (503).
exigir_revisor_imagem é o ponto de integração da segurança do grupo, com identidade autenticada e permissão rf10:revisar.
operador não autentica; overrides de teste não podem ir para produção.
Publicação em /api/publicacao/imagem/{id} exige última revisão autenticada e SHA-256 dos bytes atuais.
Rejeição ou adulteração bloqueia acesso. /arquivos não entrega imagens RF10; não há mounts /dados ou /resultados.
Pipeline não aprova/rejeita em nome do humano e não gera imagem implicitamente.

## Provedores e custos
Texto RF02/RF09: `TEXT_PROVIDER=openrouter`, `OPENROUTER_MODEL=google/gemini-3.8-flash` e chave no `.env` local.
Esse modelo consome saldo OpenRouter. `TEXT_FALLBACK_PROVIDER=none` desativa fallback.
RF09 solicita JSON Schema estrito, valida as chaves e usa limite de saída de pelo menos 4096 tokens.
Resposta inválida permite apenas uma correção de formato auditada, também sujeita a cobrança; nova falha mantém HTTP 502.
Diagnósticos brutos de falhas ficam em `.llm-diagnosticos/`, fora do Git e do acesso HTTP; não compartilhar essa pasta.
Hugging Face é opção configurável; `OPENROUTER_ENABLED` habilita apenas o fallback legado a partir dele.
HF/Cloudflare podem ter quotas, créditos e cobrança; custo desconhecido permanece não informado.
Testes automatizados usam transportes simulados; chamadas reais dependem de autorização e configuração local.
Não copiar/versionar .env. .env.example contém somente configuração não secreta.

## Evidências e implantação
dados/originais imutáveis; dados/gabaritos contém referências, não saídas de modelo.
Artefatos locais originais preservados. Evidências remotas em evidencias_origin_main, sem fusão destrutiva das trilhas.
Documentação anterior em evidencias_documentacao_anterior como histórico; métricas antigas não comprovam esta integração.
Novos processamentos textuais e experimentos usam nomes exclusivos.
Docker/Linux necessita OCR, fontes e TTS compatível; SAPI5 depende de Windows. Docker não validado.
RF10 no navegador continua bloqueado por falta de autenticação real. O [executor Windows isolado](documentacao/teste_local_rf10.md)
é exclusivo para testes e não concede acesso às rotas normais. Não há publicação automática.
Pendências: autenticação do grupo, revisão das saídas reais e qualidade do PDF oficial.

## Integração da main (17/10/2026)
Incorporadas melhorias de portabilidade do Tesseract, dependências OCR no Docker,
responsividade, formatação visual de identificadores e testes temporários.
A formatação do painel não altera JSON, minuta, métricas ou aprovação.
Referências RF02 são históricas, sem tempos ou ranking presumidos.
Rejeitados preenchimento fixo de OCR, parser permissivo, STT OpenRouter e geração
implícita de imagem pelo pipeline. Gabaritos e evidências anteriores preservados.
