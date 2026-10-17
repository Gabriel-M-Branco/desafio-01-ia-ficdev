// Central Inteligente de Atendimento - GOV.MT (Frontend Controller)

document.addEventListener("DOMContentLoaded", () => {
  let ultimaExecucaoId = null;
  let ultimoUrlPdf = null;

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
      const res = await fetch("/api/config");
      const data = await res.json();
      const badgeMode = document.getElementById("badge-api-mode");
      if (badgeMode) {
        badgeMode.textContent = data.has_hf_token ? "Modo: Hugging Face API" : "Modo: Local";
      }
    } catch (e) {
      console.warn("Erro ao buscar configurações iniciais:", e);
    }
  }
  carregarConfiguracao();

  // 4. Carregamento de Casos de Teste Pré-definidos
  const selectCaso = document.getElementById("caso-predefinido");
  const inputTexto = document.getElementById("input-texto-solicitacao");

  async function atualizarTextoCaso(valor) {
    if (!valor || valor === "personalizado") {
      inputTexto.value = "";
      return;
    }
    inputTexto.value = "Carregando conteúdo real da modalidade selecionada...";
    try {
      const res = await fetch(`/api/casos/${valor}`);
      if (!res.ok) throw new Error("Status " + res.status);
      const data = await res.json();
      inputTexto.value = data.conteudo || "";
    } catch (e) {
      console.error("Erro ao carregar caso:", e);
      inputTexto.value = "";
      alert("Falha ao carregar conteúdo real do caso: " + e.message);
    }
  }

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

    btnProcessar.disabled = true;
    btnProcessar.textContent = "Analisando e Gerando...";

    try {
      const res = await fetch("/api/processar/texto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: texto, caso: selectCaso?.value || "texto_original" }),
      });

      const data = await res.json();
      btnProcessar.disabled = false;
      btnProcessar.textContent = "Processar Solicitacao (RF03/RF05)";

      if (!data.sucesso) {
        alert("Erro no processamento: " + (data.erro || "Falha desconhecida"));
        return;
      }

      ultimaExecucaoId = data.id_execucao;
      ultimoUrlPdf = data.url_pdf || null;

      // Atualiza Minuta
      const editorMinuta = document.getElementById("editor-minuta");
      if (editorMinuta) editorMinuta.value = data.minuta_institucional || "";

      // Atualiza JSON Viewer
      const jsonView = document.getElementById("json-extracao-view");
      if (jsonView) jsonView.textContent = JSON.stringify(data.extracao, null, 2);

      // Atualiza Metricas
      document.getElementById("metric-duracao").textContent = `${data.metricas.duracao_segundos}s`;
      document.getElementById("metric-tokens").textContent = data.metricas.total_tokens || "-";
      document.getElementById("metric-custo").textContent = `US$ ${data.metricas.custo_usd.toFixed(2)}`;

      const badgeStatus = document.getElementById("badge-status-revisao");
      if (badgeStatus) {
        badgeStatus.textContent = "Pendente de Revisao Humana";
        badgeStatus.className = "badge badge-warning";
      }

      // 5. Renderiza o Painel de Conferência Visual de Dados e Auditoria (RF13)
      renderizarPainelConferencia(data.avaliacao_gabarito, data.extracao);

      // Exibe avaliacao resumida na aba de métricas
      const gabaritoBox = document.getElementById("comparacao-gabarito-view");
      if (gabaritoBox && data.avaliacao_gabarito) {
        const aval = data.avaliacao_gabarito;
        gabaritoBox.innerHTML = `
          <strong>Taxa de Conformidade Institucional:</strong> ${aval.taxa_fidelidade_percentual}% (${aval.total_acertos}/${aval.total_campos_analisados} campos corretos)<br>
          <strong>Status de Qualidade:</strong> <span class="badge ${aval.status_qualidade === 'Excelente' ? 'badge-ok' : 'badge-warning'}">${aval.status_qualidade}</span>
        `;
      }
    } catch (err) {
      btnProcessar.disabled = false;
      btnProcessar.textContent = "Processar Solicitacao (RF03/RF05)";
      alert("Erro na requisicao: " + err.message);
    }
  });

  // Função Especializada para o Painel de Conferência de Dados (RF13)
  function renderizarPainelConferencia(aval, extracao) {
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

    const erros = aval.erros_encontrados || [];
    const comparativo = aval.comparativo_campos || [];
    const pendencias = comparativo.filter((c) => c.eh_pendencia || c.status === "PENDENCIA");

    // 1. Atualiza Indicadores KPI
    if (taxaEl) taxaEl.textContent = `${aval.taxa_fidelidade_percentual}%`;
    if (statusEl) {
      statusEl.textContent = aval.status_qualidade;
      statusEl.className = `badge ${aval.status_qualidade === "Excelente" ? "badge-ok" : "badge-warning"}`;
    }
    if (acertosEl) acertosEl.textContent = `${aval.total_acertos} / ${aval.total_campos_analisados}`;
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
              ${erros.map((e) => `<span class="badge badge-danger">${e.rotulo || e.campo || "Campo"}: esperado "${e.esperado}", obtido "${e.obtido}"</span>`).join("")}
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
            <strong>Conferência Conforme:</strong> ${aval.total_acertos}/${aval.total_campos_analisados} campos validados perante as regras oficiais. Identificadas ${pendencias.length} pendências documentais no pedido:
            <div class="banner-badge-group">
              ${pendencias.map((p) => `<span class="badge badge-warning">${p.rotulo || p.campo}: Pendente</span>`).join("")}
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
            <strong>Conferência Concluída com Sucesso:</strong> Todos os ${aval.total_campos_analisados} dados conferem integralmente com as regras e formatos oficiais (Fidelidade: 100%).
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
            status: erro ? "DIVERGENTE" : (isPend ? "PENDENCIA" : "CORRETO"),
            eh_pendencia: isPend,
            gravidade: erro ? erro.gravidade : "Nenhuma",
            acao_recomendada: erro ? erro.acao_recomendada : "Conferido com sucesso",
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
          const rowClass = isDivergente ? "row-divergente" : isPendencia ? "row-pendencia" : "row-correto";

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
            extraidoHtml = `<span class="val-extraido-erro" id="val-extraido-${idx}">${item.obtido || "Vazio"}</span>`;
            statusBadge = `<span class="diag-tag diag-divergente">▲ Divergente</span>`;
            acaoHtml = `<button type="button" class="btn-corrigir-inline" data-idx="${idx}" data-campo="${item.campo}" data-esperado="${item.esperado}" data-obtido="${item.obtido}">Aplicar Correção</button>`;
          } else if (isPendencia) {
            extraidoHtml = `<span class="val-pendencia-destaque">não localizado</span>`;
            statusBadge = `<span class="diag-tag diag-pendente">○ Pendência</span>`;
            acaoHtml = `<span style="color:#64748B; font-size:0.75rem;">Documento Exigido</span>`;
          } else {
            extraidoHtml = `<strong>${item.obtido}</strong>`;
            statusBadge = `<span class="diag-tag diag-correto">● Conforme</span>`;
            acaoHtml = `<span style="color:#15803D; font-weight:600; font-size:0.75rem;">Conferido</span>`;
          }

          return `
            <tr class="${rowClass}" data-status="${item.status}">
              <td>
                <strong>${item.rotulo || item.campo}</strong>
                <br><span style="font-size:0.7rem; color:#64748B; font-family:monospace;">${item.campo}</span>
              </td>
              <td>${extraidoHtml}</td>
              <td>
                <span class="val-esperado-destaque">${item.esperado}</span>
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
          const esperado = btn.getAttribute("data-esperado");
          const obtido = btn.getAttribute("data-obtido");
          const idx = btn.getAttribute("data-idx");

          // Atualiza o editor de minuta
          const editorMinuta = document.getElementById("editor-minuta");
          if (editorMinuta && obtido && esperado) {
            if (editorMinuta.value.includes(obtido)) {
              editorMinuta.value = editorMinuta.value.replaceAll(obtido, esperado);
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
            justInput.value = `Correção aplicada no campo ${campo} para '${esperado}' conforme padrão institucional oficial.`;
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
          show = row.classList.contains("row-pendencia");
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
              ? "Nenhuma divergência encontrada. Todos os campos estão validados perante os formatos oficiais."
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
      alert("Nenhuma minuta disponivel para exportacao em PDF.");
      return;
    }

    btnExportarPdf.disabled = true;
    btnExportarPdf.textContent = "Gerando PDF Oficial Timbrado...";

    try {
      const res = await fetch("/api/minuta/gerar_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          texto_minuta: textoMinuta,
          protocolo: "2026-000142",
          solicitante: "Marcos Vinicius de Almeida Santos",
          categoria: "Matricula e Ingresso",
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
        alert("Erro ao gerar PDF: " + (data.erro || "Falha desconhecida"));
      }
    } catch (e) {
      btnExportarPdf.disabled = false;
      btnExportarPdf.textContent = "Visualizar / Baixar Minuta em PDF Oficial";
      alert("Erro ao conectar com o gerador de PDF: " + e.message);
    }
  });

  // 6. Sintese de Voz TTS da Minuta Aprovada/Editada (RF07)
  const btnTts = document.getElementById("btn-gerar-tts");
  btnTts?.addEventListener("click", async () => {
    const textoMinuta = document.getElementById("editor-minuta")?.value.trim();
    if (!textoMinuta) {
      alert("Nenhuma minuta disponivel para sintese de voz.");
      return;
    }

    btnTts.disabled = true;
    btnTts.textContent = "Sintetizando Audio Neural...";

    try {
      const res = await fetch("/api/sintetizar/audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: textoMinuta }),
      });

      const data = await res.json();
      btnTts.disabled = false;
      btnTts.textContent = "Gerar Audio Acessivel (RF07)";

      if (data.sucesso) {
        const audioContainer = document.getElementById("tts-audio-container");
        const audioPlayer = document.getElementById("tts-audio-player");
        if (audioContainer && audioPlayer) {
          audioContainer.style.display = "flex";
          audioPlayer.src = data.url_audio + "?t=" + new Date().getTime();
          audioPlayer.play();
        }
      } else {
        alert("Erro na sintese: " + (data.erro || "Falha na geracao de audio"));
      }
    } catch (e) {
      btnTts.disabled = false;
      btnTts.textContent = "Gerar Audio Acessivel (RF07)";
      alert("Erro: " + e.message);
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

    const textoAtualizado = document.getElementById("editor-minuta")?.value.trim();

    try {
      const res = await fetch("/api/revisao/decisao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_execucao: ultimaExecucaoId,
          decisao: decisao,
          justificativa: justificativa,
          texto_final: textoAtualizado,
        }),
      });

      const data = await res.json();
      if (data.sucesso) {
        const badgeStatus = document.getElementById("badge-status-revisao");
        if (badgeStatus) {
          badgeStatus.textContent = `Status: ${decisao}`;
          badgeStatus.className = decisao === "APROVADO" ? "badge badge-ok" : decisao === "CORRIGIDO" ? "badge badge-warning" : "badge badge-danger";
        }
        alert(`Decisão registrada com sucesso no log de auditoria: [${decisao}]`);
      }
    } catch (e) {
      alert("Falha ao registrar decisão: " + e.message);
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
      const res = await fetch("/api/experimento/prompts", { method: "POST" });
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

  // 9. Multimodal: Audio STT (RF06)
  document.getElementById("btn-processar-audio")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-processar-audio");
    btn.disabled = true;
    btn.textContent = "Transcrevendo audio...";

    try {
      const res = await fetch("/api/processar/audio", { method: "POST" });
      const data = await res.json();
      btn.disabled = false;
      btn.textContent = "Transcrever Áudio e Validar Entidades";

      const out = document.getElementById("resultado-audio-stt");
      if (out && data.sucesso) {
        out.innerHTML = `
          <div class="alert alert-notice">
            <strong>Duracao:</strong> ${data.metadados.duracao_segundos}s | <strong>Modelo:</strong> ${data.metadados.modelo_stt}
          </div>
          <strong>Transcricao Bruta:</strong>
          <pre class="code-font" style="background:#f1f5f9; padding:8px; border-radius:4px; max-height:100px; overflow-y:auto;">${data.transcricao_bruta}</pre>
          <strong style="margin-top:8px; display:block;">Transcricao Revisada:</strong>
          <pre class="code-font" style="background:#e8f5e9; padding:8px; border-radius:4px; max-height:120px; overflow-y:auto;">${data.transcricao_revisada}</pre>
          <div style="margin-top:8px;">
            <strong>Acuracia de Entidades Criticas:</strong> <span class="badge badge-ok">${data.comparacao_gabarito.acuracia_entidades}</span>
          </div>
        `;
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Transcrever Áudio e Validar Entidades";
      alert("Erro ao processar audio: " + e.message);
    }
  });

  // 10. Multimodal: Visao / OCR (RF08)
  document.getElementById("btn-processar-visao")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-processar-visao");
    btn.disabled = true;
    btn.textContent = "Analisando Ficha de Matricula...";

    try {
      const res = await fetch("/api/processar/visao", { method: "POST" });
      const data = await res.json();
      btn.disabled = false;
      btn.textContent = "Executar Leitura Visual e OCR";

      const out = document.getElementById("resultado-visao-ocr");
      if (out && data.sucesso) {
        out.innerHTML = `
          <div class="alert alert-notice">
            <strong>Arquivo:</strong> ${data.arquivo_analisado} | <strong>Conformidade Documental:</strong> ${data.comparacao_gabarito.taxa_acuracia_percentual}
          </div>
          <strong>Texto Corrigido Estruturado:</strong>
          <pre class="code-font" style="background:#f8fafc; padding:8px; border-radius:4px; max-height:120px; overflow-y:auto;">${data.texto_corrigido}</pre>
          <strong style="margin-top:8px; display:block;">Trechos Incertos / Manuscritos:</strong>
          <ul style="font-size:0.82rem; padding-left:18px; margin-top:4px;">
            ${data.trechos_incertos_ou_ilegiveis.map(t => `<li>${t}</li>`).join('')}
          </ul>
          <div style="margin-top:10px; font-size:0.8rem; background:#eff6ff; padding:8px; border-radius:4px;">
            <strong>Soberania e Privacidade:</strong> ${data.justificativa_soberania_privacidade}
          </div>
        `;
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Executar Leitura Visual e OCR";
      alert("Erro ao processar documento: " + e.message);
    }
  });

  // 11. Peca Visual Oficial GOV.MT (RF10)
  document.getElementById("btn-gerar-imagem-peca")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-gerar-imagem-peca");
    btn.disabled = true;
    btn.textContent = "Compondo Peca Oficial GOV.MT...";

    try {
      const res = await fetch("/api/gerar/imagem", { method: "POST" });
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
            <p><strong>Título:</strong> ${data.metadados.titulo}</p>
            <p><strong>Dimensões:</strong> ${data.metadados.dimensoes}</p>
            <p><strong>Modelo de IA:</strong> ${data.metadados.modelo_ia_utilizado}</p>
            <p><strong>Data de Geração:</strong> ${data.metadados.data_geracao}</p>
            <p><strong>Tarja de Proveniência:</strong> <span class="badge badge-warning">${data.metadados.declaracao_proveniencia}</span></p>
            <p style="margin-top:8px;"><strong>Prompt Estruturado:</strong><br><small>${data.metadados.prompt_estruturado.sujeito}</small></p>
          `;
        }
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Gerar Comunicado Visual Oficial";
      alert("Erro ao gerar peça visual: " + e.message);
    }
  });

  // 12. Carregamento de Auditoria e LGPD
  async function carregarAuditoriaELgpd() {
    try {
      // LGPD
      const resLgpd = await fetch("/api/lgpd/relatorio");
      const dataLgpd = await resLgpd.json();
      const lgpdBox = document.getElementById("lgpd-report-container");
      if (lgpdBox && dataLgpd) {
        let htmlMatriz = `
          <h4>${dataLgpd.titulo}</h4>
          <p style="font-size:0.85rem; color:#64748b; margin-bottom:12px;">${dataLgpd.declaracao_dados_ficticios}</p>
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
              <td><strong>${campo}</strong></td>
              <td>${item.natureza}</td>
              <td>${item.finalidade}<br><small style="color:#d97706;">Risco: ${item.risco}</small></td>
              <td>${item.minimizar_no_prompt ? '<span class="badge badge-ok">Minimizado</span>' : '<span class="badge badge-info">Essencial</span>'}</td>
            </tr>
          `;
        }
        htmlMatriz += "</tbody></table></div>";
        lgpdBox.innerHTML = htmlMatriz;
      }

      // Logs de Auditoria
      const resLogs = await fetch("/api/logs");
      const logs = await resLogs.json();
      const logsBox = document.getElementById("audit-logs-container");
      if (logsBox) {
        if (!logs.length) {
          logsBox.innerHTML = "<p>Nenhum log registrado até o momento.</p>";
        } else {
          logsBox.innerHTML = logs.reverse().map(l => `
            <div class="log-item ${l.decisao_humana?.status === 'APROVADO' ? 'aprovado' : l.decisao_humana?.status === 'REJEITADO' ? 'rejeitado' : ''}">
              <strong>${l.id_execucao}</strong> [${l.modalidade.toUpperCase()}] • ${new Date(l.timestamp).toLocaleTimeString()}<br>
              <span>Modelo: ${l.modelo} (${l.duracao_segundos}s)</span><br>
              <strong>Decisão Humana:</strong> <span class="badge ${l.decisao_humana?.status === 'APROVADO' ? 'badge-ok' : l.decisao_humana?.status === 'REJEITADO' ? 'badge-danger' : 'badge-warning'}">${l.decisao_humana?.status || 'Pendente'}</span>
              <p style="font-size:0.75rem; color:#64748b; margin-top:4px;">Justificativa: ${l.decisao_humana?.justificativa || 'Nenhuma'}</p>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.warn("Erro ao buscar logs/lgpd:", e);
    }
  }

  document.getElementById("btn-atualizar-logs")?.addEventListener("click", carregarAuditoriaELgpd);
});
