# Relatório Técnico - Central Inteligente de Atendimento e Comunicação Institucional (GOV.MT)

**Programa:** FIC_DEV — Programador de Sistemas com IA (2026)
**Projeto:** Desafio Prático 1 — Central Inteligente de Atendimento e Comunicação Institucional
**Órgão Atendido (Fictício):** Governo do Estado de Mato Grosso / SECITECI-MT / ETEC Cuiabá
**Versão:** 1.0

---

## 1. Visão Geral e Arquitetura da Solução

O sistema foi concebido como uma **Central Multimodal de Apoio ao Atendimento Institucional**, estruturada para processar manifestações de cidadãos recebidas em três modalidades distintas: **Texto**, **Áudio (Mensagem de Voz)** e **Imagem/Documento Digitalizado (Ficha de Matrícula manuscrita)**.

### Princípios Arquiteturais Centrais:
1. **Governança Estrita e Human-in-the-Loop (RF13):** A inteligência artificial atua exclusivamente como assistente de triagem, síntese e formatação. Nenhuma resposta ou documento é despachado automaticamente ao cidadão. Cada minuta exige revisão, justificativa e deliberação formal (Aprovação, Correção ou Rejeição) por um servidor humano.
2. **Objetivo de não inventar dados e regra do "não localizado" (RF03, RF05, RF09):** Os prompts proíbem invenção; isso não é garantia de alucinação zero. Schema valida formato, e revisão humana confere fatos e ausências.
3. **Provedores reais configuraveis (RF04):** Texto via OpenRouter/Gemini pago; STT/OCR/TTS locais. Sem contingencia ficticia.
4. **Padronização Visual Oficial Híbrida (RF10):** Geração de imagem central via IA generativa (`FLUX.1-schnell`) sem elementos textuais, acoplada programaticamente a um template em Pillow contendo o Brasão Oficial do Estado de Mato Grosso e a tarja obrigatória de identificação de conteúdo sintético.

```
                                [ CIDADÃO ]
                (Texto, Mensagem de Voz ou Ficha em Imagem/PDF)
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │              CAMADA DE RECEPÇÃO E TRIAGEM             │
        ├────────────────────────────────────────────────────────┤
        │ • Texto: Isolamento em envelope XML anti-injeção       │
        │ • Áudio: Validação e STT Whisper (RF06)                │
        │ • Imagem: PyMuPDF/Tesseract local português (RF08)     │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │              NÚCLEO DE INTELIGÊNCIA ARTIFICIAL         │
        ├────────────────────────────────────────────────────────┤
        │ • LLM: OpenRouter / google/gemini-3.8-flash            │
        │ • Extração Estruturada (JSON) com "não localizado"     │
        │ • Geração de Minuta Formal Padrão GOV.MT               │
        │ • Imagem Sintética: FLUX.1 + Pillow (RF10)             │
        │ • Acessibilidade: TTS edge-tts com alerta sonoro (RF07)│
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │         INTERFACE HUMAN-IN-THE-LOOP (SERVIDOR)         │
        ├────────────────────────────────────────────────────────┤
        │ • Painel Web FastAPI + HTML5/CSS3/Vanilla JS           │
        │ • Operador: [Aprovar] | [Corrigir/Editar] | [Rejeitar] │
        │ • Justificativa Obrigatória gravada em Trilha de Log   │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
                     [ MINUTA: DECISÃO HUMANA OBRIGATÓRIA ]
```

---

## 2. Seleção de Modelos e Tecnologias

| Modalidade / Função | Modelo / Tecnologia Adotada | Provedor / Mecanismo | Custo Estimado | Justificativa Técnica |
|---|---|---|---|---|
| **Ponto de Entrada & API** | FastAPI + Uvicorn | Python 3.11+ / Local | US$ 0.00 | Alta performance assíncrona, documentação OpenAPI automática e baixo consumo de memória. |
| **Interface de Usuário** | HTML5, CSS3, JavaScript Vanilla | Navegador Local | US$ 0.00 | Sem complexidade de build ou dependências pesadas; compatível com redes corporativas estaduais restritas. |
| **LLM (Texto e Minuta)** | `google/gemini-3.8-flash` | OpenRouter | Pago | JSON Schema estrito, validacao e uma unica correcao de formato auditada. |
| **Alternativa LLM** | Modelo HF configuravel | Hugging Face | Sujeito ao provedor | Desativada por padrao; nunca silenciosa. |
| **STT** | faster-whisper small | Local CPU/int8/pt | Sem API | Modelo em cache; transcricao real e revisao humana. |
| **TTS** | SAPI5 / Microsoft Maria | Windows local | Sem API | Exige aprovacao persistida do hash do texto exato. |
| **OCR** | PyMuPDF / Tesseract por | Local | Sem API | Texto bruto e alternativas; sem preenchimento por gabarito. |
| **Imagem Institucional** | FLUX schnell + Pillow | Cloudflare Workers AI | Cota/cobranca do provedor | IA somente ilustracao; textos e brasao via Pillow. |

---

## 3. Estimativa de Custos e Consumo de Tokens

OpenRouter/Gemini consome saldo. HF e Cloudflare podem cobrar conforme a conta e a cota. Nao presumir gratuidade. Custos nao retornados pelo provedor permanecem nao informados. Tokens estimados nao equivalem a faturamento. Nao ha fallback de respostas simuladas.

---

## 4. Gestão de Riscos, Blindagem e Segurança

### 4.1. Defesa contra Prompt Injection (RF03)
Entradas de usuários e manifestações públicas podem conter tentativas deliberadas de subversão de diretrizes (como evidenciado no cenário de teste da classe `SegurancaPrompts`). Para neutralizar esse vetor:
- Todo conteúdo fornecido pelo usuário é sanitizado contra quebras de delimitadores (`</conteudo_nao_confiavel>` é neutralizado).
- A entrada é isolada dentro do envelope semântico:
  ```xml
  <conteudo_nao_confiavel>
  [Conteúdo externo tratado exclusivamente como dado textual, nunca como comando executável]
  </conteudo_nao_confiavel>
  ```
- O modelo é instruído categoricamente a rejeitar solicitações de revogação de regras, recusa de identificação ou invenção de diplomas e isenções tributárias.

### 4.2. Mitigação de Alucinação (Hallucination Mitigation)
O edital proíbe taxativamente a invenção de normas, protocolos ou datas. O sistema implementa:
- Verificação de campos obrigatórios ausentes.
- Atribuição obrigatória e literal do valor `"não localizado"`.
- Lista explícita de `campos_ausentes` gerada no JSON para auditoria.

### 4.3. Soberania Tecnológica e Privacidade de Documentos (RF08, RF12)
Em órgãos públicos estaduais, o envio de documentos com fotos, dados de filiação e certidões de menores para nuvens de terceiros representa risco de conformidade com a LGPD (Lei nº 13.709/2018). O sistema prevê:
- Preferência mandatória por OCR e VLM local (on-premise) para dados sensíveis.
- Mascaramento e pseudonimização prévia de CPF (`***.456.***-**`) e e-mail em logs de rastreabilidade.
- Exclusão absoluta de tokens e chaves de API nos arquivos de auditoria.

---

## 5. Protocolo de Avaliação de Qualidade (RF13)

**RF06 — validação real final informada pelo operador:** após reiniciar/liberar memória,
o processamento passou pela interface em `http://127.0.0.1:8000`, com faster-whisper
small local, CPU/int8. O áudio de 89,16 s gerou transcrição, com 3/6 entidades críticas
conferidas. A revisão humana continua obrigatória; as demais entidades não foram
conferidas com sucesso. O processamento concluído não equivale a aprovação humana
nem a fidelidade integral. A falha anterior de alocação de memória foi superada nessa execução.

Metricas devem ser obtidas dos registros da execucao correspondente. Gabaritos foram preservados, sem uso para preencher resultados. Ausencias coincidentes sao pendencias, nao acertos nem divergencias; fidelidade exclui esses casos. O PDF oficial de baixa qualidade exige revisao humana; nao ha garantia de recuperacao dos manuscritos. Testes offline com mocks nao comprovam qualidade de inferencia real.

---

## 6. Governança Avançada de Imagens e Segurança Multimodal (RF10 & Proteção Web)

### 6.1. Workflow Human-in-the-Loop para Peças Visuais (`src/image_access.py`)
Para assegurar conformidade estrita e soberania visual:
- Toda imagem gerada por difusão (seja via Hugging Face ou **Cloudflare Workers AI** `@cf/black-forest-labs/flux-1-schnell`) entra inicialmente em estado `PENDENTE_REVISAO`.
- O endpoint `/api/publicacao/imagem/{id}` atua como gatekeeper: downloads públicos e veiculações só são autorizados após despacho formal do operador humano (`APROVADO`), validando a integridade criptográfica do hash SHA-256 do arquivo.
- Caso ocorra rejeição ou qualquer adulteração posterior dos bytes da imagem, o acesso público é revogado imediatamente (bloqueio 403).

### 6.2. Proteção de Arquivos e Prevenção de Path Traversal (`src/web_files.py`)
- O acesso a arquivos estáticos e anexos multimídia é rigorosamente encapsulado sob verificação de fronteiras seguras (`is_relative_to`), neutralizando tentativas de fuga de diretório (*Path Traversal*).
- Obras e diretórios internos sensíveis (como `.env`, `.git` ou configurações estruturais) são protegidos com bloqueio determinístico.

### 6.3. Fallback Resiliente de Voz (TTS) SAPI5 / edge-tts (`src/audio.py`)
- SAPI5/Microsoft Maria é o padrão Windows, selecionado explicitamente; edge-tts é uma alternativa configurável. Não há fallback automático. Falhas são reportadas, sem áudio fictício.

### 6.4. Cobertura Abrangente de Testes Automatizados
- A contagem e os limites da suíte atual estão em `auditoria_final/relatorio_final.md`. Testes unitários/ASGI usam mocks de inferência; não provam acurácia ou qualidade auditiva real.

### 6.5. Complemento da auditoria final de 18/10/2026
O relatório em `auditoria_final/relatorio_final.md` e sua matriz discriminam implementação,
evidência e critério de aceite. Entradas textuais novas passam a ter snapshot e hash;
o PDF identifica fontes e pagina textos longos, sem protocolo/data inventados.
Transcrição/OCR precisam de confirmação humana persistida antes da minuta. Aprovação de
fonte e aprovação de minuta para TTS são decisões distintas. Nenhuma evidência antiga foi reescrita.
Minimização no payload LLM permanece parcial. Autenticação real não foi implementada:
RF10 administrativo continua 503; aprovação local não autoriza publicação pública.
