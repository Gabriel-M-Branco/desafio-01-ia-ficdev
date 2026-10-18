# Central Inteligente de Atendimento — GOV.MT

Protótipo para demonstração local, com provedores reais configuráveis e revisão humana obrigatória.

## Execução
Instalação no Windows (Python 3.11+):
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements-validado.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m pip check
```
Python 3.13 x64 é a referência testada. `requirements-validado.txt` restringe às versões
instaladas neste ambiente (inclusive transitivas); não é lock com hashes de wheels nem
prova de instalação limpa. Outras versões Python 3.11+ exigem validação própria.
Copie o exemplo somente na primeira instalação; preserve um `.env` já configurado.
Configure `OPENROUTER_API_KEY` e, para RF10, as três variáveis `CLOUDFLARE_*`.
Nunca compartilhe/versione credenciais. O exemplo mantém texto OpenRouter/Gemini,
STT local e TTS SAPI5; não habilita autenticação administrativa RF10.
Instale Tesseract OCR com `por.traineddata` em `C:\Program Files\Tesseract-OCR`
e habilite a voz Microsoft Maria (pt-BR) no Windows. O modelo
`Systran/faster-whisper-small` deve estar previamente no cache Hugging Face:
download manual, quando autorizado, com
`.\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small')"`.
O processamento RF06 usa somente o cache e não baixa modelos automaticamente.
Node.js é necessário apenas para os validadores frontend; Edge, para o teste de navegador.

Dependências: requirements.txt. Usar Python com as dependências da .venv existente.
Interface local: `.\.venv\Scripts\python.exe -m src.main --host 127.0.0.1 --port 8000`
Abrir http://127.0.0.1:8000. O badge consulta os provedores configurados no backend.
Testes offline: `.\.venv\Scripts\python.exe -B testes/executar_offline.py`
O executor usa arquivos temporários e bloqueia provedores externos; mocks são exclusivos dos testes.
DOM offline: `node testes/validar_interface_offline.cjs` e `node testes/validar_fluxos_web.cjs`.
Navegador real, sem APIs: `.\.venv\Scripts\python.exe -m testes.validar_navegador_local --executar`.
Esse teste usa Edge, viewport móvel/desktop e arquivos/aprovações fictícios em pasta temporária; não inicia a aplicação de produção.
Na interface: processar solicitação, conferir/editar minuta, informar justificativa e aprovar.
Ao selecionar áudio ou OCR no atendimento, confira o original, corrija o texto e use
"Confirmar dados críticos na fonte" com justificativa. A geração da minuta exige o hash
desse texto confirmado; editar o texto exige nova conferência. Isso não aprova a minuta para TTS.
Só então gerar TTS; qualquer edição posterior exige nova aprovação. Salvar correções não equivale a aprovar.
Erros de API aparecem com status HTTP; falhas de geração nunca produzem respostas fictícias.

## Funcionalidades e limites reais
- RF06: faster-whisper small/CPU/int8/pt ou HF; bruto/revisado, metadados, referência e auditoria. Sem fallback fictício.
  Validação real final informada pelo operador: após reiniciar/liberar memória, passou pela
  interface em `http://127.0.0.1:8000`, usando faster-whisper small local, CPU/int8.
  O áudio de 89,16 s produziu transcrição; 3/6 entidades críticas foram conferidas.
  A revisão humana permanece obrigatória; sucesso de processamento não significa fidelidade integral.
  A falha anterior `mkl_malloc: failed to allocate memory` foi superada nessa execução;
  memória disponível continua necessária. Em nova falta de memória, o backend registra a causa e retorna HTTP 503.
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

## Auditoria final e entrega
Consulte [o relatório adversarial](documentacao/auditoria_final/relatorio_final.md),
[a matriz por bullet](documentacao/auditoria_final/matriz_rastreabilidade.csv) e
[o roteiro de 12 minutos](documentacao/auditoria_final/roteiro_demonstracao.md).
Versões do ambiente validado: [restrições de dependências](requirements-validado.txt).
Essas versões registram o ambiente testado, sem garantir uma instalação nova com versões futuras.
FFmpeg de linha de comando não é chamado pelo STT local: a decodificação usa PyAV;
não confundir essa biblioteca com a exigência adicional de Tesseract para OCR.
RF07: voz Maria, velocidade normal (Rate=0) e volume 100; beneficia leitura de texto,
mas não comprova qualidade auditiva, compreensão, entonação expressiva ou atendimento universal de acessibilidade.
Use apenas dados fictícios e servidor em `127.0.0.1`. As outras APIs também não têm
autenticação do grupo; não expor `--host 0.0.0.0` em rede pública. O bloqueio RF10 permanece ativo.
O padrão da CLI agora é loopback; no Compose a porta também fica restrita a `127.0.0.1`.
`HOST`, `PORT` e `DEBUG` não são lidos do `.env`; use as flags CLI documentadas.
`EXECUTION_MODE=mock` bloqueia LLM/geração de imagem; não significa que STT/OCR/TTS
viraram mocks ou que motores locais estão desligados. Para testes sem processamento real,
use o executor offline, que substitui os provedores e bloqueia transportes.
Editar uma entrada textual controlada muda o caso para personalizado: o gabarito antigo
não deve avaliar outro texto. A comparação OCR é da origem; não comparar seus campos
`nome`/`ch` diretamente com `solicitante`/`carga_horaria` do JSON de minuta.
A minimização antes do LLM é parcial: o texto fictício é enviado ao provedor; a máscara
na tela não anonimiza o payload. Aprovação textual é uma deliberação local declarada,
não autenticação de identidade. O histórico de decisões novas é preservado.
Consulte `/api/qualidade/revisoes` para contagens e taxa; a base histórica pode misturar
testes antigos e execuções reais e não deve ser apresentada como amostra controlada.
O `--run-all` executa etapas automáticas; não substitui revisão humana, não aprova minutas
e não gera imagem implicitamente. Para a banca, use o fluxo manual documentado.
O ZIP final exigido pelo enunciado ainda precisa ser montado e revisado: inclua resultados
reais selecionados, sem `.env`, caches, backups, registros de identidade Windows ou dados reais.
O ZIP complementar privado de credenciais não é um entregável apropriado ao professor.

### Fechamento da entrega

Siga a [ordem de ações humanas](documentacao/fechamento_entrega/LEIA-ME.md), a
[avaliação RF02](documentacao/fechamento_entrega/rf02_avaliacao.md), o
[checklist de máquina limpa](documentacao/fechamento_entrega/maquina_limpa.md) e o
[procedimento de ZIP seguro](documentacao/fechamento_entrega/zip_final.md).
A ferramenta `python -m ferramentas.fechar_entrega` apenas planeja/valida/empacota;
não executa provedores ou decisões. A ficha RF13 vazia não conta como avaliação.
O [plano de minimização](documentacao/fechamento_entrega/lgpd_minimizacao.md)
explicita que mascaramento visual não anonimiza o texto enviado ao LLM.
Na conferência de áudio/OCR, é possível rejeitar a leitura sem gerar minuta.

## Integração da main (17/10/2026)
Incorporadas melhorias de portabilidade do Tesseract, dependências OCR no Docker,
responsividade, formatação visual de identificadores e testes temporários.
A formatação do painel não altera JSON, minuta, métricas ou aprovação.
Referências RF02 são históricas, sem tempos ou ranking presumidos.
Rejeitados preenchimento fixo de OCR, parser permissivo, STT OpenRouter e geração
implícita de imagem pelo pipeline. Gabaritos e evidências anteriores preservados.
