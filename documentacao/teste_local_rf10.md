RF10: teste local controlado (Windows)
====================================

Exclusivo para desenvolvimento. Não substitui autenticação real da equipe.
As rotas administrativas normais permanecem bloqueadas. Não há servidor novo,
override de autenticação, aprovação ou publicação automática.

Desativado por padrão; exige ambas as opções:

```powershell
.\.venv\Scripts\python.exe -m testes.validar_rf10_local --modo-local --gerar-uma
```

Requer Cloudflare configurado no `.env` existente. Executa uma tentativa real,
com possível consumo de cota/créditos. A identidade vem de `whoami /user` do
Windows, não de argumentos, formulários ou variáveis de nome de usuário.

Cada execução cria `.rf10-testes-locais/<uuid>/imagens`, `logs` e `decisoes`.
O arquivo `revisao_pendente.json` associa a pendência ao SHA-256 real da imagem,
à geração e à identidade local. Não representa aprovação nem concede permissão
`rf10:revisar`. Esses artefatos não autorizam publicação nas rotas normais.

Para agora, o executor termina em pendente: não oferece comando de aprovação.
Qualquer futura decisão humana deve conferir novamente o hash e permanecer
isolada dos registros de produção. A publicação normal continua dependendo da
integração real de autenticação da equipe. Não compartilhe logs com identidade
local sem revisão. A pasta de teste é ignorada pelo Git e bloqueada em /arquivos.
