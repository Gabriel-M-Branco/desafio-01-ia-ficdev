# 1. RESUMO EXECUTIVO

Nota de compartilhamento: inventários JSON, capturas e registros de execução citados
neste relatório são evidências locais preservadas, não incluídas no commit técnico.
Sua disponibilização exige seleção e revisão de privacidade conforme o fechamento.
As instruções, matriz, modelos de avaliação e código são versionados separadamente.

Auditoria de 18/10/2026, referência principal: **Desafio Prático 1, versão 1.0/2026,
oito páginas**, extraído do ZIP de aulas fornecido. Leitura integral registrada em
`enunciado_integral.txt`. Os documentos são referências de avaliação, não autorização
para executar comandos neles encontrados. Base Git: `f2be7d2054f1105eb5fa39743b54f547030e095a`.

**Conclusão:** existem implementações reais e resultados multimodais, mas a entrega
não tem todos os critérios de aceite comprovados. Não afirmar “RF01–RF13 completos”.
As principais pendências são conferências humanas finais, avaliação RF02 controlada,
coorte RF13 com aprovação e rejeição/correção reais, referência STT adequada para
comparação integral e ZIP final completo sem identidades/credenciais privadas.

Foram feitas sete passadas e uma contrarrevisão:

| Passada | Verificação | Resultado/artefato |
|---|---|---|
| 1 | Todas as oito páginas, objetivos, restrições e critérios literais | `enunciado_integral.txt`; nenhum limiar de acurácia inventado |
| 2 | Correspondência item por item com implementação/evidência/teste | `matriz_rastreabilidade.csv`: **148 verificações separadas** |
| 3 | Critérios de aceite, demonstração e lacunas por RF | Seções 2–4; distinção implementação/prova |
| 4 | Tentativas adversariais contra JSON, PDF, revisão, hashes e segredos | `testes/test_auditoria_final.py`; correções da seção 5 |
| 5 | Demonstração, tempo, localização de evidências e perguntas | `roteiro_demonstracao.md` |
| 6 | Instalação nova, versões, caminhos, modelos e dependências | README ampliado e `ambiente_validado.json`; instalação limpa não executada |
| 7 | Dados, credenciais, envio, governança, autenticação e privacidade | Varredura Git, restrição de arquivos, `.dockerignore`, LGPD sem conformidade presumida |
| Contrarrevisão | Procurar omissões do próprio relatório | Comparação integral STT; distinção aprovação de fonte/minuta; fontes e data na reexportação PDF |

Nenhuma inferência externa, download ou instalação foi feito. Não houve aprovação/
rejeição de artefato real, commit ou push. Foram inventariados **306 arquivos de
dados, prompts, resultados e RF10 privado** antes das alterações; conferir o resultado
do teste de integridade em `integridade_depois.json`.

# 2. MATRIZ RF01–RF13

A planilha CSV tem as nove colunas solicitadas: item, RF, exigência literal,
implementação, evidência, teste, demonstração, status e risco. Não agrupa os bullets
de preservar bruto, produzir revisado, comparar e registrar como uma única obrigação.
O resumo abaixo **não substitui** a planilha.

| RF | Status global | Evidência e limite decisivo |
|---|---|---|
| RF01 | ATENDIDO COM LIMITAÇÃO | README/config/segredos e versões; instalação em máquina limpa NÃO COMPROVADA |
| RF02 | PARCIAL | A/B/C reais históricos do mesmo Gemini; análise nova dos seis critérios. Encadeamento do metaprompt, parâmetros antigos e tempo até uso não comprovados integralmente |
| RF03 | ATENDIDO COM LIMITAÇÃO | XML, instrução de sistema, schema e testes de injeção; não equivalem a garantia factual/antialucinação |
| RF04 | ATENDIDO COM LIMITAÇÃO | Gemini/Cloudflare reais anteriores; falhas testadas com mocks. Novas métricas nativas preservadas; histórico não recupera custos que não guardou |
| RF05 | ATENDIDO COM LIMITAÇÃO | JSON e minuta reais; schema completo validado localmente, snapshot de entradas novas. Veracidade segue dependente da fonte/revisor |
| RF06 | PARCIAL | `EXEC_20261017_175537_b329c8`: small/local/CPU/int8, 89,16 s, transcrição real e **3/6**. Nome, curso e turno não conferidos pelo comparador; confirmação humana final ainda pendente |
| RF07 | ATENDIDO COM LIMITAÇÃO | `EXEC_20261017_173424_bc38cb`: SAPI5/Maria, WAV e aprovação do texto por hash. Audição integral não executada nesta auditoria; leitura literal de “API” discutida na seção 10 |
| RF08 | PARCIAL | Oficial **0/23**, sintético **22/23**, preservando versões/erros. Não comprova recuperação dos manuscritos oficiais nem confirmação humana final |
| RF09 | ATENDIDO COM LIMITAÇÃO | Minuta/PDF reais; corrigidos defaults inventados, fontes e perda silenciosa em PDFs longos. PDFs antigos não foram reescritos |
| RF10 | ATENDIDO COM LIMITAÇÃO | Cloudflare real; peça `6364358...` aprovada localmente e SHA confirmado. Normal administrativo continua 503. Evidência privada precisa seleção para entrega |
| RF11 | PARCIAL | Registros estruturados; novos snapshots, parâmetros e histórico corrigidos. Rastreabilidade antiga incompleta não foi fabricada retroativamente |
| RF12 | PARCIAL | Ficção das fixtures e varredura sem ocorrências reconhecidas; minimização do payload textual parcial; ZIP final ainda não inspecionado |
| RF13 | PARCIAL | Fidelidade/completude, pendências e taxa com denominador documentado; amostra humana final aprovado/rejeitado e avaliação sistemática de linguagem pendentes |

# 3. BULLETS DO ENUNCIADO QUE ESTAVAM FALTANDO

| Item | Falta encontrada | Tratamento |
|---|---|---|
| RF01, versões | README não fixava quais versões realmente tinham passado | Snapshot do ambiente Python 3.13.0 e bibliotecas; sem fingir lock/install novo |
| RF02, entradas/parametrização | Experimentos novos guardavam saídas/tempos, mas não cada prompt exato e auditoria completa | Entradas e registros por prompt adicionados; falha guarda resultados parciais e erro |
| RF06, comparação com texto de referência | Comparador usava apenas entidades críticas | Comparação lexical integral adicionada; nunca alimenta/corrige a transcrição |
| RF06, aceite / RF08, aceite | Aviso de revisão não impedia gerar minuta de fonte não conferida | Conferência explícita por ID/hash antes do LLM, edição invalida; teste ASGI e DOM |
| RF09, fontes | PDF/minuta não identificava fontes verificáveis; auditoria apontava `texto_original.txt`, que não era o arquivo recebido | Snapshot e hash do texto real, vínculo com origem multimodal, fontes no PDF e na reexportação |
| RF05/RF09, ausência sem invenção | A tabela chamava qualquer pendência de “Documento Exigido” | Rótulo alterado para “Dado pendente; conferir na fonte”, sem inferir obrigação documental |
| RF11, parâmetros/erros | `max_tokens` era redigido por conter “token”; resultado podia carregar segredo aninhado; `sucesso:false` podia aparecer como resumo positivo | Sanitização recursiva, preservação das métricas e respeito ao resultado de falha |
| RF11, decisão | Atualização textual sobrescrevia a decisão anterior | Histórico de decisões novas preservado; não se inventaram decisões antigas perdidas |
| RF12, campos/necessidade | Matriz limitada e conformidade de minimização declarada sem prova | Matriz ampliada; minimização marcada PARCIAL, sem transformar política proposta em operação implementada |
| RF13, taxa | Não havia cálculo operacional claro de aprovados/decididos | Método e endpoint; pendentes/TTS excluídos e alerta sobre mistura de testes históricos |

Ainda não resolvidos automaticamente: validações humanas, prova histórica completa
do metaprompt/gabaritos, ruído controlado, pacote final e instalação em outra máquina.
São lacunas de evidência/decisão, não autorização para fabricar resultados.

# 4. CRITÉRIOS DE ACEITE NÃO TOTALMENTE COMPROVADOS

Os RF03, RF04 e RF09 **não possuem uma frase separada “Critério de aceite”** no
enunciado; seus bullets continuam obrigatórios. Não inventei critérios adicionais.

| RF | Implementação/bullets | Aceite/evidência | Verificação em poucos minutos |
|---|---|---|---|
| 01 | Configuração e comandos presentes | Instalação limpa NÃO COMPROVADA | README + versões; precisa ensaio em outro Windows |
| 02 | A/B/C/metaprompt e arquivos presentes | Matriz raiz não comprova qualidade/tempos; avaliação humana final incompleta | Usar experimento real e análise observada, não matriz de 0,12 s |
| 05 | JSON com ausências válido | Testado unitário/ASGI e JSON real anterior | Abrir JSON e mostrar quatro pendências sem erros vermelhos falsos |
| 06 | STT/versões/metadados/comparações presentes | Conferência humana de nome/protocolo/data antes de minuta real no fluxo corrigido NÃO COMPROVADA | Abrir registro, ouvir original e registrar conferência; não basta exibir 3/6 |
| 07 | TTS com hash/arquivo real | Correspondência de payload e WAV verificável; qualidade por audição integral não atestada aqui | Mostrar aprovação, hash e WAV; ouvir trecho sem chamar provedor |
| 08 | OCR/versões/referência/erros presentes | Confirmação humana dos dados críticos pendente; 0/23 oficial não é extração fiel | Mostrar dois cenários e manter ilegível como pendência |
| 10 | Imagem real/proveniência/decisão local presentes | Aprovação local real existe, mas não está em entrega pública autossuficiente | Abrir PNG local e nota/hash; não desbloquear administrativo |
| 11 | Registros novos mais completos | Reconstrução de toda saída histórica NÃO COMPROVADA | Índice selecionado; não prometer reproduzir pixels pela mesma seed na Cloudflare |
| 12 | Controles e matriz presentes | Nenhum ZIP final foi inspecionado; registros privados incluem identidade Windows | Revisão de privacidade do pacote final obrigatória |
| 13 | Protocolo/testes/taxa existentes | Caso humano real rejeitado/corrigido na coorte final NÃO COMPROVADO inequivocamente | Registrar/selecionar manualmente caso fictício e mostrar justificativa |

# 5. PROBLEMAS ENCONTRADOS E CORRIGIDOS

| Gravidade | Arquivo/local | Evidência do defeito e correção |
|---|---|---|
| Alta | `src/pdf_generator.py:_inserir_corpo/gerar_minuta_pdf` | `insert_textbox` podia devolver espaço negativo e o código salvava PDF sem corpo. Agora pagina; teste verifica início, fim e todas as 1.200 ocorrências do conteúdo sintético |
| Alta | `src/pdf_generator.py:gerar_minuta_pdf` | Protocolo fixo, data atual e categoria presumida eram usados quando dados faltavam. Substituídos por “não localizado”; não foi alterado nenhum PDF histórico |
| Alta | `src/main.py:processar_texto` | Origem textual inexistente e falta do texto bruto personalizado/prompt exato. Agora registra snapshot, hash, prompt/instrução e caminhos reais |
| Alta | `src/main.py:processar_texto`; `src/web/app.js` | Texto de áudio/OCR podia chegar ao LLM sem conferência prévia. Agora exige aprovação explícita da fonte exata, vinculada à modalidade/ID/hash. Não autentica operador nem modifica RF10 |
| Alta | `src/audit.py:obter_aprovacao_texto` | A nova aprovação de fonte não pode autorizar TTS de minuta. Finalidade/modalidade da aprovação passou a ser verificada |
| Alta | `src/text_contract.py:interpretar_minuta` | Schema remoto era completo, mas checagem local aceitava extração incompleta. Caminho de produção exige conjunto completo e categoria da lista, sem preencher pelo gabarito |
| Alta | `src/audit.py:sanitizar` | Proteção não era recursiva e redigia uma métrica legítima. Agora sanitiza resultados/parâmetros/decisões sem esconder `max_tokens`; rejeita segredo como texto aprovado |
| Alta | `src/main.py:processar_texto` | Credencial colada na entrada poderia seguir ao provedor. Agora é bloqueada antes da chamada e do snapshot; diagnóstico privado também usa sanitização de todos os segredos conhecidos |
| Alta | `src/web_files.py:arquivo_publico` | A allowlist liberava logs e dados processados genericamente. Agora só permite fixtures públicas conhecidas, minutas e áudios; logs/entradas privadas permanecem bloqueados |
| Alta | `.dockerignore` | `COPY . .` podia incluir `.env`, `.git`, venv e execuções privadas num build. Contexto passa a excluir esses arquivos; não houve build/teste Docker |
| Alta | `src/main.py:main`; Docker/Compose | Sem autenticação geral, o padrão `0.0.0.0` expunha chamadas de texto na rede. CLI e publicação Compose agora usam loopback; o bind interno Docker é explícito. Isso não implementa autenticação |
| Média | `QualityEvaluator`; frontend/backend | Formatos equivalentes de CPF/telefone/protocolo podiam virar divergências; texto editado podia herdar gabarito de outro caso; OCR e JSON textual tinham campos incompatíveis. Normalização limitada de apresentação e separação explícita das referências corrigem isso sem preencher dados ou elevar a taxa OCR |
| Média | `src/audio.py:_comparar_texto_referencia` | Só havia comparação de entidades. Adicionada comparação integral normalizada, com limites de custo/memória e sem mudar transcrição ou 3/6 |
| Média | `src/llm_client.py:generate` | Uso/custo nativos eram descartados mesmo se disponíveis. Agora preservados, com distinção entre estimativa e provedor; custo desconhecido continua desconhecido |
| Média | `src/audit.py:atualizar_decisao_humana/resumo_revisoes` | Decisões sobrescritas e ausência de denominador operacional. Histórico novo preservado e taxa explicitada; a base antiga não vira uma coorte científica |
| Média | `src/main.py` | Erro RF06 em JSONResponse poderia quebrar CLI/run-all. Tratamento de falha e mensagens corrigidos; não se afirma neutralização de injeção só porque houve saída |
| Média | README/AGENTS/relatório/registro de IA/config | Referências a HF/VLM como ativos, fallback/mock de produção, custo zero e tarja de validação anterior à revisão eram inconsistentes. Documentação/config alinhados sem reescrever evidências antigas |

Referências de linha e alterações podem ser inspecionadas com `git diff`; nenhuma
correção reintroduz STT remoto, texto fictício, OCR preenchido, Pillow como IA ou
autenticação paralela. O helper JSON sem validação completa continua disponível para
usos legados/testes, mas **a rota de produção chama explicitamente o modo completo**.

# 6. PROBLEMAS QUE CONTINUAM PENDENTES

1. **Alta — aceite humano RF06/RF08/RF13:** implementar bloqueio não cria uma conferência
   humana real. A equipe deve conferir fontes, justificar correções/rejeições e
   demonstrar um caso aprovado e outro rejeitado/corrigido na coorte final.
2. **Alta — pacote final (§11/RF12):** GitHub e ZIP complementar não substituem ZIP
   completo. Separar fontes/fixtures/resultados reais de caches, backups, credenciais e
   identidade Windows. Não exportei aprovação privada com identidade real automaticamente.
3. **Alta — qualidade e referência STT:** 3/6 não mede toda a transcrição; nome, curso
   e turno não foram conferidos pelo comparador. A recomparação local do texto existente
   dá S=46, D=2, I=66, N=77, hipótese=141 palavras, WER=148,05%. **Não usar como acurácia
   confiável do motor sem conferir que a referência é verbatim**. Não alterei gabarito,
   áudio, transcrição nem o índice 3/6 para melhorar resultado.
4. **Alta — OCR oficial:** permanece 0/23; processamento técnico com texto não significa
   formulário corretamente extraído. Sintético 22/23 demonstra capacidade em outro cenário,
   não resolve o oficial. Não preencher automaticamente nem chamar 0/23 de aprovação.
5. **Média — RF02:** encadeamento metaprompt, avaliação humana dos seis critérios,
   tempo até uso e histórico completo de parâmetros precisam consolidação. Prompts atuais
   corrigidos não podem ser apresentados como se fossem os do experimento antigo.
6. **Média — reprodução:** instalação limpa e Docker NÃO COMPROVADOS. SAPI5 depende
   de Windows/voz; small exige cache e memória; Tesseract exige português. Docker/Linux
   pode precisar de fontes e TTS alternativo, não apenas `docker compose up`.
7. **Média — minimização:** texto fictício integral ainda é enviado ao LLM; máscara de
   tela/política de campos não é anonimização do payload. Não usar dados reais.
8. **Média — serviço local:** não há autenticação geral do grupo. Rotas textuais e
   aprovação local não autenticam identidade. Expor servidor em rede permitiria uso por
   terceiros. O padrão foi restringido a loopback, mas `--host 0.0.0.0` explícito exige
   controle externo. RF10 normal segue 503, sem contorno. Não implementei auth paralela.
9. **Média — histórico:** arquivos antigos podem ter origem inválida, parâmetros
   redigidos, decisões sobrescritas e resultados de testes misturados com reais. Não
   restaurar “a história” inventando logs. Escolher uma amostra identificada.
10. **Baixa/interpretativa — CRLF:** MP3/PDF são byte a byte iguais ao ZIP oficial;
    texto tem CRLF (897 bytes contra 881), mas Unicode/conteúdo é idêntico após
    normalização. Não afirmo identidade binária de todo original; não alterei `dados/originais`.
11. **Interpretativa — orientação visual RF10:** a peça é educacional e legível, mas
    título e assunto repetem o tema sem muita instrução prática. O professor pode
    distinguir “cartaz temático” de “peça de orientação”. Se exigir algo mais explícito,
    usar somente orientação comprovada no contexto e criar nova versão/revisão; não
    alterar automaticamente os pixels/hash já aprovados nem inventar documentos/prazos.

# 7. EVIDÊNCIAS QUE EXISTEM MAS SÃO FRACAS

- `prompts/matriz_comparativa.md`: tempos iguais de 0,12 s e “alucinação zero” sem
  prova. Conservada como histórico; usar `analise_prompts_observada.md` e matriz real.
- Resultados antigos Pillow/mock e pastas `evidencias_origin_main`: existência de PNG,
  MP3 ou JSON não comprova inferência real. Não os usar para substituir Cloudflare/STT reais.
- `documentacao/relatorio_lgpd.json`: snapshot histórico; não comprova minimização atual.
  Relatório dinâmico atualizado declara a limitação, sem reescrever o snapshot.
- Aprovação textual: prova deliberação local declarada e hash, **não identidade autenticada**.
- Aprovação RF10: prova revisão local previamente registrada do PNG exato; não prova
  autorização para publicação normal nem inspeção itemizada de cada dedo/objeto.
- Gabaritos: existem e são usados; anterioridade independente de toda coorte e
  literalidade da referência STT precisam ser demonstradas. Não melhorar números editando-os.
- A contagem de testes não prova acurácia, audição, prosódia,
  ausência universal de alucinação ou domínio dos integrantes. Usar a contagem efetiva da seção 12.

# 8. FUNCIONALIDADES ALÉM DO EXIGIDO

O mínimo exige testar/revisar/registrar; não exige especificamente estas técnicas.

| Funcionalidade adicional | Avaliação | Efeito na banca |
|---|---|---|
| Web Vanilla com abas, filtros e responsividade | Agrega valor | Facilita demonstração; não substitui evidências |
| Badge de provedor/modelo efetivos, cache-busting/no-store | Agrega valor | Evita demonstrar frontend antigo ou fornecedor errado |
| JSON Schema remoto + duplicatas/truncamento + validação local | Agrega valor | Formato robusto; não confundir com verdade factual |
| Uma reparação de formato explicitamente auditada | Agrega valor com custo | Pode duplicar consumo; manter limite e informar cobrança |
| Provedores e fallback configuráveis | Agrega valor/complexidade | Não ativar silenciosamente outro modelo no experimento |
| Cache local obrigatório sem download automático STT | Agrega privacidade; exige preparação | Pode impedir instalação nova se cache não estiver pronto |
| Aprovação TTS por hash com rechecagem após síntese | Agrega valor | Evita áudio de texto editado/revogado |
| OCR integral, PSM11 e regiões/consenso | Complexidade relevante | Não apresentou ganho no oficial; não adicionar mais estratégias sem ganho verificável |
| Pillow/TrueType para toda tipografia e brasão original | Agrega valor | Resolve textos ilegíveis sem apresentar desenho como IA |
| Correção determinística de região/placa em imagens antigas | Valor pontual | Pode atrapalhar se aplicada a imagem de geometria diferente; não usar indiscriminadamente |
| Revisão/estado/hash e endpoint de publicação RF10 | Segurança extra | Não é obrigatório publicar; bloqueio sem auth dificulta botão, mas deve ser preservado |
| Executor Windows isolado com identidade da sessão | Agrega controle/complexidade | Serve ao teste; não substitui autenticação nem pacote multiplataforma |
| PDFs A4, brasão, paginação e exportação única | Agrega valor | Mais profissional; documentos permanecem minutas até revisão |
| JSONL + detalhes + histórico de decisões | Agrega valor | Evita perder revisões novas; mistura histórica ainda exige seleção |
| Distinção refinada PENDÊNCIA/DIVERGÊNCIA e normalização Unicode | Agrega valor | Evita penalização falsa; não deve transformar ausência em acerto |
| ASGI/DOM/Edge automatizados e testes reais opt-in | Agrega valor | Testar é obrigatório; essa cobertura automatizada é adicional e usa mocks |
| `.dockerignore`/allowlist de arquivos | Agrega valor | Impede vazamento incidental por build/download |
| Docker | Extra não validado | Pode atrapalhar se anunciado como pronto, especialmente com SAPI5/Linux |

Não contabilizar timeout, revisão humana, comparação com gabarito ou identificação
de IA como “extras”: esses itens já são obrigatórios no enunciado.

# 9. PONTOS QUE A EQUIPE HAVIA INTERPRETADO DE FORMA INCOMPLETA

- **Avisar não é bloquear/conferir.** A mensagem de revisão não bastava para impedir
  minuta baseada em STT/OCR não confirmado. O fluxo agora exige decisão por hash.
- **Sucesso técnico não é fidelidade.** 0/23, 3/6 e JSON parseável não significam
  dados críticos corretos; tampouco o enunciado fixa uma nota mínima de acurácia.
- **Registrar “PRODUCAO” não reconstrói o prompt.** Novos registros precisam guardar
  a versão efetiva, fonte, parâmetros e artefatos; o histórico não é corrigível por suposição.
- **Bruto/revisado não significam texto perfeito.** Normalizar espaços é conservador;
  pode ser suficiente como versão técnica, mas a revisão de conteúdo ainda deve ocorrer.
- **Comparação de entidades não é comparação integral de transcrição.** WER adicional
  mostra distância lexical, não um percentual de acerto de nomes ou de semântica.
- **Política LGPD não é implementação.** Flags de minimização/máscaras não provam
  que CPF/RG foram removidos do request ao LLM.
- **Imagem aprovada não é imagem publicável automaticamente.** Revisão local não
  concede `rf10:revisar` nas rotas normais.

# 10. POSSÍVEIS INTERPRETAÇÕES DIFERENTES DO PROFESSOR

| Nossa leitura | Alternativa razoável | Leitura mais segura / adaptação |
|---|---|---|
| Provedores substituíveis | Só seriam aceitos exemplos das aulas | §7 permite substituição documentada; explicar finalidade/custo/privacidade, sem trocar motor validado por preferência |
| SAPI5 satisfaz TTS por API | “API ou modelo aberto” significaria API de provedor remoto ou pesos abertos | SAPI5 é API COM local e proprietária. Explicitar isso e pedir confirmação pedagógica; não chamá-la de modelo aberto |
| OCR tradicional basta | Objetivo amplo menciona visão assistida por modelo | RF08 diz OCR tradicional **OU** visão multimodal; não inventar obrigação de VLM, mas saber justificar a escolha local |
| Geração de imagem basta | Seriam obrigatórias geração e edição por IA | RF10 diz gerar **OU** editar. Cloudflare real atende geração; Pillow sozinho não atenderia |
| Tema matrícula/campus caracteriza orientação | Seria necessária instrução prática de orientação ao cidadão | Há vínculo com o caso, mas conteúdo instrucional é pouco explícito. Validar suficiência com o docente; qualquer texto adicional precisa fonte e nova revisão da composição |
| Versões no mesmo JSON bastam | Bruto/corrigido precisariam de dois arquivos | Enunciado exige preservação/versões, não dois arquivos físicos; mostrar campos distintos, hash e histórico |
| 3/6 e 0/23 podem ser demonstrados como limitações | Seria exigida correção dos dados críticos para finalizar a resposta | Não há limiar numérico, mas há confirmação humana. Não liberar minuta com dúvida; usar sintético legível sem dizer que resolveu oficial |
| C é preferível por estrutura | Escolha deveria resultar de experimento controlado completo | Registrar seis critérios, parâmetros e tempo de revisão; não usar elogios automáticos como evidência |
| CRLF preserva conteúdo | Preservar original seria igualdade binária | Documentar hashes e normalização; não mudar originais silenciosamente. Decidir com docente se precisa cópia binária adicional da fonte |
| Revisão local por operador basta | Seria exigida identidade autenticada em toda revisão | Auth não é requisito explícito de infraestrutura, mas não prometer que existe. RF10 protegido e entrega fictícia/local são limites explícitos |
| GitHub + complemento bastam | §11 exige um único compactado completo | Preparar ZIP final seguro; não compartilhar `.env` nem exportar identidades Windows por conveniência |
| Proveniência é JSON/nota/identificação IA | Seria obrigatório C2PA/assinatura certificada | Não consta exigência de C2PA; registrar origem/hash/modelo/data/revisão e não declarar certificação que não existe |

# 11. ENTREGÁVEIS

| Item | Existência/conteúdo | Adequação atual |
|---|---|---|
| Código organizado/executável | `src`, testes, entrada FastAPI | Testado localmente; instalação nova não executada |
| README | Instalação, config, comandos, dependências e limitações | Atualizado; ensaio por terceiro pendente |
| requirements | Bibliotecas Python e PyAV compatível | Faixas de versões, sem lock; snapshot do ambiente separado |
| `.env.example` | Chaves vazias e defaults documentados | Sem segredo real; `.env` não deve acompanhar entrega |
| `.gitignore` | Segredos/caches/privado/artefatos | Logs/PDF já rastreados e sujos continuam fora de qualquer commit desta auditoria |
| Dados originais | Texto, MP3, PDF, brasão | Ficção fornecida; nota CRLF; nada alterado |
| Gabaritos | Texto, áudio, visão e sintético | Presentes; referência STT precisa conferência verbatim; não editar para elevar taxa |
| Prompts A/B/C | Templates + entradas antigas e experimento real | Rotular históricos e vincular versão usada; metaprompt tem prova histórica fraca |
| Respostas dos prompts | Saídas locais reais e arquivos históricos | Não misturar transportes mockados com inferência |
| Quadro comparativo | Matriz real + análise observada | Matriz raiz antiga não prova números/qualidade |
| Resultados textuais | JSON, TXT/PDF, decisões | Saída real disponível; PDFs/fontes antigos fracos |
| Resultados áudio STT | Transcrição real, bruto/revisado e 3/6 | Revisão humana pendente |
| Resultados áudio TTS | WAV real e metadados/hash | Ouvir/verificar texto antes da banca |
| OCR/visão | Oficial/sintético, bruto/alternativas/JSON | 0/23 e 22/23 claramente separados |
| Imagem | PNG/arte IA/metadados/revisão local | Existe; seleção para ZIP sem identidade real pendente |
| Relatório técnico | Arquitetura/modelos/custos/limitações | Corrigido para motores atuais e ausência de fallback automático |
| Arquitetura | Diagrama no relatório | Mostra Gemini e OCR local; decisão final humana |
| Modelos | Configuração, badge e registros | Diferenciar alternativa do config de modelo efetivo |
| Custos | Não presumidos; captura nativa nova | Não há custo total histórico reconstruível sem faturas/usage; nada inventado |
| Riscos | README, protocolo, auditoria | Memória, qualidade, fornecedor, privacidade, auth e prova explicitados |
| LGPD | Matriz ampliada e status parcial | Não afirmar conformidade jurídica integral; sem dados reais na entrega |
| Avaliação de qualidade | Comparadores/protocolo/taxa | Faltam coorte real consolidada e avaliação humana sistemática |
| Registro de IA | Solicitações reais, decisões e erros | Equipe deve confirmar responsabilidade/compreensão; versão do assistente não inventada |
| ZIP completo | NÃO COMPROVADO | Preparar após seleção/privacidade; não equivale ao ZIP privado complementar |

# 12. TESTES REAIS × MOCKS × VALIDAÇÃO HUMANA

**Executado nesta auditoria:** suíte offline completa e validadores DOM; teste de
navegador Edge + FastAPI temporário em 390/1366 px, com mocks de LLM/STT/OCR/TTS;
comparação local do STT existente, inspeção visual estática do PNG e da região OCR;
varredura de segredos, revisão de código e hashes. **Não** houve inferência STT/OCR/TTS/
imagem real nova, instalação, download, chamada paga ou publicação.

Comandos reproduzíveis:
```powershell
.\.venv\Scripts\python.exe -B testes/executar_offline.py
node testes/validar_interface_offline.cjs
node testes/validar_fluxos_web.cjs
.\.venv\Scripts\python.exe -B -m testes.validar_navegador_local --executar
.\.venv\Scripts\python.exe -B -m testes.gerar_matriz_auditoria
```

Resultado definitivo: **332 testes aprovados, zero falhas e 2 ignorados**; registro
em `validacoes_executadas.json`. Os dois testes OCR reais são opt-in (`RF08_REAL=1`) e
permaneceram ignorados para não repetir OCR nem confundir teste local com evidência já existente.

| Tipo | O que prova | O que não prova |
|---|---|---|
| Unitário com WAV sintético/mocks | Validação, falhas, comparação, hash, preservação de dados | Reconhecimento/síntese reais ou qualidade subjetiva |
| ASGI com provedor mockado | Rotas/payloads, 409/403/503, revisão, arquivo e publicação | Rede/provedor real ou autenticação de produção |
| Edge com backend temporário e mocks | JS efetivo, abas, botões, erros, PDF/WAV HTTP, responsividade | OpenRouter/Cloudflare reais nesta execução |
| Registros reais anteriores | Gemini, STT local, SAPI5, OCR e Cloudflare executados e artefatos preservados | Repetibilidade atual do fornecedor ou da máquina recém-instalada |
| Comparação STT recalculada | Cálculo determinístico sobre texto real existente | Nova transcrição, escuta humana ou acurácia sem referência verbatim |
| Decisão humana anterior | Aprovação textual e PNG exato quando registrados | Decisão nova, aprovação do OCR/STT ou identidade autenticada geral |

Conferência direta dos arquivos em `verificacao_artefatos_reais.json`: o PDF real
selecionado contém o corpo da minuta de 625 caracteres; o WAV real tem 1.309.526
frames, 59,389 s e hash correspondente ao registro; o PDF sintético tem uma imagem
e **zero caracteres selecionáveis**, exigindo OCR. Isso não é uma nova inferência.

# 13. RISCOS PARA A DEMONSTRAÇÃO

Roteiro detalhado de seis blocos/12 minutos em `roteiro_demonstracao.md`.

- Preparar os artefatos reais antes: não depender de cota/latência e não gerar imagem
  outra vez só para provar que já foi gerada.
- Fechar aplicações pesadas antes de STT; não disparar requisições concorrentes.
  O small já falhou por memória e depois passou. Não prometer tempo/memória mínimos não medidos.
- Escolher áudio no atendimento pode executar STT novamente; abrir também a aba
  multimodal significa outro processamento. Evitar duplicação de trabalho na apresentação.
- O PDF oficial é demonstração de limitação e revisão; levar o sintético legível como
  cenário diferente, não como resultado do documento oficial.
- Novas correções foram verificadas offline. Reiniciar a instância real do servidor
  antes de testar o fluxo atualizado; não afirmar que um processo antigo em 8000 carregou novo Python.
- RF10 normal continuará indisponível até auth. Mostrar peça/nota/hash em visualizador
  local e explicar o executor controlado, sem remover o bloqueio por conveniência.
- Não abrir `.env`, logs de identidade Windows, histórico de terminal com chaves ou
  versões mockadas como se fossem uma geração real.
- Preparar o caso humano rejeitado/corrigido e o ZIP: são itens de aceite, não cosmética.

# 14. PERGUNTAS QUE O PROFESSOR PROVAVELMENTE FARIA

1. **“Onde está a chamada real?”** Nos registros Gemini/Cloudflare selecionados pelo
   índice `evidencias_verificadas.json`, com artefatos; os testes atuais não foram essas chamadas.
2. **“Por que o OCR diz sucesso com zero?”** Sucesso técnico de extração de texto;
   o comparador mostra 0/23, incerteza e bloqueio da minuta sem revisão.
3. **“3/6 é metade das palavras corretas?”** Não. São seis entidades; WER é outra
   medida e depende de referência literal válida. Aqui os números não são intercambiáveis.
4. **“Que regra garante alucinação zero?”** Nenhuma. Isolamento/schema/testes reduzem
   risco; fonte e revisão humana determinam aceitabilidade.
5. **“Esse botão aprova com login real?”** Não há auth geral. A aprovação textual é
   local/declarada; RF10 administrativo permanece bloqueado, sem auth paralela.
6. **“Onde está o caso rejeitado?”** Precisa estar selecionado e revisado pela equipe;
   um teste que chama `REJEITADO` em diretório temporário não substitui essa evidência.
7. **“Tudo funciona sem internet?”** STT/OCR/SAPI5 locais com recursos instalados;
   texto Gemini e geração Cloudflare exigem rede/credenciais/cota. Não há resposta fictícia offline.
8. **“Pillow gerou essa arte?”** Não: arte central por Cloudflare; tipografia/brasão/
   tarja por Pillow. Mostrar PNG bruto, composição, prompt e hashes.
9. **“Dá para reproduzir após clonar?”** Código/instruções existem; voz, Tesseract/por,
   cache small e chaves devem ser preparados. Instalação limpa ainda não foi demonstrada.
10. **“Os estudantes compreendem tudo?”** O registro de IA não prova compreensão;
    cada integrante deve explicar arquitetura, conceitos, limites e decisões.

# 15. O QUE PRECISA SER FEITO MANUALMENTE ANTES DA ENTREGA

1. Conferir nomes/protocolos/datas no áudio e dados críticos no OCR, corrigindo apenas
   com a fonte; registrar justificativas e hashes. Não copiar valores do gabarito como OCR/STT.
2. Consolidar um caso fictício aprovado e outro rejeitado/corrigido, com decisões humanas
   reais e amostra definida. Não alterar a imagem aprovada só para criar outra decisão.
3. Verificar se a referência STT de 77 palavras é verbatim e se precede a execução.
   Se precisar outra referência, criar versão separada, explicar a revisão e não alterar
   a evidência/gabarito original para obter nota maior.
4. Concluir avaliação RF02 e justificativa, distinguindo tempo de API de tempo até uso.
5. Ouvir WAV aprovado e revisar minutas/PNG/fontes. A auditoria não assinou em nome da equipe.
6. Revisar a privacidade das cópias destinadas ao professor: `.env`/credenciais nunca
   entram; identificação/SID Windows privados precisam tratamento e escolha explícita.
7. Montar ZIP completo com código, referências e resultados selecionados; conferir
   caminhos/hashes e executar o README em outro computador. Não enviar só complemento.
8. Confirmar responsabilidade dos integrantes e ensaiar 12 minutos. Se houver dúvida
   de leitura SAPI5/API, confirmar critério pedagógico, sem afirmar modelo aberto.
9. Reiniciar a instância local para usar o backend corrigido. Uma futura chamada paga
   ou novo commit/push requer decisão separada; nada disso foi feito nesta auditoria.

# 16. O QUE NÃO PRECISA MAIS SER MEXIDO

Não trocar OpenRouter/Gemini, small/local/CPU/int8, SAPI5, OCR conservador ou Cloudflare
por preferência. Não alterar originais/gabaritos nem retrabalhar pixels aprovados.
Preservar bruto/revisado, tarja IA neutra, fonte Unicode, brasão original, SHA,
revisão humana, bloqueio RF10 e distinção pendência/divergência. Não instalar GPU,
reintroduzir mocks de produção ou aprovar automaticamente para facilitar a banca.

Correções novas precisam ser demonstradas com seus limites: testes offline são
fortes para contrato/segurança, mas não tornam dispensáveis as validações humanas
e a seleção dos artefatos reais para a entrega.

# 17. NOTA ESTIMADA DE 0 A 10

**7/10 para uma entrega feita hoje**, como estimativa crítica, não nota oficial.
O enunciado não fornece distribuição numérica de pontos; não inventei pesos por RF.

- **Impede 10:** falta prova integral dos aceites e da reprodução; STT/OCR têm
  divergências/baixa qualidade; minimização parcial; histórico e metaprompt não
  completamente reconstruíveis; validação humana/linguagem não consolidada.
- **Impede 9:** RF02 não mede tempo até uso nem fecha todos os critérios com revisão;
  o fluxo novo origem confirmada -> minuta -> TTS só foi validado com mocks; não existe
  pacote final seguro e instalação limpa comprovados.
- **Impede 8 hoje:** faltam o caso humano real rejeitado/corrigido inequívoco da coorte,
  conferências finais de dados críticos e ZIP completo revisado. Esses são itens
  verificáveis do enunciado, não preferências arquiteturais do auditor.

O total de testes e as funções extras não compensam essas provas pendentes. A nota
pode mudar após as ações manuais, mas não será elevada retroativamente por modificar
gabaritos, fabricar logs ou transformar resultados técnicos em aprovações.
