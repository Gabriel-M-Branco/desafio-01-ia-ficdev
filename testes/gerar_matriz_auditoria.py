"""Materializa a matriz editorial da auditoria; não executa provedores ou altera evidências."""
from pathlib import Path
import csv

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "documentacao/auditoria_final/matriz_rastreabilidade.csv"
STATUS = {"A": "ATENDIDO", "L": "ATENDIDO COM LIMITAÇÃO", "P": "PARCIAL",
          "E": "IMPLEMENTADO MAS SEM EVIDÊNCIA", "F": "EVIDÊNCIA EXISTE MAS NÃO PROVA O REQUISITO",
          "I": "SUJEITO A INTERPRETAÇÃO", "N": "AUSENTE"}
# Cada linha corresponde a UM bullet; implementação/evidência/teste não equivalem entre si.
REQUISITOS = {
1: (4, "src/main.py:main; config.json; .env.example", "README; ambiente_validado.json", "test_sistema; validadores DOM/Edge", [
 ("ser executada por comando documentado, preferencialmente python -m src.main", "A", "Comando e servidor existentes; demonstração local documentada."),
 ("utilizar arquivo de configuração para caminhos, modelos e parâmetros não sensíveis", "L", "config.json contém alternativas HF; motores efetivos vêm também do .env. Não confundir modelo configurado alternativo com modelo executado."),
 ("carregar segredos por variáveis de ambiente ou arquivo .env não versionado", "A", "dotenv; .env ignorado e não rastreado; varredura com limites documentados."),
 ("fornecer .env.example sem credenciais reais", "A", "Valores secretos vazios; defaults locais/OpenRouter/Cloudflare explícitos."),
 ("registrar as versões de Python e das principais bibliotecas", "A", "Snapshot de versões reais criado; requirements é faixa de versões, não lock reprodutível."),
 ("ACEITE: instalar e executar seguindo apenas README.md", "L", "NÃO COMPROVADO em uma máquina limpa; não houve instalação nem download nesta auditoria.")]),
2: (4, "src/prompts.py; src/main.py:rodar_experimento_prompts", "prompts/experimento_02d9f28ad4f8458fb865ba99ce938b39; analise_prompts_observada.md", "test_rf02_progresso_abc; test_rf02_artefatos_experimento", [
 ("Prompt A: instrução zero-shot curta", "A", "Template e saída real histórica existem."),
 ("Prompt B: Persona, Contexto, Tarefa, Formato e Critérios de sucesso", "A", "Cinco seções presentes; saída JSON histórica."),
 ("Prompt C: produzido com auxílio de um metaprompt", "E", "Metaprompt e template existem; NÃO COMPROVADO o encadeamento original metaprompt -> resposta geradora -> Prompt C."),
 ("manter o mesmo modelo e, quando possível, os mesmos parâmetros", "L", "Matriz real registra Gemini nos três; parâmetros históricos não foram persistidos integralmente. Novas execuções os registram."),
 ("avaliar fidelidade ao contexto", "L", "Análise estática nova distingue contexto e fonte; não é aprovação humana do experimento."),
 ("avaliar dados inventados", "P", "Matriz antiga promete alucinação zero sem prova; análise nova sinaliza afirmações institucionais sem fonte."),
 ("avaliar formato", "A", "A em prosa; B/C JSON analisáveis. JSON histórico não equivale ao schema atual completo."),
 ("avaliar tom", "L", "Observação editorial registrada; falta validação final da equipe."),
 ("avaliar lacunas", "A", "B/C usam marcador de ausência; faltam campos do schema atual. Nada foi preenchido por gabarito."),
 ("avaliar tempo até um resultado utilizável", "P", "Duração de API existe; tempo de revisão/correção até uso NÃO COMPROVADO."),
 ("selecionar e justificar o prompt incorporado", "L", "C escolhido por estrutura/blindagem; escolha não demonstra qualidade perfeita nem avaliação humana completa."),
 ("ACEITE: três entradas, saídas e matriz acompanham entrega", "L", "Arquivos existem localmente; experimento real ignorado pelo Git precisa entrar no ZIP selecionado. Entradas históricas nem sempre vinculadas por hash.")]),
3: (4, "src/prompts.py; src/text_contract.py; src/main.py:processar_texto", "Prompts salvos; casos adversariais; logs texto", "test_text_contract; test_integracao_main; test_sistema", [
 ("delimitar claramente o conteúdo externo", "A", "Envelope XML e escape de delimitadores; testes de tentativas de quebra."),
 ("tratar instruções de documentos como dados, não comandos", "L", "Instrução de sistema e sanitização; não há garantia matemática contra injeção."),
 ("proibir invenção de fatos, prazos, autoridades e fundamentos legais", "L", "Prompt proíbe; validação sintática não comprova veracidade factual. Humano necessário."),
 ("usar não localizado para campo obrigatório ausente", "L", "Schema/prompt exigem regra; conferência semântica continua humana."),
 ("solicitar saída estruturada e verificável", "A", "Schema remoto e checagem local completa no caminho de produção; no máximo uma reparação de formato."),
 ("incluir teste de prompt injection em pelo menos uma entrada", "A", "Caso fictício existe; testes mockados não provam resistência do modelo real atual.")]),
4: (4, "src/llm_client.py:generate", "Logs reais Gemini; metadata RF10 Cloudflare; varredura_segredos.json", "test_integracao_main; test_cloudflare_rf10; test_auditoria_final", [
 ("realizar pelo menos uma chamada programática a provedor", "A", "Registros reais Gemini/Cloudflare e artefatos; não houve nova chamada nesta auditoria."),
 ("enviar modelo, mensagem e parâmetros configuráveis", "A", "Reutiliza cliente existente; parâmetros efetivos distinguem APIs."),
 ("definir timeout", "A", "requests/HF com timeout; teste simula esgotamento."),
 ("tratar chave ausente", "A", "credentials_missing, sem minuta fictícia."),
 ("tratar autenticação inválida", "A", "401/403 diferenciados, testados com mocks."),
 ("tratar limite de requisições", "A", "429 diferenciado, testado com mocks."),
 ("tratar indisponibilidade", "A", "Falha explícita, sem fallback silencioso."),
 ("tratar resposta vazia", "A", "Bloqueada, testada com mocks."),
 ("não registrar credenciais", "L", "Sanitização recursiva corrigida; varredura não garante reconhecimento de segredos antigos arbitrários."),
 ("registrar tempo de resposta", "A", "Tempos nos registros e matrizes reais; não confundir com tempo até aprovação."),
 ("registrar tokens e custo estimado quando disponíveis", "L", "Métricas nativas agora preservadas; antigo histórico usava estimativas e perdeu possível custo nativo. Sem tarifa inventada."),
 ("mensagem compreensível na indisponibilidade", "A", "UI mostra HTTP/detail; memória RF06 vira 503 e causa auditável.")]),
5: (4, "src/main.py:processar_texto; src/text_contract.py", "EXEC_20261017_173239_c3ec12; JSONs extraídos", "test_text_contract; test_auditoria_final; ASGI", [
 ("identificar protocolo", "L", "Campo exigido; correção factual não é inferida só por schema."),
 ("identificar data", "L", "Campo exigido; dados ausentes não recebem data atual inventada no PDF."),
 ("identificar solicitante fictício", "L", "Campo exigido; ficção de texto livre depende do operador."),
 ("identificar assunto", "L", "Campo exigido pelo schema; sem análise semântica automática de verdade."),
 ("identificar pedido", "L", "Campo exigido; fonte original nova passa a ser preservada em snapshot."),
 ("classificar em lista documentada de categorias", "A", "Categorias documentadas/configuradas e enum validado no caminho de produção."),
 ("indicar ausências e confiança ou revisão", "A", "Campos e necessidade_revisao=true; conferência humana mantida."),
 ("preservar texto original", "A", "Originais intactos; novas entradas livres têm snapshot exato e hash. Histórico personalizado antigo pode não ter fonte."),
 ("gravar resultado em JSON", "A", "Arquivos únicos; sem sobrescrever resultados prévios."),
 ("ACEITE: JSON válido com campos ausentes", "A", "Schema e testes de ausências, tipos, truncamento e duplicatas; campos novos não são adivinhados.")]),
6: (5, "src/audio.py:transcrever_audio; src/main.py:processar_texto", "EXEC_20261017_175537_b329c8; transcrição local; 89,16 s; 3/6", "test_audio_rf06; test_audio_integracao_rf06; test_auditoria_final", [
 ("validar extensão", "A", "Allowlist de formatos; mocks e WAV sintético de teste."),
 ("validar tamanho", "A", "Limite 25 MB; vazio/excesso rejeitados."),
 ("executar STT por API ou modelo aberto", "A", "faster-whisper small local CPU/int8/pt comprovado por execução anterior."),
 ("preservar transcrição bruta", "A", "Campo separado no JSON e resultado auditado."),
 ("produzir versão revisada", "L", "Normalização conservadora; edição humana agora persistível. Não equivale a revisão lexical já concluída."),
 ("registrar idioma", "A", "Idioma configurado e reportado pelo motor local."),
 ("registrar modelo", "A", "small, CPU e int8 registrados."),
 ("registrar duração do áudio", "A", "89,16 s, não confundir com duração do processamento."),
 ("comparar com referência e apontar erros relevantes", "A", "3/6 entidades; lacunas explicitadas; nenhum acerto artificial."),
 ("ACEITE: conferir nomes, protocolos e datas antes da minuta", "P", "Bloqueio por hash adicionado e testado com mocks. NÃO COMPROVADA uma conferência humana real dessas três entidades seguida da minuta no fluxo novo.")]),
7: (5, "src/audio.py:sintetizar_minuta_audio", "EXEC_20261017_173424_bc38cb; WAV e aprovação textual", "test_audio_rf07; ASGI texto -> revisão -> TTS", [
 ("usar TTS por API ou modelo aberto", "I", "SAPI5 é API COM local com voz proprietária; literal API permite esta leitura, mas pedir aceite se professor exigir serviço/modelo aberto."),
 ("selecionar voz e entonação institucional", "L", "Maria pt-BR, Rate=0 e volume 100; não há comprovação de prosódia expressiva ou avaliação auditiva nesta auditoria."),
 ("avisar ao ler não localizado", "A", "Aviso explícito aplicado ao texto sintetizado, hash próprio."),
 ("salvar áudio em formato comum", "A", "WAV verdadeiro, validado por frames/tamanho; nenhum fallback de bytes fictícios."),
 ("documentar acessibilidade e limitações", "A", "README distingue leitura falada de acessibilidade universal."),
 ("ACEITE: áudio corresponde ao texto aprovado sem acréscimos relevantes", "L", "Hash/payload e arquivo real existem; aviso é acréscimo exigido. Audição integral humana NÃO COMPROVADA nesta auditoria.")]),
8: (5, "src/vision.py; confirmação de origem em src/main.py", "resumo_oficial.json 0/23; resumo_sintetico.json 22/23", "test_vision_rf08; dois cenários reais históricos (não repetidos)", [
 ("implementar OCR tradicional ou visão multimodal", "A", "PyMuPDF/Tesseract local português; VLM não é obrigatório pois o texto diz OU."),
 ("preservar original", "A", "Hash PDF idêntico ao arquivo oficial; inventário antes/depois."),
 ("preservar texto bruto", "A", "Versões e estratégias preservadas no resultado."),
 ("produzir versão corrigida sem mudar sentido", "L", "Correção conservadora de espaços; não restaura ilegibilidade nem autoriza preencher gabarito."),
 ("identificar ilegíveis/incertos", "A", "Ausências e divergências de estratégias registradas."),
 ("comparar com gabarito e registrar acertos/erros", "A", "Oficial 0/23; sintético 22/23 (e-mail não conferido). Limitações não ocultadas."),
 ("justificar processamento local por soberania/privacidade", "A", "Justificativa em código/documentação; PDF não é enviado ao LLM neste OCR."),
 ("ACEITE: confirmação humana dos dados críticos", "P", "Confirmação por hash antes da minuta adicionada; falta decisão real final sobre OCR oficial/sintético. Rejeitar ilegíveis em vez de inventar.")]),
9: (5, "src/main.py:processar_texto; src/pdf_generator.py", "Minutas reais anteriores e novos testes de fontes/PDF", "test_sistema; test_integracao_main; test_auditoria_final", [
 ("usar somente dados da entrada ou contexto", "L", "Prompts proíbem invenção; defaults de protocolo/data inventados removidos do PDF; revisão factual humana continua necessária."),
 ("seguir modelo institucional da equipe", "A", "PDF com brasão original, cabeçalho e marcação de minuta; paginação protege corpo longo."),
 ("marcar ausências explicitamente", "A", "Schema e placeholders; não converte ausências em fatos."),
 ("incluir referências aos arquivos de origem", "L", "Corrigido para novas minutas e reexportações com registro atual. PDFs históricos sem fonte não foram reescritos."),
 ("impedir envio automático", "A", "Nenhum envio por e-mail/publicação automática; download de minuta não significa despacho ou aprovação.")]),
10: (5, "src/image_generation.py; src/image_access.py; executor local", "PNG 6364358... e revisão APROVADO, hash 18e244ee...", "test_cloudflare_rf10; test_publicacao_rf10; test_rf10_local", [
 ("peça de orientação relacionada a caso fictício", "L", "Tema educacional/matrículas presente, mas pouca orientação prática além de título/assunto. Professor pode exigir instrução mais explícita; não alterar peça aprovada sem nova revisão."),
 ("prompt com sujeito", "A", "Campo sujeito preservado e integrado ao prompt exato."),
 ("prompt com composição", "A", "Campo de composição presente."),
 ("prompt com estilo", "A", "Paleta e estilo institucional documentados; manual oficial externo não foi fornecido."),
 ("prompt com iluminação", "A", "Campo iluminação presente."),
 ("prompt com proporção", "A", "Arte 1:1, composição final com faixas; distinguir arte da peça final."),
 ("prompt com restrições", "A", "Sem texto/placas/logos na arte; sem pessoas reais/ambiente clínico."),
 ("gerar imagem nova OU editar fornecida", "A", "Cloudflare real; Pillow apenas compõe, sem substituir falha da IA."),
 ("verificar textos, símbolos, mãos, objetos e coerência", "L", "Decisão visual real existe e inspeção estática feita; checklist itemizado de mãos/objetos não consta na decisão histórica."),
 ("manter prompt, modelo e data", "A", "Metadados e arte bruta com hashes; parâmetros enviados distintos das opções ignoradas."),
 ("identificar gerado/editado por IA", "A", "Tarja neutra legível; sem declarar validação inexistente."),
 ("não usar pessoa real sem autorização", "L", "Pessoas fictícias solicitadas; ausência de semelhança com qualquer pessoa não é demonstrável automaticamente."),
 ("ACEITE: peça revisada e nota de proveniência", "L", "Aprovação local real por SHA existe; é privada/ignorada pelo Git. Precisa seleção e revisão de privacidade no ZIP, sem publicar identidade Windows.")]),
11: (6, "src/audit.py; registros de texto/STT/OCR/imagem", "Logs existentes; testes novos de sanitização/histórico/fontes", "test_auditoria_final; test_publicacao_rf10", [
 ("identificador, data/hora, modalidade e origem", "L", "Origem textual nova corrigida. Histórico pode apontar arquivo inexistente; datas locais antigas não têm timezone explícito."),
 ("provedor, modelo, parâmetros e versão do prompt", "L", "Novos registros preservam max_tokens e prompt exato; parâmetros históricos foram parcialmente redigidos ou ausentes."),
 ("resultado e duração", "A", "Campos persistidos, sem inferir fidelidade a partir de sucesso técnico."),
 ("erros e decisão humana", "L", "Histórico de decisões novas preservado; decisões antigas sobrescritas não podem ser reconstruídas por invenção."),
 ("não armazenar chave API", "L", "Sanitização recursiva e varredura; limites de detecção explicitados."),
 ("relacionar saída ao caso", "L", "Novos snapshots/IDs/fontes fortes; artefatos legados sem vínculo completo continuam fracos."),
 ("ACEITE: reconstruir saída sem segredos", "P", "Reconstrução nova testada com mocks; não implica determinismo remoto nem comprova todos os registros antigos.")]),
12: (6, "LGPDManager; .gitignore; .dockerignore; web_files.py", "varredura_segredos.json; README; matriz de campos", "test_auditoria_final; test_sistema; testes de rotas", [
 ("usar somente dados fictícios", "L", "Fixtures são fornecidas pelo desafio; texto livre depende do operador. Logs privados contêm identidade local real do revisor."),
 ("identificar campos pessoais em cenário real", "A", "Matriz expandida para campos de extração e contexto; CPF não é automaticamente classificado como dado sensível."),
 ("informar finalidade de cada campo", "L", "Matriz contextual; finalidade institucional real exigiria análise do controlador."),
 ("informar necessidade de cada campo", "L", "Presença no schema não prova necessidade legal. Não presumir coleta obrigatória."),
 ("informar risco de cada campo", "A", "Riscos individuais/associação documentados."),
 ("minimizar envio ao provedor", "P", "STT/OCR locais, imagem sem dados pessoais; texto fictício integral enviado ao LLM. Máscara de tela não é anonimização do payload."),
 ("ACEITE: nenhuma evidência entregue com credencial ou dado real", "P", "Árvore/histórico textual verificados com limites; ZIP final não foi montado nem inspecionado. Excluir .env e identidade Windows privada.")]),
13: (6, "QualityEvaluator; AuditLogger.resumo_revisoes; revisão UI", "Comparações reais e histórico de decisões; protocolo_avaliacao.md", "test_conferencia_ausencias; test_auditoria_final; DOM/ASGI", [
 ("avaliar fidelidade", "A", "Esperado x obtido; ausências coincidentes não viram acertos/divergências."),
 ("avaliar completude", "A", "Denominador considera disponibilidade na fonte; omissões continuam penalizadas."),
 ("avaliar formato", "A", "Schema e regras de apresentação; formato não é prova de verdade."),
 ("avaliar linguagem", "L", "Protocolo editorial documentado; avaliação humana sistemática das minutas não consolidada."),
 ("avaliar segurança", "L", "Testes de injeção/acesso/hash; nenhuma garantia absoluta contra LLM ou endpoint exposto sem autenticação."),
 ("registrar esperado e obtido em cada caso", "L", "Áudio/OCR/texto têm referências; personalizado/imagem precisam referência editorial própria anterior, não uma meta criada depois."),
 ("classificar erros por gravidade", "L", "Textual separa pendência/divergência; protocolo unifica multimodal, mas logs históricos STT/OCR não têm gravidade por campo."),
 ("definir nova geração ou correção manual", "A", "Protocolo novo: erros críticos bloqueiam; incerteza permanece pendente; correção exige fonte."),
 ("calcular taxa simples de aprovação", "L", "Endpoint novo calcula aprovados/decididos e explica denominador. Base histórica mistura testes antigos; taxa de coorte real controlada pendente."),
 ("registrar limitações e riscos residuais", "A", "README, relatório e auditoria explicitam qualidade, memória, fornecedores e autenticação."),
 ("ACEITE: demonstrar caso aprovado e rejeitado OU corrigido", "P", "Aprovação real existe. Rejeição/correção testada com mocks; NÃO COMPROVADA decisão humana real adversarial inequívoca na coorte final.")])}


def gerar():
    linhas = []
    for rf, (pagina, implementacao, evidencia, teste, itens) in REQUISITOS.items():
        for i, (literal, status, risco) in enumerate(itens, 1):
            linhas.append([f"§7 RF{rf:02d}.{i} p.{pagina}", f"RF{rf:02d}", literal,
                implementacao, evidencia, teste, "Roteiro de 12 minutos; localizar arquivo/endpoint indicado",
                STATUS[status], risco])
    extras = [
        ("§1", "Dados exclusivamente fictícios", "L", "Não é verificável automaticamente em texto livre; exclusão de identidades reais na entrega é manual."),
        ("§1", "Originais inalterados e artefatos em diretórios próprios", "A", "Áudio/PDF idênticos ao ZIP; texto equivalente após CRLF; 306 hashes protegidos."),
        ("§1", "Sem chaves, credenciais e dados reais no repositório", "L", "Varredura sem ocorrências reconhecidas; não é prova de todas as chaves antigas arbitrárias."),
        ("§1", "README com decisões, limitações, custos, modelos e execução", "A", "README e relatório revisados; custos não disponíveis não viram zero."),
        ("§2", "Distinguir IA, ML, DL, generativa, linguagem e raciocínio", "E", "Quadro conceitual no roteiro; compreensão oral individual NÃO COMPROVADA pelo agente."),
        ("§2", "Selecionar modelos por finalidade, custo, privacidade, abertura e multimodalidade", "L", "Justificativas presentes; SAPI5 é proprietário e os custos de fornecedores não são presumidos."),
        ("§3", "Decisão final com servidor e sem envio automático", "A", "Geração não despacha; aprovações são explícitas; RF10 normal bloqueado."),
        ("§5", "Equipe até três, todos compreendem solução completa", "E", "Responsabilidade documentada; número de integrantes e compreensão precisam confirmação humana."),
        ("§6", "Solicitação textual", "A", "entrada_texto.txt fornecida pelo desafio e JSONs/minutas reais."),
        ("§6", "Mensagem de voz e ruído moderado", "L", "MP3 oficial 89,16 s processado; teste controlado de robustez ao ruído NÃO COMPROVADO."),
        ("§6", "Imagem/documento digitalizado", "A", "PDF oficial e raster sintético; qualidade oficial baixa não foi escondida."),
        ("§6", "Imagem institucional GOV.MT usada na minuta", "A", "Brasão inserido pelo PDF, sem recriação por IA; manual visual externo não foi fornecido."),
        ("§6", "Cada caso com esperado elaborado antes da execução", "L", "Gabaritos existentes; data de elaboração anterior de toda a coorte NÃO COMPROVADA independentemente."),
        ("§7", "Serviço pago indisponível permite cota/modelo aberto equivalente documentado", "A", "Substituições documentadas; o texto não exige custo zero nem fornecedor específico."),
        ("§8", "Entrada original e registro do caso", "L", "Snapshots novos corrigidos; origem legada por vezes inexistente."),
        ("§8", "Extração com bruto, revisado e comparação", "A", "Versões em campos JSON separados; não exige dois arquivos físicos."),
        ("§8", "Compreensão em JSON e ausências", "A", "Contrato de produção e avaliação de pendências."),
        ("§8", "Geração com prompt, saída e fontes", "L", "Corrigida em novas saídas; histórico não refeito."),
        ("§8", "Acessibilidade com arquivo e configurações", "L", "WAV real; precisa audição humana e confirmação da interpretação SAPI5/API."),
        ("§8", "Comunicação visual com imagem/prompt/proveniência", "L", "Existe localmente; preparar seleção privada sem dados reais para ZIP."),
        ("§8", "Revisão com decisão e justificativa", "L", "Persistência nova; amostra real aprovado/rejeitado precisa ser consolidada."),
        ("§8", "Auditoria de modelos, parâmetros, erros, tempos e custos", "L", "Custos desconhecidos marcados como desconhecidos; logs legados incompletos."),
        ("§9", "Estrutura sugerida de diretórios", "A", "Todos os diretórios principais presentes; estrutura é sugerida, não requisito de infra GPU."),
        ("§10", "Ferramentas, modelos e versões usados pela IA", "L", "Registro atualizado; versão exata do assistente não registrada, sem invenção."),
        ("§10", "Pelo menos três solicitações relevantes à IA", "A", "Excertos reais desta conversa registrados na seção 7 do registro de uso."),
        ("§10", "Sugestões aceitas, modificadas e rejeitadas", "A", "Registro distingue mocks de teste e produção."),
        ("§10", "Erros/inadequações e forma de validação", "A", "Auditoria e testes de regressão identificados; não confundir mocks com execução real."),
        ("§10", "Declaração de responsabilidade da equipe", "L", "Existe texto; a equipe deve confirmar compreensão e responsabilidade, sem assinatura pelo agente."),
        ("§11", "Arquivo compactado com todos os entregáveis", "N", "NÃO COMPROVADO um ZIP final completo, revisado e sem credenciais. ZIP complementar não o substitui."),
        ("§12", "Apresentação até 12 minutos com seis blocos", "L", "Roteiro fornecido; ensaio humano cronometrado NÃO COMPROVADO."),
        ("§13", "Sem dados reais/sigilosos/pessoas sem autorização", "L", "Só usar casos fictícios; revisão privada deve ser depurada antes de compartilhar."),
        ("§13", "Não publicar .env/credenciais", "A", ".gitignore e .dockerignore; nenhum push ou pacote de segredos nesta auditoria."),
        ("§13", "Não afirmar autoria exclusivamente humana", "A", "Tarja IA e registro do uso de Codex/assistentes."),
        ("§13", "Não testar sistemas externos/contornar controles sem autorização", "A", "Sem inferência externa, bypass RF10 ou autenticação paralela."),
        ("§13", "Validar informação crítica antes de considerá-la correta", "P", "Bloqueio novo cobre origem multimodal; confirmação humana real e avaliação de linguagem ainda pendentes.")]
    for i, (secao, literal, status, risco) in enumerate(extras, 1):
        linhas.append([f"{secao} adicional {i}", "TRANSVERSAL", literal, "README; código; relatório; roteiro",
            "integridade_antes.json; índice de evidências; artefatos locais", "Suíte offline/DOM/ASGI quando aplicável",
            "roteiro_demonstracao.md", STATUS[status], risco])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Item do enunciado", "RF", "Exigência literal", "Implementação", "Evidência", "Teste", "Demonstração", "Status", "Risco"])
        w.writerows(linhas)
    print(f"Matriz: {len(linhas)} verificações separadas; {DESTINO.name}")


if __name__ == "__main__":
    gerar()
