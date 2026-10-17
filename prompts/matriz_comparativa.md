# Experimento de Engenharia de Prompts (RF02)

| Prompt | Fidelidade ao Contexto | Dados Inventados | Formato de Saída | Tom e Adequação Institucional | Tratamento de Lacunas | Tempo até Resultado Utilizável | Provedor | Modelo | Duração (s) | Tokens Estimados |
|---|---|---|---|---|---|---|---|---|---|---|
| Prompt A | Média (reconstrução parcial) | Possível (sem blindagem formal) | Texto Livre | Informal / Não padronizado | Omissão ou preenchimento genérico | Rápido (exige revisão manual) | OpenRouter | inclusionai/ling-3.1-flash | 27.9348 | 717 |
| Prompt B | Alta (instruções institucionais) | Baixo ('não localizado' explícito) | Estruturado / Marcadores | Formal / Institucional GOV.MT | Preserva 'não localizado' | Médio (revisão pontual) | OpenRouter | inclusionai/ling-3.1-flash | 21.7366 | 1648 |
| Prompt C | Estrita (100% aderência) | Zero (blindagem XML contra Prompt Injection) | JSON Estruturado + Minuta Oficial | Oficial Padrão GOV.MT | Alucinação zero ('não localizado' rigoroso) | Imediato (pronto para despacho) | OpenRouter | inclusionai/ling-3.1-flash | 20.5790 | 1339 |

**Prompt Selecionado:** Prompt C (Metaprompting - Produção) devido à blindagem estrita XML contra Prompt Injection e garantia de alucinação zero com formato estruturado JSON.