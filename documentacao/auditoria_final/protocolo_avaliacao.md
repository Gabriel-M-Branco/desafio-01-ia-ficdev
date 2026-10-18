# Protocolo de qualidade — sem aprovação automática

1. Definir caso fictício, fonte, finalidade e referência **antes** da execução.
   Guardar versão/hash do gabarito. Não usar o gabarito para produzir ou escolher a saída.
2. Separar sucesso técnico (arquivo/JSON/áudio produzido) de fidelidade e aprovação.
3. Fidelidade textual: comparar dados disponíveis; ausências coincidentes são pendências,
   não acertos nem divergências. Informação inventada é divergência. Omissão de um dado
   presente na fonte reduz completude e fidelidade, mesmo sem entrar na contagem vermelha.
4. STT: conferir nome, protocolo e datas ouvindo a fonte; taxa 3/6 não autoriza minuta
   sem conferência. Conservar bruto, revisado, erro por entidade e decisão por hash.
5. OCR: conferir cada campo no original. Oficial 0/23 e sintético 22/23 são cenários
   distintos. Não transformar rótulo/assinatura em dado confirmado. Ilegível permanece pendente.
6. Classificar gravidade: **crítica** = identidade/protocolo/data/lei/prazo inventado,
   vazamento, uso sem aprovação ou hash alterado; **alta** = dado disponível omitido,
   pedido alterado, documento sem corpo; **média** = ambiguidade/linguagem inadequada;
   **baixa** = apresentação sem mudança de sentido. Ausência real = pendência informativa,
   salvo se impedir uma decisão necessária, quando bloqueia a finalização.
7. Linguagem: o revisor verifica clareza, português, respeito, formalidade, resposta ao
   pedido e ausência de obrigação legal/documental sem fonte. Não atribuir pontuação automática
   como se fosse parecer humano. Registrar observação e justificativa.
8. Segurança: testar injeção, JSON inválido, arquivo inválido, erros de provedor,
   credenciais e publicação por hash. Testes com mocks comprovam controle, não qualidade do modelo.
9. Decisão: corrigir com fonte quando houver erro recuperável; pedir nova geração
   explicitamente se estrutura/linguagem inviáveis; rejeitar quando houver invenção crítica,
   fonte não verificável ou impossibilidade de revisão. Correção não equivale a aprovação.
10. Aprovar somente o texto/PNG exato após conferência. Editar invalida a aprovação.
    Aprovação da transcrição/OCR não aprova a minuta para TTS. Não publicar automaticamente.
11. Taxa: aprovados / (aprovados + corrigidos + rejeitados), com coorte e data definidas;
    pendentes e eventos TTS excluídos. `/api/qualidade/revisoes` informa contagens da trilha,
    que pode conter testes antigos; não é benchmark de acurácia nem taxa de coorte real controlada.
12. Para RF13, demonstrar uma aprovação e uma rejeição/correção **humanas reais** de
    casos fictícios, com justificativas. Os testes criam decisões fictícias em pastas temporárias;
    elas não contam como deliberação real da equipe.

Ficha mínima a preencher: ID e hash; esperado/obtido; fidelidade, completude, formato,
linguagem e segurança; erros e gravidade; decisão/justificativa; responsável; data;
tempo até resultado utilizável. Campos em branco são **NÃO COMPROVADOS**, não aprovação.

Históricos anteriores não foram reescritos. Sem uma amostra selecionada e conferida,
não divulgar uma “taxa geral de aprovação” como avaliação do sistema atual.
