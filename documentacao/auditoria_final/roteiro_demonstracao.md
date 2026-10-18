# Demonstração em 12 minutos

Preparar antes: ambiente/caches/voz/idioma OCR instalados; navegador local; arquivos
reais selecionados e hashes conferidos; nenhuma credencial visível; áudio testado.
Não depender de nova chamada Cloudflare na banca. Não executar `--run-all` como
substituto da revisão. Levar cópia offline segura dos artefatos selecionados.

| Tempo | Mostrar | Comprova | Pergunta/risco e resposta |
|---|---|---|---|
| 0–2 min | README, diagrama do relatório, badge de provedores e snapshot de versões | RF01/RF04; problema, arquitetura e escolhas | “Tudo é gratuito?” Não: OpenRouter usa saldo; Cloudflare depende de cota. STT/OCR/TTS atuais locais; custos de hardware permanecem. |
| 2–4 min | A/B/C e matriz real `experimento_02d9...`; análise observada | RF02 | “C nunca alucina?” Não. Isolamento/schema ajudam; a auditoria encontrou orientações sem fonte e revisão continua obrigatória. Tempos medidos são API, não tempo de revisão. |
| 4–7 min | Entrada texto; JSON e quatro pendências; transcrição existente 89,16 s/3 de 6; OCR oficial 0/23 e sintético 22/23 | RF03/05/06/08 | “Sucesso com 0/23?” Sucesso de OCR produzir texto, não de extração fiel. Mostrar bruto e pendências; não inventar dados. Conferir origem antes da minuta. |
| 7–9 min | Minuta/PDF com fontes; aprovação textual por hash e WAV real; PNG Cloudflare aprovado localmente + nota/hash | RF07/09/10 | “Por que RF10 web está 503?” Não há autenticação real; executor separado não a contorna. Mostrar artefato já gerado, sem chamar API. SAPI5 usa API COM local; é proprietário. |
| 9–11 min | Resultados da suíte; erro real de memória histórico; caso aprovado e rejeitado/corrigido; LGPD e controles de publicação | RF11/12/13 | “O teste rodou IA?” A suíte/ASGI/Edge usam mocks; o manifesto identifica os testes reais anteriores. Não usar decisão criada por teste como parecer humano real. |
| 11–12 min | Limitações, custos não presumidos, uso de IA e melhorias | §10–§13 | Expor memória, PDF pouco legível, minimização parcial, falta de autenticação e pendências de evidência. Responsabilidade é da equipe. |

## Arquivos a localizar sem pesquisa durante a banca
- Texto aprovado: `resultados/logs/EXEC_20261017_173239_c3ec12.json` e caminhos de saída nele.
- STT real: `resultados/logs/EXEC_20261017_175537_b329c8.json`; conferir a transcrição em `arquivo_transcricao`.
- TTS real: `resultados/logs/EXEC_20261017_173424_bc38cb.json`; verificar hash e arquivo WAV.
- OCR: `dados/processados/validacao_rf08/resumo_oficial.json` e `resumo_sintetico.json`.
- RF10: `.rf10-testes-locais/6364358ce7a14981906a744188492de5/imagens/teste_local_rf10.png`,
  nota de proveniência e decisão vinculada. Não projetar identidade/SID do Windows nem expor a pasta por HTTP.
- Rejeição/correção humana final: **a equipe ainda deve selecionar/registrar um caso real inequívoco**.

## Conceitos que todos devem saber explicar
IA é o campo abrangente; ML aprende padrões a partir de dados; DL usa redes com
múltiplas camadas; IA generativa produz conteúdo; LLM modela linguagem; modelos
de raciocínio dedicam computação adicional a resolver tarefas, sem garantia de verdade.
OCR extrai sinais visuais; não valida manuscrito/assinatura. STT reconhece fala;
TTS sintetiza texto e não confirma sua veracidade. Esquema válido não prova fidelidade.
Geração é produzir arte por modelo; composição Pillow é edição determinística, não inferência.

Não afirmar que seguir a paleta configurada comprova certificação por manual oficial
de identidade visual que não foi fornecido. Não atribuir taxas de teste mockado ao modelo real.
