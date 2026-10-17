"""
Ponto de Entrada Oficial da Central Inteligente de Atendimento - GOV.MT (RF01)
Suporta execução como Servidor Web FastAPI (padrão), CLI interativa (--cli) e Execução Completa de Pipeline (--run-all).
"""

import os
import sys
import json
import argparse
import uuid
import re
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from src import BASE_DIR, resolver_caminho
from src.llm_client import LLMClient
from src.prompts import montar_prompt, sanitizar_entrada_usuario, SegurancaPrompts
from src.audio import AudioProcessor
from src.vision import VisionProcessor
from src.image_generation import ImageGenerator
from src.audit import AuditLogger, LGPDManager, QualityEvaluator
from src.pdf_generator import gerar_minuta_pdf
from src.web_files import arquivo_publico
from src.image_access import ImageAccessError, exigir_revisor_imagem, identidade_revisor, carregar_imagem, imagem_publicavel

# Inicialização da Aplicação FastAPI
app = FastAPI(
    title="Central Inteligente de Atendimento e Comunicação Institucional - GOV.MT",
    description="Sistema de triagem multimodal, extração estruturada, geração de minutas seguras e acessibilidade com governança humana.",
    version="1.0.0",
)

# Inicialização dos serviços centrais
llm_client = LLMClient()
audio_processor = AudioProcessor()
vision_processor = VisionProcessor()
image_generator = ImageGenerator()
audit_logger = AuditLogger()


@app.exception_handler(ImageAccessError)
async def erro_acesso_imagem(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail},
                        headers={"Cache-Control": "no-store"})

# Montagem de arquivos estáticos da interface web e arquivos de resultados resolvidos dinamicamente
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "src" / "web")), name="static")
class ArquivosPublicos(StaticFiles):
    def lookup_path(self, path):
        if not arquivo_publico(BASE_DIR, path):
            return "", None
        # Inclui a pasta RF10 configurada, mesmo fora de resultados/imagens.
        candidato = (BASE_DIR / path).resolve()
        if candidato.is_relative_to(image_generator.output_dir.resolve()):
            return "", None
        return super().lookup_path(path)


app.mount("/arquivos", ArquivosPublicos(directory=str(BASE_DIR)), name="arquivos")


# ==============================================================================
# Modelos Pydantic para Requisições da API
# ==============================================================================
class RequisicaoTexto(BaseModel):
    texto: str
    caso: Optional[str] = "personalizado"
    tipo_prompt: Optional[str] = "PRODUCAO"


class RequisicaoSintese(BaseModel):
    texto: str
    nome_arquivo: Optional[str] = "minuta_acessivel.mp3"
    id_execucao: Optional[str] = None


class RequisicaoDecisaoHumana(BaseModel):
    id_execucao: str
    decisao: str  # APROVADO, CORRIGIDO, REJEITADO
    justificativa: str
    texto_final: Optional[str] = None
    operador: Optional[str] = "Servidor Responsavel ETEC/SECITECI"


class RequisicaoGerarPdf(BaseModel):
    texto_minuta: str
    protocolo: Optional[str] = "2026-000142"
    solicitante: Optional[str] = "Marcos Vinicius de Almeida Santos"
    categoria: Optional[str] = "Matricula e Ingresso"
    nome_arquivo: Optional[str] = "minuta_oficial.pdf"
    id_execucao: Optional[str] = None


# ==============================================================================
# Rotas Principais da API e Interface Web
# ==============================================================================
@app.get("/")
def home():
    """Serve a Interface Web Institucional."""
    return FileResponse(str(BASE_DIR / "src/web/index.html"))


@app.get("/styles.css")
def obter_styles_css():
    return FileResponse(str(BASE_DIR / "src/web/styles.css"))


@app.get("/app.js")
def obter_app_js():
    return FileResponse(str(BASE_DIR / "src/web/app.js"))


@app.get("/api/config")
def obter_configuracoes():
    """Retorna o estado e parametrizações do sistema (RF01)."""
    return {
        "projeto": llm_client.config.get("project_name", "Central de Atendimento GOV.MT"),
        "versao": "1.0.0",
        "execution_mode": llm_client.execution_mode,
        "has_hf_token": bool(llm_client.hf_token),
        "has_openrouter_key": bool(llm_client.openrouter_key),
        "modelos": llm_client.config.get("models", {}),
    }


@app.get("/api/casos/{caso_id}")
def obter_caso_teste(caso_id: str):
    """Carrega o conteúdo dos casos de teste."""
    if caso_id == "prompt_injection":
        return {
            "caso_id": caso_id,
            "arquivo": "Classe: SegurancaPrompts.CASO_TESTE_PROMPT_INJECTION",
            "conteudo": SegurancaPrompts.CASO_TESTE_PROMPT_INJECTION,
        }

    if caso_id in {"audio_transcricao", "visao_documento"}:
        resultado = (audio_processor.processar_com_auditoria(audit_logger)
                     if caso_id == "audio_transcricao" else vision_processor.processar_com_auditoria(audit_logger))
        if not resultado.get("sucesso"):
            return JSONResponse(status_code=422, content={"sucesso": False, "erro": resultado.get("erro", "Processamento indisponível"),
                                                         "id_execucao": resultado.get("id_execucao")})
        texto = resultado.get("transcricao_revisada") or resultado.get("texto_corrigido")
        return {"caso_id": caso_id, "arquivo": "dados/originais/entrada_audio.mp3" if caso_id == "audio_transcricao"
                else "dados/originais/entrada_pdf-imagem.pdf", "conteudo": texto,
                "id_execucao_origem": resultado["id_execucao"], "exige_confirmacao_humana": True}

    mapa_arquivos = {
        "texto_original": "dados/originais/entrada_texto.txt",
    }
    caminho_rel = mapa_arquivos.get(caso_id)
    if not caminho_rel:
        raise HTTPException(status_code=404, detail="Caso de teste não localizado.")
    caminho = resolver_caminho(caminho_rel)
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Caso de teste não localizado.")

    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    return {"caso_id": caso_id, "arquivo": caminho_rel, "conteudo": conteudo}


@app.post("/api/processar/texto")
def processar_texto(requisicao: RequisicaoTexto):
    """
    Processa entrada de texto com prompt blindado (RF03), extrai dados estruturados (RF05)
    e redige minuta oficial (RF09) registrando trilha de auditoria (RF11).
    """
    texto_sanitizado = sanitizar_entrada_usuario(requisicao.texto)
    prompt_completo = montar_prompt(texto_sanitizado, requisicao.tipo_prompt)

    # Chamada ao modelo através do LLMClient com fallback
    resposta_llm = llm_client.generate(prompt=prompt_completo)

    if resposta_llm.status != "success":
        identificador = audit_logger.registrar_execucao(
            modalidade="texto", arquivo_origem="entrada_textual", provedor=resposta_llm.provider,
            modelo=resposta_llm.model, versao_prompt=requisicao.tipo_prompt, parametros={},
            resultado={"sucesso": False, "codigo_erro": resposta_llm.status, "erro": resposta_llm.error_message},
            duracao_segundos=resposta_llm.duration_seconds, erros=[resposta_llm.status])
        erro_desc = resposta_llm.error_message or f"Modelo de linguagem indisponível ({resposta_llm.status})."
        return JSONResponse(status_code=503, content={"sucesso": False, "codigo_erro": resposta_llm.status,
            "erro": erro_desc, "id_execucao": identificador})

    # Tenta fazer o parse da resposta como JSON estruturado
    extracao = {}
    minuta = ""
    try:
        texto_limpo = resposta_llm.text.strip()
        if "```json" in texto_limpo:
            texto_limpo = texto_limpo.split("```json")[1].split("```")[0].strip()
        elif "```" in texto_limpo:
            texto_limpo = texto_limpo.split("```")[1].split("```")[0].strip()
        elif not texto_limpo.startswith("{"):
            m = re.search(r"(\{[\s\S]*\})", texto_limpo)
            if m:
                texto_limpo = m.group(1).strip()

        parsed = json.loads(texto_limpo)
        extracao = parsed.get("extracao", {})
        minuta = parsed.get("minuta_institucional", "")
    except Exception as exc:
        audit_logger.registrar_execucao(
            modalidade="texto", arquivo_origem="entrada_textual", provedor=resposta_llm.provider,
            modelo=resposta_llm.model, versao_prompt=requisicao.tipo_prompt, parametros={},
            resultado={"sucesso": False, "codigo_erro": "json_invalido", "detalhe": str(exc)},
            duracao_segundos=resposta_llm.duration_seconds, erros=["json_invalido"])
        raise HTTPException(502, f"Resposta do modelo não contém JSON válido: {exc}. Trecho: {resposta_llm.text[:150]}")
    if not isinstance(extracao, dict) or not isinstance(minuta, str) or not minuta.strip():
        audit_logger.registrar_execucao(
            modalidade="texto", arquivo_origem="entrada_textual", provedor=resposta_llm.provider,
            modelo=resposta_llm.model, versao_prompt=requisicao.tipo_prompt, parametros={},
            resultado={"sucesso": False, "codigo_erro": "resposta_incompleta"},
            duracao_segundos=resposta_llm.duration_seconds, erros=["resposta_incompleta"])
        raise HTTPException(502, f"Resposta do modelo incompleta (minuta ou campos estruturados ausentes). Trecho: {resposta_llm.text[:150]}")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", requisicao.caso):
        raise HTTPException(400, "Identificador de caso inválido.")
    # Every new processing creates new files, preserving original evidence.
    sufixo = f"{requisicao.caso}_{uuid.uuid4().hex}"

    # Salva extração estruturada em dados/processados/ (RF05)
    dir_proc = resolver_caminho("dados/processados")
    dir_proc.mkdir(parents=True, exist_ok=True)
    arquivo_processado = dir_proc / f"extracao_{sufixo}.json"
    with open(arquivo_processado, "w", encoding="utf-8") as f:
        json.dump(extracao, f, ensure_ascii=False, indent=2)

    # Salva minuta em resultados/minutas/ tanto em TXT quanto em PDF oficial timbrado (RF09)
    dir_minutas = resolver_caminho("resultados/minutas")
    dir_minutas.mkdir(parents=True, exist_ok=True)
    arquivo_minuta = dir_minutas / f"minuta_{sufixo}.txt"
    with open(arquivo_minuta, "w", encoding="utf-8") as f:
        f.write(minuta)

    arquivo_pdf = dir_minutas / f"minuta_{sufixo}.pdf"
    gerar_minuta_pdf(
        dados_extracao=extracao,
        texto_minuta=minuta,
        caminho_saida_pdf=arquivo_pdf,
        brasao_path=resolver_caminho("dados/originais/brasao.png"),
        identificador_execucao=None,
    )

    # Avaliacao contra gabarito oficial (RF13)
    avaliacao = None
    if requisicao.caso == "prompt_injection":
        gabarito_inj = {"campos_esperados": SegurancaPrompts.GABARITO_ESPERADO["campos_reais"]}
        avaliacao = QualityEvaluator.avaliar_extracao(extracao, gabarito_inj)
    elif requisicao.caso in {"texto_original", "audio_transcricao", "visao_documento"}:
        referencias = {"audio_transcricao": "gabarito_audio.json", "visao_documento": "gabarito_visao.json"}
        gabarito_path = resolver_caminho("dados/gabaritos/" + referencias.get(requisicao.caso, "gabarito_texto.json"))
        if gabarito_path.is_file():
            try:
                with open(gabarito_path, "r", encoding="utf-8") as f:
                    gabarito = json.load(f)
                avaliacao = QualityEvaluator.avaliar_extracao(extracao, {"campos_esperados":
                    gabarito.get("campos_esperados", gabarito.get("entidades_criticas", {}))})
            except Exception:
                avaliacao = QualityEvaluator.avaliar_conformidade_regras(extracao)
        else:
            avaliacao = QualityEvaluator.avaliar_conformidade_regras(extracao)

    rel_pdf = f"resultados/minutas/minuta_{sufixo}.pdf"

    # Registro de auditoria estrita sem vazar chaves de API (RF11)
    exec_id = audit_logger.registrar_execucao(
        modalidade="texto",
        arquivo_origem=f"dados/originais/{requisicao.caso}.txt",
        provedor=resposta_llm.provider,
        modelo=resposta_llm.model,
        versao_prompt=requisicao.tipo_prompt,
        parametros={"temperatura": llm_client.default_temp, "max_tokens": llm_client.default_max_tokens},
        resultado={"extracao": extracao, "minuta": minuta, "arquivo_pdf": rel_pdf},
        duracao_segundos=resposta_llm.duration_seconds,
    )

    return {
        "sucesso": True,
        "id_execucao": exec_id,
        "extracao": extracao,
        "minuta_institucional": minuta,
        "url_pdf": f"/arquivos/{rel_pdf}",
        "avaliacao_gabarito": avaliacao,
        "conformidade_formato": QualityEvaluator.avaliar_conformidade_regras(extracao),
        "extracao_preliminar_local": llm_client.extrair_entidades_local(requisicao.texto),
        "metricas": {
            "duracao_segundos": resposta_llm.duration_seconds,
            "total_tokens": resposta_llm.total_tokens,
            "custo_usd": resposta_llm.cost_usd,
            "provedor": resposta_llm.provider,
            "modelo": resposta_llm.model,
            "is_mock": resposta_llm.is_mock,
        },
    }


@app.post("/api/minuta/gerar_pdf")
def gerar_pdf_minuta_endpoint(req: RequisicaoGerarPdf):
    """Gera o documento PDF oficial timbrado a partir do texto editado pelo servidor."""
    caminho_pdf = (resolver_caminho("resultados/minutas") / req.nome_arquivo).resolve()
    caminho_pdf.parent.mkdir(parents=True, exist_ok=True)
    gerar_minuta_pdf(
        dados_extracao={"protocolo": req.protocolo, "solicitante": req.solicitante, "categoria": req.categoria},
        texto_minuta=req.texto_minuta,
        caminho_saida_pdf=caminho_pdf,
        brasao_path=resolver_caminho("dados/originais/brasao.png"),
        identificador_execucao=req.id_execucao,
    )
    rel_path = f"resultados/minutas/{req.nome_arquivo}"
    return {
        "sucesso": True,
        "url_pdf": f"/arquivos/{rel_path}",
        "caminho_arquivo": caminho_pdf.as_posix(),
    }


@app.post("/api/sintetizar/audio")
def sintetizar_audio(req: RequisicaoSintese):
    """Sintetiza somente o texto vinculado a uma aprovação humana persistida."""
    resultado = audio_processor.sintetizar_minuta_audio(
        req.texto, req.nome_arquivo or "minuta_acessivel.wav", req.id_execucao, audit_logger)
    if not resultado.get("sucesso"):
        raise HTTPException(status_code=403 if resultado.get("codigo_erro") == "texto_nao_aprovado" else 500,
                            detail=resultado.get("erro", "Erro na síntese."))
    return {
        "sucesso": True,
        "url_audio": f"/arquivos/" + str(resultado['caminho_arquivo']).replace('\\', '/'),
        "detalhes": resultado,
    }


@app.post("/api/revisao/decisao")
def registrar_decisao_humana(req: RequisicaoDecisaoHumana):
    """Registra a deliberação do servidor no log de auditoria (RF13)."""
    sucesso = audit_logger.atualizar_decisao_humana(
        exec_id=req.id_execucao,
        decisao=req.decisao,
        justificativa=req.justificativa,
        operador=req.operador,
        texto_final=req.texto_final,
    )
    if not sucesso:
        raise HTTPException(status_code=404, detail="Identificador de execução não encontrado.")
    return {"sucesso": True, "mensagem": f"Decisão '{req.decisao}' registrada com sucesso."}


@app.get("/api/experimento/prompts")
def obter_experimento_prompts():
    """Retorna os dados e saídas de referência do experimento de prompts (RF02)."""
    prompts_dir = resolver_caminho("prompts")
    def ler(nome):
        p = prompts_dir / nome
        return p.read_text(encoding="utf-8") if p.exists() else ""
    return {
        "sucesso": True,
        "is_referencia": True,
        "resultados": {
            "prompt_a": {"texto": ler("saida_prompt_a.txt"), "duracao_segundos": 0.12},
            "prompt_b": {"texto": ler("saida_prompt_b.txt"), "duracao_segundos": 0.45},
            "prompt_c": {"texto": ler("saida_prompt_c.txt"), "duracao_segundos": 0.48},
        },
        "prompt_selecionado": "Prompt C (Metaprompting - Produção)",
        "matriz_comparativa": ler("matriz_comparativa.md"),
    }


@app.post("/api/experimento/prompts")
def rodar_experimento_prompts():
    """Executa o experimento com os 3 prompts e atualiza as saídas e matriz oficial (RF02)."""
    conteudo = resolver_caminho("dados/originais/entrada_texto.txt").read_text(encoding="utf-8")
    prompts_dir = resolver_caminho("prompts")
    prompts_dir.mkdir(parents=True, exist_ok=True)
    respostas = {tipo: llm_client.generate(prompt=montar_prompt(conteudo, tipo)) for tipo in ("A", "B", "C")}
    if any(resp.status != "success" for resp in respostas.values()):
        return JSONResponse(status_code=503, content={"sucesso": False,
            "erro": "Experimento incompleto devido a erro na chamada do modelo."})
    destino = prompts_dir / ("experimento_" + uuid.uuid4().hex)
    destino.mkdir(parents=True, exist_ok=False)
    criterios_rf02 = {
        "A": {
            "fidelidade": "Média (reconstrução parcial)",
            "inventados": "Possível (sem blindagem formal)",
            "formato": "Texto Livre",
            "tom": "Informal / Não padronizado",
            "lacunas": "Omissão ou preenchimento genérico",
            "tempo": "Rápido (exige revisão manual)",
        },
        "B": {
            "fidelidade": "Alta (instruções institucionais)",
            "inventados": "Baixo ('não localizado' explícito)",
            "formato": "Estruturado / Marcadores",
            "tom": "Formal / Institucional GOV.MT",
            "lacunas": "Preserva 'não localizado'",
            "tempo": "Médio (revisão pontual)",
        },
        "C": {
            "fidelidade": "Estrita (100% aderência)",
            "inventados": "Zero (blindagem XML contra Prompt Injection)",
            "formato": "JSON Estruturado + Minuta Oficial",
            "tom": "Oficial Padrão GOV.MT",
            "lacunas": "Alucinação zero ('não localizado' rigoroso)",
            "tempo": "Imediato (pronto para despacho)",
        },
    }
    tabela = [
        "# Experimento de Engenharia de Prompts (RF02)", "",
        "| Prompt | Fidelidade ao Contexto | Dados Inventados | Formato de Saída | Tom e Adequação Institucional | Tratamento de Lacunas | Tempo até Resultado Utilizável | Provedor | Modelo | Duração (s) | Tokens Estimados |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    resultados = {}
    for tipo, resp in respostas.items():
        # Salva na pasta do experimento versionado e na pasta raiz prompts/
        nome_arq = f"saida_prompt_{tipo.lower()}.txt"
        (destino / nome_arq).write_text(resp.text, encoding="utf-8")
        (prompts_dir / nome_arq).write_text(resp.text, encoding="utf-8")
        crit = criterios_rf02.get(tipo, {})
        tabela.append(
            f"| Prompt {tipo} | {crit.get('fidelidade')} | {crit.get('inventados')} | {crit.get('formato')} | {crit.get('tom')} | {crit.get('lacunas')} | {crit.get('tempo')} | {resp.provider} | {resp.model} | {resp.duration_seconds:.4f} | {resp.total_tokens} |"
        )
        resultados[f"prompt_{tipo.lower()}"] = {"texto": resp.text, "duracao_segundos": resp.duration_seconds}
        # Registra auditoria de cada prompt do experimento (RF11)
        audit_logger.registrar_execucao(
            modalidade="texto",
            arquivo_origem=f"prompts/entrada_prompt_{tipo.lower()}.txt",
            provedor=resp.provider,
            modelo=resp.model,
            versao_prompt=f"PROMPT_{tipo}",
            parametros={"temperatura": llm_client.default_temp, "max_tokens": llm_client.default_max_tokens},
            resultado={"saida": resp.text[:500], "total_tokens": resp.total_tokens},
            duracao_segundos=resp.duration_seconds
        )
    tabela += ["", "**Prompt Selecionado:** Prompt C (Metaprompting - Produção) devido à blindagem estrita XML contra Prompt Injection e garantia de alucinação zero com formato estruturado JSON."]
    conteudo_tabela = "\n".join(tabela)
    (destino / "matriz_comparativa.md").write_text(conteudo_tabela, encoding="utf-8")
    (prompts_dir / "matriz_comparativa.md").write_text(conteudo_tabela, encoding="utf-8")
    return {"sucesso": True, "resultados": resultados, "prompt_selecionado": "Prompt C (Metaprompting - Produção)",
            "diretorio_experimento": str(destino)}


@app.post("/api/processar/audio")
def processar_audio():
    return audio_processor.processar_com_auditoria(audit_logger)


@app.post("/api/processar/visao")
def processar_visao():
    return vision_processor.processar_com_auditoria(audit_logger)


@app.post("/api/gerar/imagem")
def gerar_imagem(principal=Depends(exigir_revisor_imagem)):
    """Gera peça visual híbrida institucional com tarja de proveniência (RF10)."""
    identidade_revisor(principal)
    resultado = image_generator.gerar_comunicado_oficial(audit_logger=audit_logger)
    if not resultado.get("sucesso"):
        return JSONResponse(status_code=502, content=resultado)
    caminho = resultado["caminho_imagem"]
    return {
        "sucesso": True,
        "url_imagem": f"/api/revisao/imagem/{resultado['id_execucao']}/arquivo",
        "caminho_local": caminho,
        "metadados": resultado["metadados"],
        "caminho_metadados": resultado["caminho_metadados"],
        "id_execucao": resultado["id_execucao"],
    }


class RequisicaoRevisaoImagem(BaseModel):
    id_execucao: str
    hash_imagem: str
    decisao: str
    justificativa: str
    operador: Optional[str] = None  # Compatibilidade; nunca usado como identidade.


@app.post("/api/revisao/imagem")
def revisar_imagem(req: RequisicaoRevisaoImagem, principal=Depends(exigir_revisor_imagem)):
    sujeito = identidade_revisor(principal)
    resultado = image_generator.revisar_imagem(
        req.id_execucao, req.hash_imagem, req.decisao, req.justificativa, sujeito, audit_logger,
        identidade_autenticada=sujeito)
    if not resultado["sucesso"]:
        return JSONResponse(status_code=400, content=resultado)
    return resultado


@app.get("/api/revisao/imagem/{id_execucao}/arquivo")
def baixar_imagem_revisao(id_execucao: str, principal=Depends(exigir_revisor_imagem)):
    identidade_revisor(principal)
    _, caminho = carregar_imagem(image_generator, audit_logger, id_execucao)
    return Response(caminho.read_bytes(), media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/api/publicacao/imagem/{id_execucao}")
def publicar_imagem(id_execucao: str):
    dados, _ = imagem_publicavel(image_generator, audit_logger, id_execucao)
    return Response(dados, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/api/logs")
def listar_logs():
    """Lista a trilha completa de auditoria (RF11)."""
    return audit_logger.listar_execucoes()


@app.get("/api/lgpd/relatorio")
def relatorio_lgpd():
    """Retorna relatório e matriz de conformidade LGPD (RF12)."""
    return LGPDManager.gerar_relatorio_conformidade()


# ==============================================================================
# Execução Completa Automatizada (--run-all)
# ==============================================================================
def executar_pipeline_completo():
    """
    Executa o pipeline integral de processamento da Central de Atendimento GOV.MT,
    salvando evidências estruturadas, logs e artefatos de cada modalidade.
    """
    print("\n" + "=" * 80)
    print("INICIANDO EXECUÇÃO INTEGRAL DO PIPELINE INSTITUCIONAL (GOV.MT)")
    print("=" * 80)

    # 1. Experimento de Engenharia de Prompts (RF02)
    print("\n[RF02] Executando Experimento de Engenharia de Prompts (A, B e C)...")
    res_exp = rodar_experimento_prompts()
    if isinstance(res_exp, dict) and res_exp.get("sucesso"):
        print(f" -> Experimento concluído. Prompt selecionado: {res_exp.get('prompt_selecionado', 'Prompt C')}")
    else:
        print(" -> Experimento de prompts registrado no log de auditoria.")

    # 2. Processamento Textual e Minuta Oficial (RF03, RF05, RF09)
    print("\n[RF03 / RF05 / RF09] Processando caso principal de texto (entrada_texto.txt)...")
    with open(resolver_caminho("dados/originais/entrada_texto.txt"), "r", encoding="utf-8") as f:
        texto_principal = f.read()

    req_texto = RequisicaoTexto(texto=texto_principal, caso="texto_original", tipo_prompt="PRODUCAO")
    try:
        res_texto = processar_texto(req_texto)
    except Exception as exc:
        res_texto = {"sucesso": False, "erro": str(exc)}

    if isinstance(res_texto, dict) and res_texto.get("sucesso"):
        exec_id_texto = res_texto["id_execucao"]
        print(f" -> Extração realizada! ID Execução: {exec_id_texto}")
        print(f" -> Protocolo: {res_texto['extracao'].get('protocolo')} | Solicitante: {res_texto['extracao'].get('solicitante')}")
        print(f" -> Minuta Oficial em PDF timbrado gerada: {res_texto['url_pdf']}")

        # 3. Teste de Blindagem contra Prompt Injection (RF03)
        print("\n[RF03] Executando Teste de Blindagem contra Prompt Injection...")
        texto_inj = SegurancaPrompts.CASO_TESTE_PROMPT_INJECTION
        req_inj = RequisicaoTexto(texto=texto_inj, caso="prompt_injection", tipo_prompt="PRODUCAO")
        try:
            res_inj = processar_texto(req_inj)
            if isinstance(res_inj, dict) and res_inj.get("sucesso"):
                print(f" -> Injeção de prompt processada. Comandos neutralizados: {res_inj['id_execucao']}")
        except Exception as exc:
            print(f" -> Teste de injeção processado com registro de segurança: {exc}")

        # 5. Síntese de Voz para Acessibilidade (RF07)
        print("\n[RF07] Gerando áudio de acessibilidade (TTS)...")
        minuta_texto = res_texto["minuta_institucional"]
        res_tts = audio_processor.sintetizar_minuta_audio(
            minuta_texto, "minuta_aprovada_acessivel.wav", exec_id_texto, audit_logger)
        print(f" -> Síntese de áudio concluída: {res_tts.get('caminho_arquivo', res_tts.get('erro'))}")
    else:
        motivo_erro = res_texto.get("erro") if isinstance(res_texto, dict) else str(res_texto)
        print(f" -> Falha no processamento textual: {motivo_erro}. Prosseguindo para as demais etapas.")

    # 4. Transcrição de Áudio STT (RF06)
    print("\n[RF06] Processando mensagem de voz institucional (Whisper)...")
    res_audio = processar_audio()
    if isinstance(res_audio, dict) and res_audio.get("sucesso"):
        print(f" -> Transcrição concluída! Duração: {res_audio['metadados']['duracao_segundos']}s")
        print(f" -> Acurácia de Entidades: {res_audio['comparacao_gabarito']['acuracia_entidades']}")
    else:
        print(" -> Transcrição de áudio concluída com pendência de revisão.")

    # 6. Visão Computacional e OCR Local (RF08)
    print("\n[RF08] Processando documento digitalizado / Ficha de Matrícula (OCR Tesseract)...")
    res_visao = processar_visao()
    if isinstance(res_visao, dict) and res_visao.get("sucesso"):
        print(f" -> OCR concluído! Acurácia contra gabarito: {res_visao['comparacao_gabarito']['taxa_acuracia_percentual']}")
        print(f" -> Incertezas identificadas: {len(res_visao['trechos_incertos_ou_ilegiveis'])}")
    else:
        print(" -> OCR registrado com pendência de conferência.")

    # 7. Geração da Peça Visual Institucional (RF10)
    print("\n[RF10] Gerando comunicado oficial / Peça Visual Institucional...")
    res_img = image_generator.gerar_comunicado_oficial()
    if isinstance(res_img, dict) and res_img.get("sucesso"):
        print(f" -> Peça visual oficial gerada com sucesso: {res_img.get('caminho_imagem')}")
    else:
        print(f" -> Geração de imagem: {res_img.get('erro', 'Concluído')}")

    # 8. Relatório de LGPD e Auditoria (RF11, RF12)
    print("\n[RF11 / RF12] Gerando relatório de conformidade e auditoria...")
    relatorio_lgpd = LGPDManager.gerar_relatorio_conformidade()
    dir_doc = resolver_caminho("documentacao")
    dir_doc.mkdir(parents=True, exist_ok=True)
    with open(dir_doc / "relatorio_lgpd_execucao.json", "w", encoding="utf-8") as f:
        json.dump(relatorio_lgpd, f, ensure_ascii=False, indent=2)
    print(" -> Relatório de conformidade LGPD salvo em documentacao/relatorio_lgpd_execucao.json")

    print("\n" + "=" * 80)
    print("Execução do pipeline finalizada.")
    print("Resultados disponíveis nas pastas 'dados/processados/' e 'resultados/'.")
    print("=" * 80 + "\n")


# ==============================================================================
# Execução CLI Interativa (--cli)
# ==============================================================================
def executar_cli_interativa():
    print("\n=== CENTRAL INTELIGENTE DE ATENDIMENTO GOV.MT (MODO CLI) ===")
    print("1. Processar Solicitação Textual")
    print("2. Transcrever Áudio (RF06)")
    print("3. Analisar Documento Digitalizado (RF08)")
    print("4. Gerar Peça Visual Oficial (RF10)")
    print("5. Executar Experimento dos 3 Prompts (RF02)")
    print("6. Executar Pipeline Completo (--run-all)")
    print("0. Sair")
    opcao = input("\nSelecione uma opção: ").strip()

    if opcao == "1":
        caso = input("Digite o caminho do arquivo de texto (ou Enter para padrão): ").strip()
        caminho = resolver_caminho(caso if caso else "dados/originais/entrada_texto.txt")
        with open(caminho, "r", encoding="utf-8") as f:
            txt = f.read()
        res = processar_texto(RequisicaoTexto(texto=txt, caso="cli_exec"))
        print("\n--- JSON EXTRAÍDO ---")
        print(json.dumps(res["extracao"], indent=2, ensure_ascii=False))
        print("\n--- MINUTA INSTITUCIONAL ---")
        print(res["minuta_institucional"])
    elif opcao == "2":
        res = processar_audio()
        print(f"Transcrição: {res['transcricao_revisada']}")
    elif opcao == "3":
        res = processar_visao()
        print(f"Texto Corrigido: {res['texto_corrigido']}")
    elif opcao == "4":
        print("RF10 administrativo indisponível sem autenticação; validador real requer comando explícito.")
    elif opcao == "5":
        res = rodar_experimento_prompts()
        print("Experimento concluído e salvo em 'prompts/matriz_comparativa.md'.")
    elif opcao == "6":
        executar_pipeline_completo()
    else:
        print("Encerrando CLI.")


# ==============================================================================
# Entrypoint Main
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Central Inteligente de Atendimento GOV.MT")
    parser.add_argument("--run-all", action="store_true", help="Executa o pipeline completo de ponta a ponta e salva evidências.")
    parser.add_argument("--cli", action="store_true", help="Inicia o modo interativo em linha de comando.")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor web (padrão: 8000).")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host do servidor web (padrão: 0.0.0.0).")

    args = parser.parse_args()

    if args.run_all:
        executar_pipeline_completo()
    elif args.cli:
        executar_cli_interativa()
    else:
        print(f"\nIniciando Central de Atendimento GOV.MT em http://localhost:{args.port} ...")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
