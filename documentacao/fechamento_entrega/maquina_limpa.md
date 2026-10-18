# Checklist de reprodução em outro Windows

Preencher numa cópia local: data, responsável, Windows/arquitetura, Python e resultado
por etapa. Estados: NÃO EXECUTADO, PASSOU, FALHOU ou BLOQUEADO com causa. Este checklist
não é evidência de instalação já realizada.

1. Extrair ZIP em caminho curto, por exemplo `C:\projetos\ficdev-avaliacao`; verificar
   `MANIFESTO_SHA256.json` antes de editar. Não reutilizar `.venv` de outro computador.
2. Usar Python **3.13 x64**, referência testada; `py -3.13 --version`. Python 3.11+
   é suportado pelo projeto, mas outras versões não foram comprovadas nesta auditoria.
3. Criar ambiente e instalar conscientemente (acesso ao índice/download necessário):
   `py -3.13 -m venv .venv`; depois
   `.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements-validado.txt`.
   Rodar `python -m pip check` usando o Python da `.venv`. O arquivo de restrições é
   snapshot das distribuições instaladas, sem hashes de wheels; não garante disponibilidade
   futura no índice nem equivalência de sistema/voz/modelo. Se uma versão falhar, registrar
   a causa; não atualizar silenciosamente nem trocar provedores para obter aprovação.
4. Criar `.env` a partir do exemplo apenas se não existir. Configurar chave própria
   OpenRouter e Cloudflare quando autorizado; manter modelo Gemini validado e fallback
   none. Não enviar valores em capturas/logs. Credenciais não acompanham o ZIP.
5. Tesseract em `C:\Program Files\Tesseract-OCR` e idioma `por`; validar caminho e
   dados de idioma. Maria pt-BR instalada no Windows. Fontes TrueType Unicode disponíveis.
6. Preparar cache `Systran/faster-whisper-small` por download manual autorizado conforme
   README. Manter local/small/CPU/int8/pt. Liberar RAM e verificar paginação do Windows;
   não prometer limiar universal de RAM. Instalação Python não inclui o modelo/voz/Tesseract.
7. Executar suíte offline e ambos validadores DOM; Edge opcional conforme README.
   Testes usam mocks, não comprovam qualidade real. Registrar contagens/ignorados/causas.
8. Iniciar `.\.venv\Scripts\python.exe -m src.main --host 127.0.0.1 --port 8000`;
   verificar badge, abas e mensagens. Não expor na rede. RF10 normal deve continuar 503.
9. Com autorização de custo, validar texto/minuta; conferir/decidir manualmente antes
   do TTS. Sem autorização, marcar teste remoto BLOQUEADO e usar evidência histórica
   como histórico, sem afirmar nova execução. Não usar `--run-all` como atalho de aprovação.
10. Testar RF06 isolado e RF08 local se houver recursos; registrar tempo, campos e
    pendências. Oficial 0/23 permanece insatisfatório. Sintético é cenário separado.
11. RF10: mostrar artefato real existente e proveniência; não remover bloqueio nem
    gerar de novo só para conferir instalação. Executor local requer ativação explícita
    e autorização de cota; imagem gerada inicia pendente.
12. Registrar falhas, limitações e passos exatos. Ouvir WAV e revisar PNG/Unicode.
    Conferir decisão/hash e conteúdo selecionado, sem alterar aprovação original.

Docker/Linux permanece alternativa **não validada**; não usar este checklist Windows
como atestado Docker. Node/Edge são requisitos dos validadores, não da síntese/OCR.
