"""Regressões adversariais: dados sintéticos, arquivos temporários e LLM mockado."""
import json
import hashlib
from pathlib import Path
from unittest.mock import Mock

import pymupdf
import pytest

from src.audit import AuditLogger, QualityEvaluator
from src.audio import AudioProcessor
from src.llm_client import LLMResponse
from src.pdf_generator import gerar_minuta_pdf
from src.text_contract import interpretar_minuta, ContratoTextoInvalido
from testes.test_integracao_main import web, llm, payload_contrato


def test_pdf_longo_nao_perde_corpo_e_nao_inventa_protocolo(tmp_path):
    texto = "INICIOCONFERIVEL " + "Informação fictícia para revisão humana. " * 1200 + " FIMCONFERIVEL"
    p = tmp_path / "longo.pdf"
    gerar_minuta_pdf({}, texto, p, fontes_origem=["dados/originais/entrada_texto.txt"])
    with pymupdf.open(p) as doc:
        extraido = " ".join(pg.get_text() for pg in doc)
        assert len(doc) > 1
        assert "INICIOCONFERIVEL" in extraido and "FIMCONFERIVEL" in extraido
        assert extraido.count("Informação") == extraido.count("fictícia") == 1200
        assert "2026-000142" not in extraido
        assert "Categoria: Atendimento" not in extraido
        assert "dados/originais/entrada_texto.txt" in extraido


def test_auditoria_redige_segredos_aninhados_mas_nao_max_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "segredo-ficticio-auditoria")
    logger = AuditLogger(str(tmp_path))
    ident = logger.registrar_execucao("texto", "fonte", "teste", "teste", "teste",
        {"max_tokens": 4096, "opcoes": [{"api_key": "segredo-ficticio-auditoria"}]},
        {"sucesso": False, "erro": "contém segredo-ficticio-auditoria"}, 0)
    blob = (tmp_path / (ident + ".json")).read_text(encoding="utf-8")
    dado = json.loads(blob)
    assert "segredo-ficticio-auditoria" not in blob
    assert dado["parametros"]["max_tokens"] == 4096
    assert dado["resultado_resumo"]["sucesso"] is False


def test_historico_e_taxa_nao_contam_pendencia_ou_tts_como_aprovacao(tmp_path):
    logger = AuditLogger(str(tmp_path))
    ids = [logger.registrar_execucao("texto", "fonte", "mock", "mock", "teste", {}, {}, 0) for _ in range(3)]
    assert logger.atualizar_decisao_humana(ids[0], "APROVADO", "Conferido", texto_final="Fictício")
    assert logger.atualizar_decisao_humana(ids[1], "CORRIGIDO", "Correção necessária")
    logger.registrar_execucao("tts", "fonte", "mock", "mock", "teste", {}, {}, 0,
        decisao_humana={"status": "APROVADO"})
    assert logger.resumo_revisoes()["taxa_aprovacao_percentual"] == 50
    assert logger.atualizar_decisao_humana(ids[0], "REJEITADO", "Revisão posterior")
    d = json.loads((tmp_path / (ids[0] + ".json")).read_text(encoding="utf-8"))
    assert any(h["status"] == "APROVADO" for h in d["historico_decisoes"])
    assert not logger.obter_aprovacao_texto(ids[0], "Fictício")


@pytest.mark.parametrize("extracao", [{}, {"protocolo": "não localizado"}, {"campo_inventado": "x"}])
def test_schema_producao_incompleto_nao_e_aceito(extracao):
    with pytest.raises(ContratoTextoInvalido):
        interpretar_minuta(json.dumps({"extracao": extracao, "minuta_institucional": "Minuta fictícia"}), schema_completo=True)


@pytest.mark.parametrize("caso,modalidade", [("audio_transcricao", "audio"), ("visao_documento", "visao")])
def test_confirmacao_origem_precede_llm_e_edicao_invalida(web, monkeypatch, caso, modalidade):
    main, pedir = web
    gerar = Mock(return_value=LLMResponse(payload_contrato({}, "Minuta fictícia."), "modelo", "mock", 0, 0, 0, 0, None, "success"))
    monkeypatch.setattr(main.llm_client, "generate", gerar)
    id_origem = main.audit_logger.registrar_execucao(modalidade, "dados/originais/entrada_audio.mp3", "mock", "mock", "teste", {}, {"sucesso": True}, 0)
    texto_confirmado = "Texto fictício conferido\nProtocolo: 2099-000001"
    corpo = {"texto": texto_confirmado, "caso": caso, "id_execucao_origem": id_origem}
    assert pedir("POST", "/api/processar/texto", json=corpo).status_code == 409
    gerar.assert_not_called()
    assert pedir("POST", "/api/revisao/decisao", json={"id_execucao": id_origem, "decisao": "APROVADO",
        "justificativa": "Nomes, protocolos e datas conferidos na fonte fictícia", "texto_final": corpo["texto"]}).status_code == 200
    r = pedir("POST", "/api/processar/texto", json=corpo)
    assert r.status_code == 200
    registro = json.loads((main.audit_logger.log_dir / (r.json()["id_execucao"] + ".json")).read_text(encoding="utf-8"))
    origem = main.resolver_caminho(registro["arquivo_origem"])
    assert origem.read_text(encoding="utf-8") == corpo["texto"]
    assert hashlib.sha256(origem.read_bytes()).hexdigest() == registro["detalhes_completos"]["rastreabilidade"]["sha256_entrada"]
    assert registro["detalhes_completos"]["rastreabilidade"]["id_execucao_origem"] == id_origem
    corpo["texto"] += " alterado"
    assert pedir("POST", "/api/processar/texto", json=corpo).status_code == 409
    assert gerar.call_count == 1
    # Conferir uma fonte não equivale a aprovar uma minuta para TTS.
    assert main.audit_logger.obter_aprovacao_texto(id_origem, texto_confirmado) is None


@pytest.mark.parametrize("url", ["/arquivos/resultados/logs/audit_trail.jsonl", "/arquivos/dados/processados/entrada.json", "/arquivos/dados/originais/segredo.txt"])
def test_download_nao_expoe_logs_ou_dados_arbitrarios(web, url, tmp_path, monkeypatch):
    main, pedir = web
    arquivo = tmp_path / url.removeprefix("/arquivos/")
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text("conteudo ficticio privado que existe", encoding="utf-8")
    monkeypatch.setattr(main, "BASE_DIR", tmp_path)
    rota = next(r for r in main.app.routes if getattr(r, "path", None) == "/arquivos")
    monkeypatch.setattr(rota.app, "directory", str(tmp_path))
    monkeypatch.setattr(rota.app, "all_directories", [str(tmp_path)])
    assert pedir("GET", url).status_code == 404


def test_reexportacao_pdf_preserva_data_e_fontes_conhecidas(web, monkeypatch):
    main, pedir = web
    ident = main.audit_logger.registrar_execucao("texto", "fonte_ficticia.txt", "mock", "mock", "teste", {},
        {"extracao": {"data": "01/01/2099"}, "rastreabilidade": {"fontes": ["fonte_ficticia.txt"]}}, 0)
    gerar = Mock(side_effect=lambda **kw: kw["caminho_saida_pdf"].write_bytes(b"%PDF-teste"))
    monkeypatch.setattr(main, "gerar_minuta_pdf", gerar)
    r = pedir("POST", "/api/minuta/gerar_pdf", json={"texto_minuta": "Minuta fictícia", "id_execucao": ident})
    assert r.status_code == 200
    assert gerar.call_args.kwargs["dados_extracao"]["data"] == "01/01/2099"
    assert gerar.call_args.kwargs["fontes_origem"] == ["fonte_ficticia.txt"]


def test_credencial_na_entrada_bloqueada_antes_do_provedor(web, monkeypatch, tmp_path):
    main, pedir = web
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "credencial-ficticia-para-teste")
    gerar = Mock()
    monkeypatch.setattr(main.llm_client, "generate", gerar)
    assert pedir("POST", "/api/processar/texto", json={"texto": "conteudo credencial-ficticia-para-teste"}).status_code == 422
    gerar.assert_not_called()
    assert not any("credencial-ficticia-para-teste" in p.read_text(encoding="utf-8") for p in tmp_path.rglob("*.txt"))


def test_cli_texto_indisponivel_nao_indexa_jsonresponse(web, monkeypatch, capsys):
    from fastapi.responses import JSONResponse
    main, _ = web
    respostas = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(respostas))
    monkeypatch.setattr(main, "processar_texto", Mock(return_value=JSONResponse(status_code=503, content={"sucesso": False, "erro": "Provedor indisponível"})))
    main.executar_cli_interativa()
    assert "Provedor indisponível" in capsys.readouterr().out


def test_entrypoint_cli_apresenta_http502_sem_sucesso_falso(web, monkeypatch, capsys):
    from fastapi import HTTPException
    import sys
    main, _ = web
    monkeypatch.setattr(sys, "argv", ["src.main", "--run-all"])
    monkeypatch.setattr(main, "executar_pipeline_completo", Mock(side_effect=HTTPException(502, "JSON inválido")))
    main.main()
    assert "HTTP 502" in capsys.readouterr().out


def test_servidor_sem_autenticacao_inicia_somente_no_loopback(web, monkeypatch):
    import sys
    main, _ = web
    monkeypatch.setattr(sys, "argv", ["src.main"])
    subir = Mock()
    monkeypatch.setattr(main.uvicorn, "run", subir)
    main.main()
    assert subir.call_args.kwargs["host"] == "127.0.0.1"


@pytest.mark.parametrize("campo,esperado,obtido,status", [
    ("cpf", "123.456.789-00", "12345678900", "CORRETO"),
    ("cpf", "123.456.789-00", "12345678901", "DIVERGENTE"),
    ("protocolo", "2099-000001", "2099/000001", "CORRETO"),
    ("telefone", "(65) 99999-0000", "65999990000", "CORRETO"),
])
def test_formatacao_equivalente_nao_cria_erro_mas_digito_errado_continua(campo, esperado, obtido, status):
    r = QualityEvaluator.avaliar_extracao({campo: obtido}, {"campos_esperados": {campo: esperado}})
    assert r["comparativo_campos"][0]["status"] == status


def test_texto_editado_nao_herda_referencia_de_outro_caso(web, monkeypatch):
    main, pedir = web
    resposta = LLMResponse(payload_contrato({"solicitante": "Pessoa Nova Fictícia"}, "Minuta fictícia"), "modelo", "mock", 0, 0, 0, 0, None, "success")
    monkeypatch.setattr(main.llm_client, "generate", Mock(return_value=resposta))
    r = pedir("POST", "/api/processar/texto", json={"texto": "Nome: Pessoa Nova Fictícia", "caso": "texto_original"})
    assert r.status_code == 200 and r.json()["avaliacao_gabarito"] is None
    assert "dados/originais/entrada_texto.txt" not in r.json()["fontes_origem"]


def test_ocr_e_extracao_textual_nao_comparam_campos_incompativeis(web, monkeypatch):
    main, pedir = web
    comparacao = {"taxa_acuracia_percentual": "0.0%", "total_campos": 23}
    texto = "Nome: Ana Fictícia"
    ident = main.audit_logger.registrar_execucao("visao", "dados/originais/entrada_pdf-imagem.pdf", "mock", "mock", "teste", {},
        {"sucesso": True, "comparacao_gabarito": comparacao}, 0)
    assert main.audit_logger.atualizar_decisao_humana(ident, "APROVADO", "Conferência sintética de teste", texto_final=texto)
    resposta = LLMResponse(payload_contrato({"solicitante": "Ana Fictícia"}, "Minuta fictícia"), "modelo", "mock", 0, 0, 0, 0, None, "success")
    monkeypatch.setattr(main.llm_client, "generate", Mock(return_value=resposta))
    r = pedir("POST", "/api/processar/texto", json={"texto": texto, "caso": "visao_documento", "id_execucao_origem": ident})
    assert r.status_code == 200 and r.json()["avaliacao_gabarito"] is None
    assert r.json()["avaliacao_origem"] == comparacao


def test_metricas_nativas_nao_sao_substituidas_por_estimativa(llm, monkeypatch):
    from types import SimpleNamespace
    cliente, _ = llm
    cliente.text_provider = "openrouter"
    cliente.openrouter_key = "chave-ficticia"
    monkeypatch.setattr("requests.post", Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {
        "model": "modelo-efetivo", "usage": {"prompt_tokens": 101, "completion_tokens": 23, "cost": .003},
        "choices": [{"message": {"content": "Resposta fictícia"}}]})))
    r = cliente.generate("Entrada")
    assert (r.prompt_tokens, r.completion_tokens, r.total_tokens) == (101, 23, 124)
    assert r.token_usage_source == "provedor" and r.cost_usd == .003


@pytest.mark.parametrize("obtido,ref,erros", [("Ana falou", "Ana falou", 0), ("Ana cantou", "Ana falou", 1),
    ("Ana", "Ana falou", 1), ("Ana falou ontem", "Ana falou", 1)])
def test_stt_compara_texto_referencia_sem_corrigir_dados(obtido, ref, erros):
    r = AudioProcessor._comparar_texto_referencia(obtido, ref)
    assert r["substituicoes"] + r["exclusoes"] + r["insercoes"] == erros
    assert r["wer_percentual"] == 50 * erros
