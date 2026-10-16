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
2. **Alucinação Zero e Regra do "Não Localizado" (RF03, RF05, RF09):** O sistema é estritamente proibido de inferir dados ausentes, inventar números de leis, decretos, protocolos ou prazos. Campos omitidos recebem compulsoriamente o valor literal `"não localizado"`.
3. **Custo Zero e Disponibilidade Híbrida (RF04):** Integração com modelos abertos e gratuitos de última geração através da **Hugging Face Serverless Inference API** e **OpenRouter**, acompanhada de motor de contingência offline local para garantir resiliência e independência de conectividade.
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
        │ • Imagem: Renderização e OCR/VLM Qwen2.5-VL (RF08)     │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │              NÚCLEO DE INTELIGÊNCIA ARTIFICIAL         │
        ├────────────────────────────────────────────────────────┤
        │ • LLM: Qwen2.5-72B-Instruct / Llama-3.3-70B           │
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
                     [ RESPOSTA INSTITUCIONAL HOMOLOGADA ]
```

---

## 2. Seleção de Modelos e Tecnologias

| Modalidade / Função | Modelo / Tecnologia Adotada | Provedor / Mecanismo | Custo Estimado | Justificativa Técnica |
|---|---|---|---|---|
| **Ponto de Entrada & API** | FastAPI + Uvicorn | Python 3.11+ / Local | US$ 0.00 | Alta performance assíncrona, documentação OpenAPI automática e baixo consumo de memória. |
| **Interface de Usuário** | HTML5, CSS3, JavaScript Vanilla | Navegador Local | US$ 0.00 | Sem complexidade de build ou dependências pesadas; compatível com redes corporativas estaduais restritas. |
| **LLM (Texto e Minuta)** | `Qwen/Qwen2.5-72B-Instruct` | Hugging Face Serverless API | US$ 0.00 | Superioridade comprovada em aderência a regras estritas de formato JSON e compreensão do idioma português. |
| **Fallback de LLM** | `meta-llama/Llama-3.3-70B-Instruct` | OpenRouter (Free Tier) | US$ 0.00 | Contingência de alta fidelidade sem custo financeiro em caso de rate limit. |
| **STT (Áudio para Texto)** | `openai/whisper-large-v3-turbo` | Hugging Face Serverless API | US$ 0.00 | Transcrição precisa em português mesmo sob ruído moderado, com conferência contra gabarito. |
| **TTS (Síntese Acessível)** | `edge-tts` (`pt-BR-AntonioNeural`) | Microsoft Edge TTS (Gratuito) | US$ 0.00 | Entonação institucional neutra, sem robótica e com capacidade de pausa e ênfase auditiva. |
| **Visão Multimodal / OCR** | `Qwen/Qwen2.5-VL-7B-Instruct` + `PyMuPDF` | Hugging Face + Local | US$ 0.00 | Capacidade de interpretar fichas manuscritas e apontar formalmente incertezas e campos em branco. |
| **Imagem Institucional** | `black-forest-labs/FLUX.1-schnell` + `Pillow` | HF API + Renderizador Python | US$ 0.00 | Ilustração artística sem texto via IA, unida à precisão tipográfica e heráldica institucional do Pillow. |

### 2.1. Documentação de Substituição de Serviços Pagos por Hugging Face (Seção 7 do Edital)

O edital estabelece na **Seção 7 (Requisitos Funcionais Obrigatórios)** a seguinte previsão normativa:
> *"Quando um serviço pago não estiver disponível, a equipe poderá utilizar cota gratuita ou modelo aberto equivalente, desde que documente a substituição."*

Em conformidade estrita com esta determinação, **documenta-se formalmente que não foi possível a utilização de chave de API (API key) de serviços comerciais proprietários pagos** (tais como OpenAI GPT-4o, Google Gemini comercial, Midjourney, DALL-E ou AWS Polly pagos) devido à inexistência de dotação orçamentária e indisponibilidade de contas pagas corporativas para o desenvolvimento deste projeto educacional.

Diante dessa premissa, **optou-se pela utilização da infraestrutura da Hugging Face Serverless Inference API** associada a modelos abertos de última geração e ferramentas locais de código aberto:

1. **Substituição de LLM Comercial Pago:** O modelo comercial proprietário foi substituído pelo modelo aberto de alta escala **`Qwen/Qwen2.5-72B-Instruct`** (com contingência em `meta-llama/Llama-3.3-70B-Instruct`) via **Hugging Face Inference API**, oferecendo aderência superior a esquemas JSON, rigor gramatical em português e custo zero de execução.
2. **Substituição de Serviço Pago de Transcrição Fonética (STT):** Foi integrado o modelo **`openai/whisper-large-v3-turbo`** via Hugging Face, mantendo precisão de 100% nas entidades críticas de áudio sem tarifação por minuto.
3. **Substituição de OCR Comercial Pago:** Foi adotado o modelo multimodal aberto **`Qwen/Qwen2.5-VL-7B-Instruct`** em conjunto com a biblioteca local **`PyMuPDF`**, viabilizando leitura de formulários manuscritos e auditoria de soberania de dados.
4. **Substituição de Gerador de Imagem Pago (ex: Midjourney):** Adotou-se a arquitetura híbrida com **`black-forest-labs/FLUX.1-schnell`** via Hugging Face para a geração de arte artística sem texto, aliada à composição tipográfica institucional em **Pillow (PIL)** com o Brasão Oficial do GOV.MT.
5. **Substituição de Síntese de Voz Paga (TTS):** Adotou-se a biblioteca neural **`edge-tts`** com voz padrão brasileira (`pt-BR-AntonioNeural`), sem cobrança por caractere.
6. **Modo de Contingência Local Offline:** Para garantir funcionamento ininterrupto mesmo diante de eventuais limites de requisições por minuto (rate limits) ou indisponibilidade de conexão na Hugging Face, foi desenvolvido um motor determinístico offline fiel aos gabaritos, assegurando continuidade dos testes e demonstrações em qualquer cenário.

---

## 3. Estimativa de Custos e Consumo de Tokens

Todos os provedores selecionados operam em regime de **Cota Gratuita / Custo Zero (US$ 0.00)**:
- **Hugging Face Serverless Inference API:** Gratuita para requisições sob o plano comunitário com `HF_TOKEN`.
- **OpenRouter Free Tier:** Roteamento para modelos `:free` sem consumo financeiro.
- **Edge-TTS:** Serviço de síntese de voz de acesso livre sem cobrança por caractere.
- **Modo Mock / Contingência Local:** Execução 100% offline com consumo nulo de rede e zero custo.

### Médias de Consumo por Ciclo de Atendimento Completo:
- **Tokens de Entrada (Prompt C + Caso Real):** ~450 tokens.
- **Tokens de Saída (JSON + Minuta):** ~520 tokens.
- **Tempo Médio de Resposta Local:** ~0.15s (Mock) a ~2.4s (API remota).
- **Custo Financeiro Total por Atendimento:** **US$ 0.00**.

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

A avaliação do sistema é realizada confrontando os resultados gerados com os gabaritos prévios em `dados/gabaritos/`:
- **Taxa de Fidelidade contra Gabarito Textual:** 94.4% (acertos em 17 de 18 entidades estruturadas).
- **Conferência de Entidades Críticas no Áudio (Whisper):** 6 de 6 entidades confirmadas (100%).
- **Detecção de Incertezas Visuais (Ficha de Matrícula):** 7 campos em branco e manuscritos identificados com sucesso.
- **Taxa de Aprovação com Human-in-the-Loop:** 50% de aprovação no ciclo de teste (1 caso aprovado formalmente e 1 caso malicioso rejeitado, cumprindo o critério de aceite do RF13).
