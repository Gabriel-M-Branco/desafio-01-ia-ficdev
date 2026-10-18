# ZIP final — seleção explícita, revisão e integridade

Não é o ZIP complementar com credenciais. Entrega completa deve conter código atual,
dependências/configuração de exemplo, instruções, entradas fictícias, gabaritos,
prompts A/B/C e respostas reais selecionadas, comparação, resultados multimodais,
relatórios de arquitetura/custos/riscos/LGPD/qualidade/uso de IA e decisões selecionadas.

## Preparação sem empacotar automaticamente

```powershell
New-Item -ItemType Directory -Force .entrega-local
.\.venv\Scripts\python.exe -m ferramentas.fechar_entrega planejar .entrega-local/manifesto.json
```

O plano inclui código, testes, ferramentas, configurações permitidas e dados oficiais.
**Não inclui automaticamente documentação nem evidências geradas/históricas**: a equipe
deve selecionar as versões corretas e acrescentar objetos `caminho`/`sha256` à lista.
Use caminhos relativos com `/`. Para obter hash de arquivo explicitamente escolhido:
`(Get-FileHash -Algorithm SHA256 'caminho-do-arquivo').Hash.ToLowerInvariant()`.
Não modificar originais. Não selecionar indiscriminadamente pastas de evidências antigas.

Checklist obrigatório de seleção:

- Documentação atual e este fechamento; excluir dados privados e duplicações históricas.
- Prompts/saídas/matriz do experimento Gemini real e ficha humana RF02, com limites conhecidos.
- JSON/minuta/PDF de texto e decisões da coorte humana final, referência e hash.
- STT bruto/revisado, comparação e metadados; 3/6 não vira aprovação por estar no pacote.
- WAV real aprovado e vínculo/hash; ouvir antes do envio.
- OCR oficial e sintético claramente separados, referências, resultados/pendências.
- Arte original IA, composição RF10 e proveniência/revisão: a pasta privada de teste
  não pode entrar. Criar cópia de avaliação sanitizada fora dela, identificando omissões
  e vínculo; não converter derivada em aprovação original. Seleção/anonimização humana.
- Política/registro de IA e responsáveis; não assinar pelo grupo automaticamente.

Inspecionar conteúdo de cada item e então preencher `responsavel_revisao` e
`revisao_privacidade_concluida: true`. Esses campos são declaração da equipe, não
autenticação. Para testes de segurança contendo padrões fictícios de segredo/SID,
o empacotador exige `justificativa_fixture_sintetica` no item; só é aceito em
`testes/*.py`. Escrever por que se trata de fixture e conferir o arquivo inteiro.
Isso nunca permite incluir um valor de credencial atual detectado.

```powershell
# Somente após a revisão efetiva; saída nova, sem sobrescrever ZIP anterior:
.\.venv\Scripts\python.exe -m ferramentas.fechar_entrega zip .entrega-local/manifesto.json --saida .entrega-local/ficdev-final.zip
```

O script bloqueia caminhos externos, links/junções, caches/privado, arquivos de chave,
`.env`, hashes divergentes, duplicação Windows e padrões reconhecidos de segredos.
Lê os valores locais apenas para comparação privada, sem imprimir. Cria inventário
de hashes dos bytes efetivamente arquivados e testa o CRC do ZIP. Não certifica
ausência de todos os dados pessoais, autenticidade humana, cumprimento integral do
enunciado ou legibilidade dos binários: a revisão da seleção é obrigatória.

Depois, extrair em diretório novo; verificar hashes e executar `maquina_limpa.md`.
Guardar manifesto privado e resultado do ensaio. Nenhum ZIP final foi criado nesta
fase: faltam seleção/decisões humanas e revisão de privacidade. `.entrega-local/`
está ignorada pelo Git; isso não substitui cuidado ao compartilhar arquivos.
