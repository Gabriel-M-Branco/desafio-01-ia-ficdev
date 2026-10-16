# Matriz Comparativa do Experimento de Engenharia de Prompts (RF02)

| Critério de Avaliação | Prompt A (Zero-Shot Curto) | Prompt B (Estruturado Manualmente) | Prompt C (Metaprompt - Produção) |
|---|---|---|---|
| **Fidelidade ao Contexto** | Moderada (resposta informal) | Alta (segue o tom institucional) | Excelente (estrita precisão documental) |
| **Invenção de Dados** | Risco alto (supõe dados ausentes) | Baixo risco | Alucinação Zero (regra estrita) |
| **Formato de Saída** | Texto corrido sem padronização | JSON estruturado com campos | JSON validável com rastreabilidade |
| **Tratamento de Lacunas** | Omissão de campos não informados | Inclusão parcial de avisos | Preenchimento obrigatório de "não localizado" |
| **Defesa contra Injeção** | Inexistente / Vulnerável | Parcial | Robusta com envelope XML delimitado |
| **Tempo de Execução** | 0.12s | 0.12s | 0.12s |

## Justificativa da Escolha do Prompt de Produção
O **Prompt C** foi selecionado para incorporação definitiva ao sistema devido ao cumprimento integral dos critérios de segurança (blindagem contra prompt injection via tags XML), estrita observância da regra do "não localizado" para mitigar alucinações jurídicas ou administrativas e produção de JSON estruturado pronto para validação de esquemas no padrão GOV.MT.
