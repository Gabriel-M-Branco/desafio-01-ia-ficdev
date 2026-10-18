// Central Inteligente de Atendimento - GOV.MT (Frontend Controller)

document.addEventListener("DOMContentLoaded", () => {
  const esc = (valor) => String(valor ?? "").replace(/[&<>"']/g, c =>
    ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[c]));
  let ultimaExecucaoId = null;
  let ultimoUrlPdf = null;
  let ultimaExtracao = {};
  let textoAprovado = null;
  let processando = false;
  let decidindo = false;
  let sintetizando = false;
  let exportando = false;
  let carregandoCaso = false;
  let idOrigem = null;
  let textoOrigemConfirmado = null;
  let confirmandoOrigem = false;
  let formatoVisual = "original";
  let conferenciaAtual = null;

  // Apenas apresentação: não altera extração, minuta, métricas ou aprovação.
  function apresentarIdentificador(campo, valor) {
    const texto = String(valor ?? "");
    if (campo !== "cpf" && campo !== "rg") return texto;
    if (!/^[\d.\s-]+$/.test(texto)) return texto;
    const digitos = texto.replace(/\D/g, "");
    if (formatoVisual === "digitos") return digitos;
    if (formatoVisual === "mascara" && campo === "cpf" && digitos.length === 11)
      return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
    return texto;
  }
  for (const [id, formato] of [["btn-aplicar-mascaras-todas", "mascara"], ["btn-aplicar-digitos-todas", "digitos"]]) {
    document.getElementById(id)?.addEventListener("click", () => {
      formatoVisual = formato;
      if (conferenciaAtual) renderizarPainelConferencia(...conferenciaAtual);
    });
  }

  function mensagemSegura(data, status) {
    let detalhe = data?.detail ?? data?.erro;
    if (Array.isArray(detalhe)) detalhe = detalhe.map(e => `${(e.loc || []).join(".")}: ${e.msg || "Valor inválido"}`).join("; ");
    if (typeof detalhe !== "string") detalhe = "Não foi possível concluir a operação.";
    if (status >= 500 && status !== 502 && status !== 503) detalhe = "Falha interna. Consulte a auditoria local.";
    return detalhe.replace(/Bearer\s+\S+|(?:sk-or-v1-|hf_)[A-Za-z0-9_-]+/gi, "[credencial omitida]").slice(0, 400);
  }

  async function api(url, opcoes) {
    let res;
    try { res = await fetch(url, opcoes); }
    catch (_) { throw new Error("Não foi possível conectar à API local. Verifique se o servidor está ativo."); }
    let data;
    try { data = await res.json(); }
    catch (_) { throw new Error(`HTTP ${res.status || "?"}: a API não retornou JSON válido.`); }
    if (!res.ok || data?.sucesso === false) {
      throw new Error(`HTTP ${res.status || 200}: ${mensagemSegura(data, res.status)}`);
    }
    return { ...res, ok: true, json: async () => data };
  }

  function atualizarAcoes() {
    const ocupado = processando || decidindo || sintetizando || exportando || carregandoCaso || confirmandoOrigem;
    for (const id of ["btn-aprovar-minuta", "btn-corrigir-minuta", "btn-rejeitar-minuta", "btn-exportar-pdf"]) {
      const btn = document.getElementById(id);
      if (btn) btn.disabled = ocupado || !ultimaExecucaoId;
    }
    const tts = document.getElementById("btn-gerar-tts");
    if (tts) tts.disabled = ocupado || !ultimaExecucaoId || textoAprovado === null || textoAprovado !== document.getElementById("editor-minuta")?.value;
    for (const id of ["caso-predefinido", "input-texto-solicitacao", "btn-limpar-texto", "btn-processar-solicitacao", "editor-minuta"]) {
      const elemento = document.getElementById(id);
      if (elemento) elemento.disabled = ocupado;
    }
    const multimodal = ["audio_transcricao", "visao_documento"].includes(document.getElementById("caso-predefinido")?.value);
    const textoFonte = document.getElementById("input-texto-solicitacao")?.value.trim();
    const processar = document.getElementById("btn-processar-solicitacao");
    if (processar && multimodal) processar.disabled = ocupado || !idOrigem || textoOrigemConfirmado !== textoFonte;
    const confirmar = document.getElementById("btn-confirmar-origem");
    if (confirmar) confirmar.disabled = ocupado || !idOrigem || !textoFonte;
    const rejeitarOrigem = document.getElementById("btn-rejeitar-origem");
    if (rejeitarOrigem) rejeitarOrigem.disabled = ocupado || !idOrigem;
  }
  document.getElementById("editor-minuta")?.addEventListener("input", () => {
    if (textoAprovado !== null && textoAprovado !== document.getElementById("editor-minuta").value) {
      textoAprovado = null;
      document.getElementById("badge-status-revisao").textContent = "Texto alterado: nova aprovação necessária";
      document.getElementById("badge-status-revisao").className = "badge badge-warning";
    }
    document.getElementById("tts-audio-container").style.display = "none";
    atualizarAcoes();
  });
  atualizarAcoes();


  // 1. Gerenciamento de Abas Principais
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");

  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");
      navTabs.forEach((t) => t.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");

      if (targetId === "tab-auditoria") {
        carregarAuditoriaELgpd();
      }
    });
  });

  // 2. Sub-abas (Minuta vs JSON vs Métricas)
  const subTabs = document.querySelectorAll(".sub-tab");
  const subtabPanes = document.querySelectorAll(".subtab-pane");

  subTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-subtab");
      subTabs.forEach((t) => t.classList.remove("active"));
      subtabPanes.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const targetSub = document.getElementById(targetId);
      if (targetSub) targetSub.classList.add("active");
    });
  });

  // 3. Inicialização e Consulta de Configuração
  async function carregarConfiguracao() {
    try {
      const res = await api("/api/config");
      const data = await res.json();
      const badgeMode = document.getElementById("badge-api-mode");
      if (badgeMode) {
        badgeMode.textContent = data.texto ? `Texto: ${data.texto.provedor} / ${data.texto.modelo}${data.texto.habilitado ? "" : " (desativado)"}` : "Configuração de texto indisponível";
        const modos = document.getElementById("modos-multimodais");
        if (modos) modos.textContent = `STT: ${data.stt?.provedor || "não informado"} / ${data.stt?.modelo || "não informado"} · TTS: ${data.tts?.provedor || "não informado"} · OCR local · RF10 administrativo bloqueado`;
        const imagem = document.getElementById("btn-gerar-imagem-peca");
        if (imagem) { imagem.disabled = data.rf10_administrativo_habilitado !== true; imagem.title = "Requer autenticação real da equipe; use o executor local controlado para testes."; }
      }
    } catch (e) {
      document.getElementById("badge-api-mode").textContent = "Configuração indisponível";
    }
  }
  carregarConfiguracao();

  // 4. Carregamento de Casos de Teste Pré-definidos
  const selectCaso = document.getElementById("caso-predefinido");
  const inputTexto = document.getElementById("input-texto-solicitacao");

  async function atualizarTextoCaso(valor) {
    idOrigem = null; textoOrigemConfirmado = null;
    const blocoOrigem = document.getElementById("revisao-origem");
    if (blocoOrigem) blocoOrigem.style.display = ["audio_transcricao", "visao_documento"].includes(valor) ? "block" : "none";
    if (!valor || valor === "personalizado") {
      inputTexto.value = "";
      atualizarAcoes();
      return;
    }
    carregandoCaso = true; atualizarAcoes();
    inputTexto.value = "Carregando conteúdo real da modalidade selecionada...";
    try {
      const res = await api(`/api/casos/${valor}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.erro || data.detail || "Processamento indisponível");
      inputTexto.value = data.conteudo || "";
      idOrigem = data.id_execucao_origem || null;
      const status = document.getElementById("status-revisao-origem");
      if (status) status.textContent = "Revisão humana pendente";
    } catch (e) {
      console.error("Erro ao carregar caso:", e);
      inputTexto.value = "";
      alert("Falha ao carregar a modalidade: " + e.message);
    } finally {
      carregandoCaso = false; atualizarAcoes();
    }
  }

  inputTexto?.addEventListener("input", () => {
    if (["texto_original", "prompt_injection"].includes(selectCaso?.value)) {
      selectCaso.value = "personalizado"; // Texto editado não é mais o caso controlado do gabarito.
    }
    textoOrigemConfirmado = null;
    const status = document.getElementById("status-revisao-origem");
    if (status) status.textContent = "Texto alterado; confirme novamente na fonte";
    atualizarAcoes();
  });
  document.getElementById("btn-confirmar-origem")?.addEventListener("click", async () => {
    if (!idOrigem || !inputTexto.value.trim()) return;
    const justificativa = window.prompt("Registre: 1) campos conferidos na fonte; 2) correções feitas; 3) campos ausentes/ilegíveis e impacto. Confira nomes, protocolo, datas, curso, carga horária e turno. Se dados críticos continuarem duvidosos, cancele e rejeite a leitura; não confirme por suposição.");
    if (!justificativa?.trim()) return;
    const texto = inputTexto.value.trim();
    confirmandoOrigem = true; atualizarAcoes();
    try {
      await api("/api/revisao/decisao", {method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({id_execucao:idOrigem, decisao:"APROVADO", justificativa, texto_final:texto})});
      textoOrigemConfirmado = texto;
      document.getElementById("status-revisao-origem").textContent = "Conferência humana registrada para este texto";
    } catch (e) { alert(e.message); }
    finally { confirmandoOrigem = false; atualizarAcoes(); }
  });

  document.getElementById("btn-rejeitar-origem")?.addEventListener("click", async () => {
    if (!idOrigem) return;
    const justificativa = window.prompt("Explique por que a leitura não é confiável, quais campos não puderam ser conferidos e qual ação é necessária. A rejeição não altera o original nem autoriza minuta.");
    if (!justificativa?.trim()) return;
    textoOrigemConfirmado = null;
    confirmandoOrigem = true; atualizarAcoes();
    try {
      await api("/api/revisao/decisao", {method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({id_execucao:idOrigem, decisao:"REJEITADO", justificativa, texto_final:inputTexto.value.trim()})});
      document.getElementById("status-revisao-origem").textContent = "Leitura rejeitada; geração de minuta bloqueada até nova conferência";
    } catch (e) { alert(e.message); }
    finally { confirmandoOrigem = false; atualizarAcoes(); }
  });

  if (selectCaso) {
    selectCaso.addEventListener("change", (e) => atualizarTextoCaso(e.target.value));
    atualizarTextoCaso(selectCaso.value);
  }

  document.getElementById("btn-limpar-texto")?.addEventListener("click", () => {
    if (inputTexto) inputTexto.value = "";
  });

  // 5. Processar Solicitação com IA Segura (RF03, RF05, RF09)
  const btnProcessar = document.getElementById("btn-processar-solicitacao");
  btnProcessar?.addEventListener("click", async () => {
    const texto = inputTexto?.value.trim();
    if (!texto) {
      alert("Por favor, insira ou carregue o texto de uma solicitação.");
      return;
    }

    processando = true;
    ultimaExecucaoId = null; ultimoUrlPdf = null; ultimaExtracao = {}; textoAprovado = null;
    document.getElementById("editor-minuta").value = "";
    document.getElementById("justificativa-revisao").value = "";
    document.getElementById("json-extracao-view").textContent = "Aguardando processamento...";
    document.getElementById("tabela-conferencia-body").innerHTML = "";
    for (const id of ["metric-duracao", "metric-tokens", "metric-custo"]) document.getElementById(id).textContent = "—";
    document.getElementById("tts-audio-container").style.display = "none";
    document.getElementById("badge-status-revisao").textContent = "Processando; revisão indisponível";
    document.getElementById("badge-status-revisao").className = "badge badge-warning";
    document.getElementById("comparacao-gabarito-view").textContent = "";
    document.getElementById("banner-conferencia-operador").style.display = "none";
    atualizarAcoes();
    btnProcessar.disabled = true;
    btnProcessar.textContent = "Analisando solicitação e gerando minuta...";

    try {
      const res = await api("/api/processar/texto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: texto, caso: selectCaso?.value || "texto_original", id_execucao_origem: idOrigem }),
      });

      const data = await res.json();
      btnProcessar.disabled = false;
      btnProcessar.textContent = "Processar Solicitação (RF03/RF05)";

      if (!data.sucesso) {
        alert("Erro no processamento: " + (data.detail || data.erro || "Resposta incompleta da API"));
        return;
      }

      if (!data.id_execucao || typeof data.minuta_institucional !== "string") throw new Error("Resposta incompleta da API: execução ou minuta ausente.");
      ultimaExecucaoId = data.id_execucao;
      ultimaExtracao = data.extracao || {};
      ultimoUrlPdf = data.url_pdf || null;

      // Atualiza Minuta
      const editorMinuta = document.getElementById("editor-minuta");
      if (editorMinuta) editorMinuta.value = data.minuta_institucional || "";

      // Atualiza JSON Viewer
      const jsonView = document.getElementById("json-extracao-view");
      if (jsonView) jsonView.textContent = JSON.stringify(data.extracao, null, 2);

      // Atualiza Metricas
      document.getElementById("metric-duracao").textContent = `${data.metricas?.duracao_segundos}s`;
      document.getElementById("metric-tokens").textContent = data.metricas?.total_tokens || "-";
      document.getElementById("metric-custo").textContent = typeof data.metricas?.custo_usd === "number" ? `US$ ${data.metricas?.custo_usd.toFixed(2)}` : "Não informado";

      const badgeStatus = document.getElementById("badge-status-revisao");
      if (badgeStatus) {
        badgeStatus.textContent = "Pendente de Revisão Humana";
        badgeStatus.className = "badge badge-warning";
      }

      // 5. Renderiza o Painel de Conferência Visual de Dados e Auditoria (RF13)
      renderizarPainelConferencia(data.avaliacao_gabarito || data.conformidade_formato, data.extracao);

      // Exibe avaliacao resumida na aba de métricas
      const gabaritoBox = document.getElementById("comparacao-gabarito-view");
      if (gabaritoBox && !data.avaliacao_gabarito) {
        gabaritoBox.textContent = data.referencia_avaliacao || "Fidelidade não avaliada; somente formato conferido.";
        const origem = data.avaliacao_origem;
        if (origem) gabaritoBox.textContent += " Comparação da origem: " +
          (origem.acuracia_entidades || origem.taxa_acuracia_percentual || "consultar auditoria") +
          ". Essa pontuação não valida a minuta.";
      }
      if (gabaritoBox && data.avaliacao_gabarito) {
        const aval = data.avaliacao_gabarito;
        gabaritoBox.innerHTML = `
          <strong>Fidelidade à referência institucional:</strong> ${aval.taxa_fidelidade_percentual ?? "não avaliada"}${aval.taxa_fidelidade_percentual == null ? "" : "%"} (${aval.total_acertos}/${aval.total_campos_avaliaveis ?? aval.total_campos_analisados} campos avaliáveis)<br>
          <strong>Completude dos dados disponíveis na fonte:</strong> ${aval.taxa_completude_percentual ?? "não avaliada"}${aval.taxa_completude_percentual == null ? "" : "%"}<br>
          <small>Ausências na fonte: ${aval.total_ausentes_na_fonte ?? "não informado"}. Ausências coincidentes não contam como acertos nem divergências.</small><br>
          <strong>Status de Qualidade:</strong> <span class="badge ${aval.status_qualidade === 'Excelente' ? 'badge-ok' : 'badge-warning'}">${esc(aval.status_qualidade)}</span>
        `;
      }
    } catch (err) {
      btnProcessar.disabled = false;
      btnProcessar.textContent = "Processar Solicitação (RF03/RF05)";
      document.getElementById("badge-status-revisao").textContent = "Processamento não concluído";
      alert("Erro no processamento: " + err.message);
    } finally {
      processando = false;
      atualizarAcoes();
    }
  });

  // Função Especializada para o Painel de Conferência de Dados (RF13)
  function renderizarPainelConferencia(aval, extracao) {
    conferenciaAtual = [aval, extracao];
    if (!aval) return;

    const banner = document.getElementById("banner-conferencia-operador");
    const badgeCount = document.getElementById("badge-divergencias-count");
    const taxaEl = document.getElementById("audit-taxa-fidelidade");
    const statusEl = document.getElementById("audit-status-qualidade");
    const acertosEl = document.getElementById("audit-campos-acertos");
    const errosEl = document.getElementById("audit-campos-erros");
    const subErrosEl = document.getElementById("audit-sub-erros");
    const pendenciasEl = document.getElementById("audit-campos-pendencias");
    const tbody = document.getElementById("tabela-conferencia-body");

    const erros = (aval.erros_encontrados || []).filter(c => c.status !== "PENDENCIA" && !c.eh_pendencia);
    const comparativo = aval.comparativo_campos || [];
    const pendencias = comparativo.filter((c) => c.eh_pendencia || c.status === "PENDENCIA");

    // 1. Atualiza Indicadores KPI
    if (taxaEl) taxaEl.textContent = `${aval.taxa_fidelidade_percentual ?? "não avaliada"}${aval.taxa_fidelidade_percentual == null ? "" : "%"}`;
    if (statusEl) {
      statusEl.textContent = aval.status_qualidade || "Formato avaliado; fidelidade não avaliada";
      statusEl.className = `badge ${aval.status_qualidade === "Excelente" ? "badge-ok" : "badge-warning"}`;
    }
    if (acertosEl) acertosEl.textContent = `${aval.total_acertos ?? "—"} / ${aval.total_campos_avaliaveis ?? aval.total_campos_analisados ?? "—"}`;
    if (errosEl) errosEl.textContent = erros.length;
    if (subErrosEl) {
      subErrosEl.textContent = erros.length === 0 ? "Nenhuma divergência" : `${erros.length} campo(s) exigem atenção`;
    }
    if (pendenciasEl) pendenciasEl.textContent = pendencias.length;

    // 2. Atualiza Bolinha de Notificação na Aba
    if (badgeCount) {
      if (erros.length > 0) {
        badgeCount.style.display = "inline-flex";
        badgeCount.textContent = `${erros.length}`;
        badgeCount.className = "badge-count-circle";
      } else {
        badgeCount.style.display = "none";
      }
    }

    // 3. Atualiza Banner Rápido na Minuta
    if (banner) {
      banner.style.display = "flex";
      if (erros.length > 0) {
        banner.className = "conferencia-banner divergente";
        banner.innerHTML = `
          <div>
            <strong>Atenção Servidor:</strong> Foram identificadas <strong>${erros.length} divergência(s)</strong> em relação aos padrões e regras oficiais:
            <div class="banner-badge-group">
              ${erros.map((e) => `<span class="badge badge-danger">${esc(e.rotulo || e.campo || "Campo")}: esperado "${esc(e.esperado)}", obtido "${esc(e.obtido)}"</span>`).join("")}
            </div>
          </div>
          <button type="button" class="banner-action-btn" id="btn-ir-conferencia">Abrir Painel de Conferência &rarr;</button>
        `;
        document.getElementById("btn-ir-conferencia")?.addEventListener("click", () => {
          document.getElementById("btn-subtab-conferencia")?.click();
        });
      } else if (pendencias.length > 0) {
        banner.className = "conferencia-banner alerta";
        banner.innerHTML = `
          <div>
            <strong>Conferência com pendências:</strong> ${aval.total_acertos}/${aval.total_campos_avaliaveis ?? aval.total_campos_analisados} campos avaliáveis conferidos. Há ${pendencias.length} dados pendentes; ausência na fonte não representa divergência:
            <div class="banner-badge-group">
              ${pendencias.map((p) => `<span class="badge badge-warning">${esc(p.rotulo || p.campo)}: Pendente</span>`).join("")}
            </div>
          </div>
          <button type="button" class="banner-action-btn" id="btn-ir-conferencia">Ver Tabela Completa &rarr;</button>
        `;
        document.getElementById("btn-ir-conferencia")?.addEventListener("click", () => {
          document.getElementById("btn-subtab-conferencia")?.click();
        });
      } else {
        banner.className = "conferencia-banner sucesso";
        banner.innerHTML = `
          <div>
            <strong>Conferência Concluída com Sucesso:</strong> Conferência automática concluída. Revise a tabela e a fonte; formato não comprova fidelidade nem aprovação.
          </div>
          <button type="button" class="banner-action-btn" id="btn-ir-conferencia">Ver Tabela Completa &rarr;</button>
        `;
        document.getElementById("btn-ir-conferencia")?.addEventListener("click", () => {
          document.getElementById("btn-subtab-conferencia")?.click();
        });
      }
    }

    // 4. Renderiza Tabela Campo a Campo (com fallback defensivo)
    if (tbody) {
      const ROTULOS_MAP = {
        protocolo: "Número de Protocolo",
        data: "Data da Solicitação",
        solicitante: "Nome do Requerente / Solicitante",
        cpf: "Cadastro de Pessoa Física (CPF)",
        rg: "Registro Geral (RG)",
        orgao_expedidor: "Órgão Expedidor do RG",
        data_nascimento: "Data de Nascimento",
        naturalidade: "Naturalidade / Cidade",
        uf: "Unidade Federativa (UF)",
        nome_mae: "Nome da Mãe (Filiação)",
        nome_pai: "Nome do Pai (Filiação)",
        curso: "Curso Técnico Pretendido",
        eixo_tecnologico: "Eixo Tecnológico",
        carga_horaria: "Carga Horária do Curso",
        turno: "Turno Solicitado",
        inicio_curso: "Previsão de Início das Aulas",
        email: "E-mail de Contato",
        telefone: "Telefone / Celular",
        assunto: "Assunto da Manifestação",
        pedido: "Teor do Pedido Formal",
        categoria: "Categoria do Atendimento",
      };

      let comparativo = aval.comparativo_campos || [];
      if (comparativo.length === 0 && extracao) {
        const mapaErros = {};
        erros.forEach((e) => { mapaErros[e.campo] = e; });
        comparativo = Object.keys(extracao).map((k) => {
          const val = extracao[k];
          const erro = mapaErros[k];
          const isPend = String(val).toLowerCase() === "não localizado";
          return {
            campo: k,
            rotulo: ROTULOS_MAP[k] || k,
            esperado: erro ? erro.esperado : (isPend ? "não localizado" : val),
            obtido: val,
            status: erro ? "DIVERGENTE" : (isPend ? "PENDENCIA" : "NAO_AVALIADO"),
            eh_pendencia: isPend,
            gravidade: erro ? erro.gravidade : "Nenhuma",
            acao_recomendada: erro ? erro.acao_recomendada : "Conferir na fonte; sem referência independente.",
          };
        });
      }

      if (comparativo.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: #64748B;">Nenhum detalhe comparativo disponível para esta extração.</td></tr>`;
        return;
      }

      const linhasHtml = comparativo
        .map((item, idx) => {
          const isDivergente = item.status === "DIVERGENTE";
          const isPendencia = item.eh_pendencia || item.status === "PENDENCIA";
          const rowClass = isDivergente ? "row-divergente" : isPendencia || item.status !== "CORRETO" ? "row-pendencia" : "row-correto";

          let extraidoHtml = "";
          let statusBadge = "";
          let acaoHtml = "";

          const FORMATOS_MAP = {
            protocolo: "Ano-Sequencial (ex: 2026-000142)",
            data: "Padrão DD/MM/AAAA",
            solicitante: "Nome Completo (Mínimo 2 palavras)",
            cpf: "Padrão Nacional (000.000.000-00)",
            rg: "Numérico com dígito (0000000-0)",
            orgao_expedidor: "Sigla Oficial (ex: SSP, DETRAN)",
            data_nascimento: "Padrão DD/MM/AAAA",
            naturalidade: "Município / Cidade",
            uf: "Sigla da UF (2 letras)",
            nome_mae: "Nome Completo da Mãe",
            nome_pai: "Nome do Pai ou 'não localizado'",
            curso: "Denominação Institucional do Curso",
            eixo_tecnologico: "Eixo Institucional Oficial",
            carga_horaria: "Carga Horária (ex: 1200 horas)",
            turno: "Matutino / Vespertino / Noturno",
            inicio_curso: "Padrão DD/MM/AAAA",
            email: "Endereço válido (nome@dominio.ext)",
            telefone: "DDD + Número de Contato",
            assunto: "Tema principal da manifestação",
            pedido: "Teor da solicitação expressa",
            categoria: "Categoria de atendimento oficial",
          };

          const formatoTexto = FORMATOS_MAP[item.campo] ? `<span class="formato-hint">Formato: ${FORMATOS_MAP[item.campo]}</span>` : "";

          if (isDivergente) {
            extraidoHtml = `<span class="val-extraido-erro" id="val-extraido-${idx}">${esc(apresentarIdentificador(item.campo, item.obtido || "Vazio"))}</span>`;
            statusBadge = `<span class="diag-tag diag-divergente">▲ Divergente</span>`;
            acaoHtml = `<button type="button" class="btn-corrigir-inline" data-idx="${idx}" data-campo="${esc(item.campo)}" data-esperado="${esc(item.esperado)}" data-obtido="${esc(item.obtido)}">Aplicar Correção</button>`;
          } else if (isPendencia) {
            extraidoHtml = `<span class="val-pendencia-destaque">não localizado</span>`;
            statusBadge = `<span class="diag-tag diag-pendente">○ Pendência</span>`;
            acaoHtml = `<span style="color:#64748B; font-size:0.75rem;">Dado pendente; conferir na fonte</span>`;
          } else if (item.status !== "CORRETO") {
            extraidoHtml = `<strong>${esc(apresentarIdentificador(item.campo, item.obtido))}</strong>`;
            statusBadge = '<span class="diag-tag diag-pendente">Não conferido com referência</span>';
            acaoHtml = '<span>Revisar na fonte</span>';
          } else {
            extraidoHtml = `<strong>${esc(apresentarIdentificador(item.campo, item.obtido))}</strong>`;
            statusBadge = `<span class="diag-tag diag-correto">● Conforme</span>`;
            acaoHtml = `<span style="color:#15803D; font-weight:600; font-size:0.75rem;">Conferido</span>`;
          }

          return `
            <tr class="${rowClass}" data-status="${esc(item.status)}">
              <td>
                <strong>${esc(item.rotulo || item.campo)}</strong>
                <br><span style="font-size:0.7rem; color:#64748B; font-family:monospace;">${esc(item.campo)}</span>
              </td>
              <td>${extraidoHtml}</td>
              <td>
                <span class="val-esperado-destaque">${esc(item.esperado)}</span>
                ${formatoTexto}
              </td>
              <td>${statusBadge}</td>
              <td id="acao-col-${idx}">${acaoHtml}</td>
            </tr>
          `;
        })
        .join("");

      tbody.innerHTML = linhasHtml + `<tr id="tr-empty-filter" style="display:none;"><td colspan="5" style="text-align:center; padding: 24px; color: #16A34A; font-weight: 600;"></td></tr>`;

      // Vincula cliques no botão "Aplicar Correção"
      tbody.querySelectorAll(".btn-corrigir-inline").forEach((btn) => {
        btn.addEventListener("click", () => {
          const campo = btn.getAttribute("data-campo");
          const esperado = window.prompt("Informe o valor conferido diretamente na fonte (não copie uma descrição de formato):");
          if (esperado === null || !esperado.trim()) return;
          const obtido = btn.getAttribute("data-obtido");
          const idx = btn.getAttribute("data-idx");

          // Atualiza o editor de minuta
          const editorMinuta = document.getElementById("editor-minuta");
          if (editorMinuta && obtido && esperado) {
            if (editorMinuta.value.includes(obtido)) {
              editorMinuta.value = editorMinuta.value.replaceAll(obtido, esperado);
              textoAprovado = null;
              document.getElementById("badge-status-revisao").textContent = "Correção local: salvar e aprovar novamente";
              document.getElementById("tts-audio-container").style.display = "none";
              atualizarAcoes();
            }
          }

          // Atualiza a visualização do JSON se disponível
          const jsonView = document.getElementById("json-extracao-view");
          if (jsonView && extracao) {
            extracao[campo] = esperado;
            jsonView.textContent = JSON.stringify(extracao, null, 2);
          }

          // Marca o botão como corrigido
          const colAcao = document.getElementById(`acao-col-${idx}`);
          if (colAcao) {
            colAcao.innerHTML = `<span class="btn-corrigido-ok">&#10003; Corrigido</span>`;
          }
          const valCol = document.getElementById(`val-extraido-${idx}`);
          if (valCol) {
            valCol.className = "val-esperado-destaque";
            valCol.textContent = esperado;
          }

          // Preenche justificativa de revisão sugerindo a correção feita
          const justInput = document.getElementById("justificativa-revisao");
          if (justInput) {
            justInput.value = `Correção aplicada no campo ${esc(campo)} para '${esperado}' após conferência humana na fonte; exige nova aprovação.`;
          }
        });
      });
    }
  }

  // Filtros da Tabela de Conferência
  const filterBtns = document.querySelectorAll(".conferencia-filters .btn-filter");
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tipo = btn.getAttribute("data-filter");
      const rows = document.querySelectorAll("#tabela-conferencia-body tr");
      let visiveis = 0;
      rows.forEach((row) => {
        if (row.id === "tr-empty-filter") return;
        let show = false;
        if (tipo === "todos") {
          show = true;
        } else if (tipo === "divergentes") {
          show = row.classList.contains("row-divergente");
        } else if (tipo === "pendencias") {
          show = row.getAttribute("data-status") === "PENDENCIA";
        }
        row.style.display = show ? "" : "none";
        if (show) visiveis++;
      });

      const emptyRow = document.getElementById("tr-empty-filter");
      if (emptyRow) {
        if (visiveis === 0) {
          emptyRow.style.display = "";
          emptyRow.querySelector("td").textContent =
            tipo === "divergentes"
              ? "Nenhuma divergência neste filtro. Confira também pendências e campos não avaliados."
              : tipo === "pendencias"
              ? "Nenhuma pendência documental registrada."
              : "Nenhum campo para exibir.";
        } else {
          emptyRow.style.display = "none";
        }
      }
    });
  });

  // 5.1 Exportar / Visualizar Minuta em PDF Oficial
  const btnExportarPdf = document.getElementById("btn-exportar-pdf");
  btnExportarPdf?.addEventListener("click", async () => {
    const textoMinuta = document.getElementById("editor-minuta")?.value.trim();
    if (!textoMinuta) {
      alert("Nenhuma minuta disponível para exportação em PDF.");
      return;
    }

    if (!ultimaExecucaoId) { alert("Processe uma solicitação antes de exportar."); return; }
    exportando = true; atualizarAcoes();
    btnExportarPdf.disabled = true;
    btnExportarPdf.textContent = "Gerando PDF Oficial Timbrado...";

    try {
      const res = await api("/api/minuta/gerar_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          texto_minuta: textoMinuta,
          protocolo: ultimaExtracao.protocolo || "não localizado",
          solicitante: ultimaExtracao.solicitante || "não localizado",
          categoria: ultimaExtracao.categoria || "não localizado",
          nome_arquivo: `minuta_oficial_${new Date().getTime()}.pdf`,
          id_execucao: ultimaExecucaoId,
        }),
      });

      const data = await res.json();
      btnExportarPdf.disabled = false;
      btnExportarPdf.textContent = "Visualizar / Baixar Minuta em PDF Oficial";

      if (data.sucesso && data.url_pdf) {
        window.open(data.url_pdf, "_blank");
      } else {
        alert("Erro ao gerar PDF: " + (data.detail || data.erro || "Resposta incompleta da API"));
      }
    } catch (e) {
      btnExportarPdf.disabled = false;
      btnExportarPdf.textContent = "Visualizar / Baixar Minuta em PDF Oficial";
      alert("Erro ao conectar com o gerador de PDF: " + e.message);
    } finally { exportando = false; atualizarAcoes(); }
  });

  // 6. Síntese de Voz TTS da Minuta Aprovada/Editada (RF07)
  const btnTts = document.getElementById("btn-gerar-tts");
  btnTts?.addEventListener("click", async () => {
    const textoMinuta = document.getElementById("editor-minuta")?.value || "";
    if (!textoMinuta.trim()) {
      alert("Nenhuma minuta disponível para síntese de voz.");
      return;
    }

    if (!ultimaExecucaoId || textoAprovado !== textoMinuta) {
      alert("Aprove o texto atual antes de gerar o áudio."); return;
    }
    sintetizando = true; atualizarAcoes();
    btnTts.disabled = true;
    btnTts.textContent = "Sintetizando áudio aprovado...";

    try {
      const res = await api("/api/sintetizar/audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: textoMinuta, id_execucao: ultimaExecucaoId }),
      });

      const data = await res.json();
      btnTts.disabled = false;
      btnTts.textContent = "Gerar Áudio Acessivel (RF07)";

      if (data.sucesso) {
        const audioContainer = document.getElementById("tts-audio-container");
        const audioPlayer = document.getElementById("tts-audio-player");
        if (audioContainer && audioPlayer) {
          audioContainer.style.display = "flex";
          audioPlayer.src = data.url_audio + "?t=" + new Date().getTime();
          audioPlayer.play()?.catch(() => {});
        }
      } else {
        alert("Erro na síntese: " + (data.detail || data.erro || "Falha na geração de áudio"));
      }
    } catch (e) {
      btnTts.disabled = false;
      btnTts.textContent = "Gerar Áudio Acessivel (RF07)";
      alert("Erro: " + e.message);
    } finally {
      sintetizando = false; atualizarAcoes();
    }
  });

  // 7. Human-in-the-Loop: Decisão do Servidor (RF13)
  async function registrarDecisao(decisao) {
    if (!ultimaExecucaoId) {
      alert("Processe uma solicitação antes de submeter a decisão de revisão.");
      return;
    }

    const justificativa = document.getElementById("justificativa-revisao")?.value.trim();
    if (!justificativa) {
      alert("Por favor, preencha o campo de justificativa da sua decisão para registro de auditoria.");
      return;
    }

    const textoAtualizado = document.getElementById("editor-minuta")?.value;
    const execucao = ultimaExecucaoId;
    if (decidindo || processando || sintetizando) return;
    decidindo = true; atualizarAcoes();
    try {
      const res = await api("/api/revisao/decisao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_execucao: execucao,
          decisao: decisao,
          justificativa: justificativa,
          texto_final: textoAtualizado,
        }),
      });

      const data = await res.json();
      if (data.sucesso) {
        textoAprovado = decisao === "APROVADO" ? textoAtualizado : null;
        document.getElementById("tts-audio-container").style.display = "none";
        const badgeStatus = document.getElementById("badge-status-revisao");
        if (badgeStatus) {
          badgeStatus.textContent = `Status: ${decisao}`;
          badgeStatus.className = decisao === "APROVADO" ? "badge badge-ok" : decisao === "CORRIGIDO" ? "badge badge-warning" : "badge badge-danger";
        }
        alert(`Decisão registrada com sucesso no log de auditoria: [${decisao}]`);
      }
    } catch (e) {
      alert("Falha ao registrar decisão: " + e.message);
    } finally {
      decidindo = false; atualizarAcoes();
    }
  }

  document.getElementById("btn-aprovar-minuta")?.addEventListener("click", () => registrarDecisao("APROVADO"));
  document.getElementById("btn-corrigir-minuta")?.addEventListener("click", () => registrarDecisao("CORRIGIDO"));
  document.getElementById("btn-rejeitar-minuta")?.addEventListener("click", () => registrarDecisao("REJEITADO"));

  // 8. Experimento dos 3 Prompts (RF02)
  const btnExp = document.getElementById("btn-rodar-experimento");
  btnExp?.addEventListener("click", async () => {
    btnExp.disabled = true;
    btnExp.textContent = "Executando experimento controlado...";

    try {
      const res = await api("/api/experimento/prompts", { method: "POST" });
      const data = await res.json();
      btnExp.disabled = false;
      btnExp.textContent = "Executar Experimento de Prompts";

      if (data.sucesso) {
        document.getElementById("exp-tempo-a").textContent = `${data.resultados.prompt_a.duracao_segundos}s`;
        document.getElementById("exp-tempo-b").textContent = `${data.resultados.prompt_b.duracao_segundos}s`;
        document.getElementById("exp-tempo-c").textContent = `${data.resultados.prompt_c.duracao_segundos}s`;

        document.getElementById("exp-out-a").textContent = data.resultados.prompt_a.texto;
        document.getElementById("exp-out-b").textContent = data.resultados.prompt_b.texto;
        document.getElementById("exp-out-c").textContent = data.resultados.prompt_c.texto;
      }
    } catch (e) {
      btnExp.disabled = false;
      btnExp.textContent = "Executar Experimento de Prompts";
      alert("Erro ao rodar experimento: " + e.message);
    }
  });

  // 9. Multimodal: Áudio STT (RF06)
  document.getElementById("btn-processar-audio")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-processar-audio");
    document.getElementById("resultado-audio-stt").textContent = "Transcrição em andamento; aguarde.";
    btn.disabled = true;
    btn.textContent = "Transcrevendo áudio local...";

    try {
      const res = await api("/api/processar/audio", { method: "POST" });
      const data = await res.json();
      btn.disabled = false;
      btn.textContent = "Transcrever Áudio e Validar Entidades";

      const out = document.getElementById("resultado-audio-stt");
      if (out && data.sucesso) {
        out.innerHTML = `
          <div class="alert alert-notice">
            <strong>Duração:</strong> ${data.metadados.duracao_segundos}s | <strong>Modelo:</strong> ${esc(data.metadados.modelo_stt)}
          </div>
          <strong>Transcrição Bruta:</strong>
          <pre class="code-font" style="background:#f1f5f9; padding:8px; border-radius:4px; max-height:100px; overflow-y:auto;">${esc(data.transcricao_bruta)}</pre>
          <strong style="margin-top:8px; display:block;">Transcrição Revisada:</strong>
          <pre class="code-font" style="background:#e8f5e9; padding:8px; border-radius:4px; max-height:120px; overflow-y:auto;">${esc(data.transcricao_revisada)}</pre>
          <div style="margin-top:8px;">
            <strong>Acurácia de Entidades Críticas:</strong> <span class="badge badge-warning">${esc(data.comparacao_gabarito.acuracia_entidades)}</span> — revisão humana obrigatória
          </div>
        `;
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Transcrever Áudio e Validar Entidades";
      document.getElementById("resultado-audio-stt").textContent = e.message;
      alert("Erro ao processar áudio: " + e.message);
    }
  });

  // 10. Multimodal: Visão / OCR (RF08)
  document.getElementById("btn-processar-visao")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-processar-visao");
    document.getElementById("resultado-visao-ocr").textContent = "OCR em andamento; aguarde. O PDF oficial pode exigir correção humana.";
    btn.disabled = true;
    btn.textContent = "Analisando Ficha de Matrícula...";

    try {
      const res = await api("/api/processar/visao", { method: "POST" });
      const data = await res.json();
      btn.disabled = false;
      btn.textContent = "Executar Leitura Visual e OCR";

      const out = document.getElementById("resultado-visao-ocr");
      if (out && data.sucesso) {
        out.innerHTML = `
          <div class="alert alert-notice">
            <strong>Arquivo:</strong> ${esc(data.arquivo_analisado)} | <strong>Campos conferidos com a referência:</strong> ${esc(data.comparacao_gabarito.taxa_acuracia_percentual)}
          </div>
          <strong>Texto extraído com normalização conservadora (revisão humana obrigatória):</strong>
          <pre class="code-font" style="background:#f8fafc; padding:8px; border-radius:4px; max-height:120px; overflow-y:auto;">${esc(data.texto_corrigido)}</pre>
          <strong style="margin-top:8px; display:block;">Trechos Incertos / Manuscritos:</strong>
          <ul style="font-size:0.82rem; padding-left:18px; margin-top:4px;">
            ${(data.trechos_incertos_ou_ilegiveis || []).map(t => `<li>${esc(t)}</li>`).join('')}
          </ul>
          <div style="margin-top:10px; font-size:0.8rem; background:#eff6ff; padding:8px; border-radius:4px;">
            <strong>Soberania e Privacidade:</strong> ${esc(data.justificativa_soberania_privacidade || "Processamento local; revisão humana obrigatória.")}
          </div>
        `;
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Executar Leitura Visual e OCR";
      document.getElementById("resultado-visao-ocr").textContent = e.message;
      alert("Erro ao processar documento: " + e.message);
    }
  });

  // 11. Peça Visual Oficial GOV.MT (RF10)
  document.getElementById("btn-gerar-imagem-peca")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-gerar-imagem-peca");
    btn.disabled = true;
    btn.textContent = "Compondo Peça Oficial GOV.MT...";

    try {
      const res = await api("/api/gerar/imagem", { method: "POST" });
      const data = await res.json();
      btn.disabled = false;
      btn.textContent = "Gerar Comunicado Visual Oficial";

      if (data.sucesso) {
        const imgPeca = document.getElementById("img-peca-visual");
        if (imgPeca) {
          imgPeca.src = data.url_imagem + "?t=" + new Date().getTime();
        }

        const metaBox = document.getElementById("meta-peca-visual");
        if (metaBox) {
          metaBox.innerHTML = `
            <p><strong>Título:</strong> ${esc(data.metadados.titulo)}</p>
            <p><strong>Dimensões:</strong> ${data.metadados.dimensoes}</p>
            <p><strong>Modelo de IA:</strong> ${esc(data.metadados.modelo_ia_utilizado)}</p>
            <p><strong>Data de Geração:</strong> ${data.metadados.data_geracao}</p>
            <p><strong>Estado:</strong> <span id="estado-revisao-imagem">${data.metadados.estado_imagem}</span></p>
            <p><strong>Tarja de Proveniência:</strong> <span class="badge badge-warning">${esc(data.metadados.declaracao_proveniencia)}</span></p>
            <p style="margin-top:8px;"><strong>Prompt Estruturado:</strong><br><small>${esc(data.metadados.prompt_estruturado.sujeito)}</small></p>
            <label><input type="checkbox" id="conferencia-imagem"> Conferi textos, símbolos, mãos, objetos e coerência visual.</label>
            <p>A identidade do revisor deve vir da autenticação real da equipe.</p>
            <p><label>Justificativa: <input id="justificativa-imagem" type="text"></label></p>
            <button type="button" id="aprovar-imagem">Aprovar imagem</button>
            <button type="button" id="rejeitar-imagem">Rejeitar imagem</button>
          `;
          const revisarImagem = async (decisao) => {
            const justificativa = document.getElementById("justificativa-imagem").value.trim();
            if (!justificativa || (decisao === "APROVADO" && !document.getElementById("conferencia-imagem").checked)) {
              alert("Informe a justificativa e confirme a conferência visual antes da aprovação.");
              return;
            }
            try {
              const resposta = await api("/api/revisao/imagem", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_execucao: data.id_execucao, hash_imagem: data.metadados.sha256_imagem,
                  decisao, justificativa }),
              });
              const revisao = await resposta.json();
              if (!revisao.sucesso) throw new Error(revisao.erro || "Falha ao registrar revisão.");
              document.getElementById("estado-revisao-imagem").textContent = revisao.metadados.estado_imagem;
              document.getElementById("aprovar-imagem").disabled = true;
              document.getElementById("rejeitar-imagem").disabled = true;
            } catch (erro) { alert(erro.message); }
          };
          document.getElementById("aprovar-imagem").onclick = () => revisarImagem("APROVADO");
          document.getElementById("rejeitar-imagem").onclick = () => revisarImagem("REJEITADO");
        }
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Gerar Comunicado Visual Oficial";
      alert("Erro ao gerar peça visual: " + e.message);
      btn.disabled = true;
    }
  });

  // 12. Carregamento de Auditoria e LGPD
  async function carregarAuditoriaELgpd() {
    try {
      // LGPD
      const resLgpd = await api("/api/lgpd/relatorio");
      const dataLgpd = await resLgpd.json();
      const lgpdBox = document.getElementById("lgpd-report-container");
      if (lgpdBox && dataLgpd) {
        let htmlMatriz = `
          <h4>${esc(dataLgpd.titulo)}</h4>
          <p style="font-size:0.85rem; color:#64748b; margin-bottom:12px;">${esc(dataLgpd.declaracao_dados_ficticios)}</p>
          <div class="table-responsive">
            <table class="table-gov">
              <thead>
                <tr>
                  <th>Campo</th>
                  <th>Natureza do Dado</th>
                  <th>Finalidade & Risco</th>
                  <th>Minimização</th>
                </tr>
              </thead>
              <tbody>
        `;
        for (const [campo, item] of Object.entries(dataLgpd.matriz_de_dados)) {
          htmlMatriz += `
            <tr>
              <td><strong>${esc(campo)}</strong></td>
              <td>${esc(item.natureza)}</td>
              <td>${esc(item.finalidade)}<br><small style="color:#d97706;">Risco: ${esc(item.risco)}</small></td>
              <td>${item.minimizar_no_prompt ? '<span class="badge badge-ok">Minimizado</span>' : '<span class="badge badge-info">Essencial</span>'}</td>
            </tr>
          `;
        }
        htmlMatriz += "</tbody></table></div>";
        lgpdBox.innerHTML = htmlMatriz;
      }

      // Logs de Auditoria
      const resLogs = await api("/api/logs");
      const logs = await resLogs.json();
      const logsBox = document.getElementById("audit-logs-container");
      if (logsBox) {
        if (!logs.length) {
          logsBox.innerHTML = "<p>Nenhum log registrado até o momento.</p>";
        } else {
          logsBox.innerHTML = logs.reverse().map(registro => { const l = {...registro, decisao_humana: registro.decisao_humana_atual || registro.decisao_humana}; return `
            <div class="log-item ${l.decisao_humana?.status === 'APROVADO' ? 'aprovado' : l.decisao_humana?.status === 'REJEITADO' ? 'rejeitado' : ''}">
              <strong>${esc(l.id_execucao)}</strong> [${esc(l.modalidade.toUpperCase())}] • ${new Date(l.timestamp).toLocaleTimeString()}<br>
              <span>Modelo: ${esc(l.modelo)} (${l.duracao_segundos}s)</span><br>
              <strong>Decisão Humana:</strong> <span class="badge ${l.decisao_humana?.status === 'APROVADO' ? 'badge-ok' : l.decisao_humana?.status === 'REJEITADO' ? 'badge-danger' : 'badge-warning'}">${esc(l.decisao_humana?.status || 'Pendente')}</span>
              <p style="font-size:0.75rem; color:#64748b; margin-top:4px;">Justificativa: ${esc(l.decisao_humana?.justificativa || 'Nenhuma')}</p>
            </div>
          `; }).join('');
        }
      }
    } catch (e) {
      alert("Falha ao carregar auditoria/LGPD: " + e.message);
    }
  }

  document.getElementById("btn-atualizar-logs")?.addEventListener("click", carregarAuditoriaELgpd);
});
