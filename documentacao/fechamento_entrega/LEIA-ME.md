# Fechamento da entrega — ações humanas ainda pendentes

Este diretório complementa, sem reescrever, a auditoria de 18/10/2026. Modelos de
fichas não são evidências preenchidas, decisões ou avaliações assinadas.
Nenhuma chamada de IA é necessária para executar as ferramentas deste diretório.

## Ordem operacional

1. Preparar o Windows seguindo `maquina_limpa.md`; reiniciar o servidor para carregar
   o código atual. Usar somente dados fictícios e `127.0.0.1:8000`.
2. RF02: abrir a fonte e as saídas históricas indicadas em `rf02_avaliacao.md`;
   preencher os seis critérios e a escolha justificada em cópia da ficha CSV.
   Não criar tempos passados nem inferir parâmetros ausentes.
3. RF06: Atendimento → transcrição de áudio; ouvir a fonte, conferir nome/protocolo/
   datas/curso/carga horária/turno. Corrigir somente com o áudio. Confirmar com
   justificativa se os dados críticos estiverem verificáveis; caso contrário,
   usar **Rejeitar leitura não confiável**. Não usar o gabarito para preencher.
4. RF08: Atendimento → documento OCR; confrontar PDF e cada campo. O oficial 0/23
   exige revisão e pode precisar rejeição. Dado ilegível fica pendente. O sintético
   22/23 é demonstração distinta, não recuperação do PDF oficial. Confirmar apenas
   uma leitura cujo uso seja defensável; se isso não for possível, rejeitar.
5. RF13: conferir uma minuta fictícia e registrar APROVADO somente se merecido.
   Selecionar outro caso real distinto e registrar REJEITADO ou CORRIGIDO se houver
   motivo efetivo. Não criar erro artificial nem rejeitar peça correta para preencher
   cota. Se não existir segundo caso adequado, a evidência continua pendente.
6. Copiar `coorte_rf13.modelo.json` para `.entrega-local/coorte.json`, preencher IDs,
   caminhos, hashes, cinco critérios e confirmação humana; validar com o comando
   abaixo. A aprovação da fonte não conta como aprovação da minuta.
7. Ouvir o WAV já aprovado, revisar o PNG existente e conferir a avaliação RF02.
   Não gerar nova imagem nem alterar a imagem aprovada só para esta entrega.
8. Selecionar evidências e revisar privacidade conforme `lgpd_minimizacao.md` e
   `zip_final.md`. Criar ZIP novo, extrair/testar em máquina limpa e registrar resultados.
9. Ensaiar os 12 minutos com o roteiro da auditoria. O teste em outra máquina e as
   decisões acima são ações da equipe, não certificações do agente.

```powershell
New-Item -ItemType Directory -Force .entrega-local
Copy-Item documentacao/fechamento_entrega/coorte_rf13.modelo.json .entrega-local/coorte.json
# Preencher a cópia; o modelo intencionalmente não passa até ser completado.
.\.venv\Scripts\python.exe -m ferramentas.fechar_entrega coorte .entrega-local/coorte.json
```

O verificador RF13 apenas lê registros: confirma IDs distintos, modalidade final
texto, status, justificativa/responsável/data, referência e hashes. Não autentica o
operador, não decide e não registra aprovação. Mudanças posteriores exigem renovar
os hashes da ficha depois de conferir novamente. CORRIGIDO continua sem autorizar TTS.
Logs da ficha podem conter identidade: permanecem privados até revisão de envio.

## Situação do fechamento

- Estrutura RF02, instrumento RF13, orientações de revisão, política de minimização,
  restrições reproduzíveis e ferramentas de ZIP: preparados automaticamente.
- Fidelidade final, avaliação assinada, amostra humana e reprodução limpa: dependem
  da equipe. Nenhuma dessas pendências é resolvida apenas por existir este documento.
- O relatório da auditoria é uma fotografia anterior; suas notas sobre ausência de
  ferramentas/checklists devem ser lidas com este complemento. Seus resultados reais
  e pendências humanas permanecem válidos.
