"""Regressões da combinação final; transportes reais não são usados."""
from unittest.mock import Mock

import pytest

from src.pdf_generator import normalizar_caracteres_pdf
from testes.test_integracao_main import web


@pytest.mark.parametrize("url,tipo", [("/favicon.ico", "image/x-icon"), ("/favicon.png", "image/png")])
def test_favicon_disponivel_sem_cache(web, url, tipo):
    _, pedir = web
    resposta = pedir("GET", url)
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == tipo
    assert "no-store" in resposta.headers["cache-control"]


def test_revisao_desconhecida_nao_inventa_execucao(web):
    main, pedir = web
    ident = "EXEC_INEXISTENTE_MERGE"
    r = pedir("POST", "/api/revisao/decisao", json={"id_execucao": ident,
        "decisao": "APROVADO", "justificativa": "Fixture de segurança", "texto_final": "Fictício"})
    assert r.status_code == 404
    assert not (main.audit_logger.log_dir / (ident + ".json")).exists()


def test_config_imagem_nao_habilita_administracao(web):
    main, pedir = web
    r = pedir("GET", "/api/config")
    assert r.status_code == 200
    assert r.json()["imagem"]["provedor"] == main.image_generator.image_provider
    assert r.json()["rf10_administrativo_habilitado"] is False


def test_normalizacao_pdf_preserva_pergunta_e_nao_reescreve_fatos():
    texto = 'Matrícula — “informação”? Secretaria de Educação; protocolo 2099-000001.'
    obtido = normalizar_caracteres_pdf(texto)
    assert obtido == 'Matrícula  -  "informação"? Secretaria de Educação; protocolo 2099-000001.'


def test_stt_openrouter_nao_reintroduzido(web, monkeypatch):
    main, _ = web
    monkeypatch.setenv("STT_PROVIDER", "openrouter")
    monkeypatch.setattr(main.audio_processor, "validar_arquivo_audio", Mock(return_value=(True, "")))
    resultado = main.audio_processor.transcrever_audio("fixture.mp3")
    assert resultado["sucesso"] is False
    assert resultado["codigo_erro"] == "provedor_invalido"
