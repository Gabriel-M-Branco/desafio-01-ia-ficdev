# Minimização e privacidade — limites operacionais reais

Escopo: protótipo acadêmico com dados fictícios. Não é parecer jurídico nem
declaração de conformidade integral. Não processar dados pessoais reais na demonstração.

| Fluxo | O que sai do computador | Controle/limitação |
|---|---|---|
| RF02/RF09 OpenRouter | Texto fornecido e instruções; podem conter identificadores fictícios | Minimização automática parcial; máscara da tela não altera o payload. Equipe deve revisar a entrada antes da chamada |
| RF06 local | Áudio permanece local; cache small deve existir | Escolha local preservada; não ativar HF por conveniência |
| RF07 SAPI5 | Texto sintetizado localmente | Exige aprovação por hash; edge-tts alternativo exige rede, não presumir privacidade local nesse modo |
| RF08 local | PDF/recortes permanecem locais | Textos, JSONs e logs continuam identificáveis localmente |
| RF10 Cloudflare | Prompt e parâmetros de geração | Usar apenas cenário educacional genérico, sem nomes, CPF, matrícula ou dados pessoais; brasão e tipografia são compostos localmente |
| HF/endpoint opcional | Depende do provedor/modalidade configurados | Não habilitar automaticamente; revisar finalidade e dados antes de uso |

CPF/RG/telefone/nascimento/filiação/endereço são identificadores pessoais no uso
real, mesmo que nem todos sejam dados sensíveis pela definição legal. Nome de
curso e turno podem identificar alguém por associação. Não declarar finalidade,
base legal, consentimento ou prazo legal sem definição real da instituição.

## Antes de enviar ou compartilhar

1. Usar fixtures fictícias fornecidas; verificar se qualquer caso personalizado
   introduziu dados reais, credenciais, endereço privado ou informação desnecessária.
2. Preferir descrição do pedido sem identificadores desnecessários em novos casos,
   sem alterar os originais oficiais. Se o teste exige extração de um campo, explicar
   sua necessidade e manter o caso fictício; não alegar anonimização automática.
3. Inspecionar texto, PDFs, imagens, áudio, metadados e logs. Revisão de binários é
   humana: uma varredura de texto não lê voz/rostos/texto rasterizado.
4. Excluir `.env`, diagnósticos LLM, SID/nome de conta Windows, caminhos pessoais,
   caches, histórico completo e logs não selecionados. Não compartilhar chave da equipe
   com o professor; cada avaliador configura suas próprias credenciais fora do ZIP.
5. Manter originais locais intactos. Se uma cópia precisar anonimização para envio,
   criar derivada separada e documentar transformações; seus hashes não serão os
   da aprovação original. Não afirmar que a derivada foi aprovada automaticamente.
6. Definir com a equipe responsável pelo pacote, destinatários/acesso e data de
   revisão/eliminação das cópias de avaliação. Nenhuma exclusão automática foi feita:
   evidências existentes estão preservadas e o prazo institucional é NÃO DEFINIDO.

## O que o sistema não garante

Sem autenticação geral, servidor restrito a loopback e casos fictícios são essenciais.
Rotas administrativas RF10 continuam 503. Aprovação textual declarada não autentica
pessoa. Logs recebem redaction de segredos conhecidos, mas não anonimização completa.
Criptografia em repouso, retenção automática, controle institucional de acesso e
termos vigentes de tratamento do provedor não foram certificados nesta entrega.
