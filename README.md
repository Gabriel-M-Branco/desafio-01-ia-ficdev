# Central Inteligente de Atendimento — integração em validação

Cópia isolada: origin/main 90a9b69 + trabalho local de fix/multimodal-emilly.
Nada aplicado à branch original. Sem .env, credenciais ou .git nesta cópia.

## Execução
Dependências: requirements.txt. Usar Python com as dependências da .venv existente.
Interface: python -m src.main
Testes offline: python -B testes/executar_offline.py
O executor usa arquivos temporários e bloqueia provedores externos; mocks são exclusivos dos testes.

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
OpenRouter opcional: OPENROUTER_ENABLED=false; modelo configurável com sufixo :free. Disponibilidade não garantida.
HF/Cloudflare podem ter quotas, créditos e cobrança; custo desconhecido permanece não informado.
Nenhuma API real ou modelo executado/baixado na integração. Novos testes reais dependem de autorização separada.
Não copiar/versionar .env. .env.example contém somente configuração não secreta.

## Evidências e implantação
dados/originais imutáveis; dados/gabaritos contém referências, não saídas de modelo.
Artefatos locais originais preservados. Evidências remotas em evidencias_origin_main, sem fusão destrutiva das trilhas.
Documentação anterior em evidencias_documentacao_anterior como histórico; métricas antigas não comprovam esta integração.
Novos processamentos textuais e experimentos usam nomes exclusivos.
Docker/Linux necessita OCR, fontes e TTS compatível; SAPI5 depende de Windows. Docker não validado.
Pendências: autenticação do grupo, revisão humana real do RF10, validação visual da interface e qualidade do PDF oficial.
