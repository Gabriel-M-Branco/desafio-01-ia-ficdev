# RF02 — ficha e método de avaliação final

## Material existente, sem novas chamadas

- Fonte: `dados/originais/entrada_texto.txt`.
- Experimento: `prompts/experimento_02d9f28ad4f8458fb865ba99ce938b39/`.
- Avaliação editorial: `documentacao/auditoria_final/analise_prompts_observada.md`.
- Prompts vigentes: `src/prompts.py`; não confundir a versão atual com a histórica.
- Modelo registrado nos três resultados: `google/gemini-3.8-flash`, via OpenRouter.
- Tempos de API históricos: A 11,4423 s; B 10,1677 s; C 8,1817 s.
- Parâmetros antigos completos e tempo histórico até uso: NÃO COMPROVADOS.

## Preenchimento pela equipe

Copiar `rf02_ficha.modelo.csv` para `.entrega-local/`; usar Excel com UTF-8 e `;`.
Para cada versão, registrar trecho/problema verificável, julgamento e correção
necessária. Avaliar seis critérios: fidelidade; invenções; formato; tom; lacunas;
tempo até resultado utilizável. Não converter automaticamente crítica editorial em
assinatura de um integrante. O resultado técnico vigente prefere C, mas a escolha
final exige justificar os seis critérios, sem alegar alucinação zero.

Se revisar as saídas existentes agora, medir o tempo de revisão **agora**, com início
e fim; isso não reconstrói o tempo histórico. A soma API antiga + revisão atual deve
ser rotulada estimativa retrospectiva, nunca medição de uma execução contínua.
Uma repetição controlada futura exigiria mesma entrada/modelo/parâmetros, prompts
exatos, hashes, tempos de API/revisão separados e autorização de custo. Não repetir
apenas para melhorar pontuação; não escolher saída pelo gabarito.

## Registro complementar obrigatório

Na cópia preenchida, acrescentar: avaliador, data, fonte/saídas e hashes; parâmetros
conhecidos e desconhecidos; início/fim da revisão atual; escolha A/B/C e justificativa;
limitações; descrição do metaprompt e seus artefatos realmente existentes. Onde não
houver cadeia histórica verificável, escrever NÃO COMPROVADO. Não inventar uma
conversa retroativa de criação do metaprompt.

Questões já observadas para conferência: pré-registro/autuação não comprovados;
normas/cópias/notificações sem fonte; campos ausentes no schema histórico.
Corrigir eventual minuta em nova versão deliberada; preservar saídas A/B/C originais.
