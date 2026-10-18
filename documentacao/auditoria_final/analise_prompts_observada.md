# RF02 — análise dos artefatos existentes, sem nova inferência

Fonte: `prompts/experimento_02d9f28ad4f8458fb865ba99ce938b39/`.
A matriz local registra OpenRouter / `google/gemini-3.8-flash` nos três casos.
Esta é uma análise editorial da auditoria, não uma aprovação humana inventada.
As saídas e a matriz original não foram alteradas. A assinatura dos artefatos consta
do inventário de integridade. Não há registro completo dos parâmetros dessas chamadas antigas.

| Critério | A | B | C |
|---|---|---|---|
| Fidelidade ao contexto | Repete dados do caso em prosa; sugere pré-registro sem prova de ato administrativo | Retoma dados e contexto institucional; afirma recepção/autuação | Retoma pedido e identifica pai/telefone ausentes; ainda sugere recepção/regularização |
| Dados inventados / não comprovados | Alegação de pré-registro deve ser revisada; não comprova matrícula efetivada | Referência genérica a edital/normas/cópias não veio acompanhada de fonte | Orientações de homologação/notificações não são prova de exigências oficiais |
| Formato | Prosa com seções, sem objeto JSON | JSON com extração e minuta | JSON com extração, ausências, confiança e revisão |
| Tom | Formalidade moderada; apresentação em Markdown | Formal institucional, mais extenso | Conciso e institucional; verificar se resolve a pergunta do cidadão |
| Lacunas | Não apresenta estrutura equivalente ao schema de produção | Pai e telefone como “não localizado”; não cobre o schema completo atual | Pai e telefone como “não localizado”; órgão expedidor/UF ausentes do JSON histórico |
| Tempo de API registrado | 11,4423 s | 10,1677 s | 8,1817 s |
| Tempo até uso institucional seguro | NÃO COMPROVADO: falta medir revisão humana | NÃO COMPROVADO | NÃO COMPROVADO |

**Escolha técnica vigente:** C, pela explicitação de isolamento, dados ausentes e
revisão, não por uma alegada garantia de alucinação zero. A produção atual acrescenta
schema completo e uma reparação de formato auditada; não se deve afirmar que o
experimento histórico já utilizava exatamente esse contrato corrigido.

O arquivo raiz `prompts/matriz_comparativa.md` contém alegações de precisão absoluta
e tempos de 0,12 s sem vínculo verificável com este experimento real. É histórico,
**não deve ser usado como evidência de acurácia ou latência real**.

Antes da entrega: a equipe deve conferir o texto original e assinar avaliação dos
seis critérios, justificar as orientações sem fonte ou removê-las em nova minuta
revisada e registrar o tempo de correção. Não executar APIs só para melhorar o relatório.
Se desejar repetir o experimento após mudar prompts/modelo, fazer isso explicitamente,
com autorização de custo; novas execuções passam a salvar entradas exatas e auditoria.
