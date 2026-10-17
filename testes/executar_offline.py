"""Executa a suíte em cópia temporária, sem alterar evidências ou acessar provedores."""
import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

def main():
    raiz = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(raiz))
    os.environ["EXECUTION_MODE"] = "mock"
    os.environ["OPENROUTER_ENABLED"] = "false"
    os.environ.pop("RF08_REAL", None)
    # Não carrega credenciais do projeto original.
    os.environ.pop("HF_TOKEN", None)
    os.environ.pop("OPENROUTER_API_KEY", None)
    from src.audio import AudioProcessor
    import src
    async def sem_tts(*args, **kwargs):
        raise RuntimeError("TTS externo bloqueado na suíte")
    with tempfile.TemporaryDirectory(prefix="ficdev_integracao_testes_") as tmp:
        destino = Path(tmp)
        for nome in ["config.json", "pytest.ini", ".env.example"]:
            shutil.copy2(raiz / nome, destino / nome)
        for nome in ["testes", "dados/originais", "dados/gabaritos", "resultados/imagens", "src/web", "prompts"]:
            shutil.copytree(raiz / nome, destino / nome)
        anterior, base = Path.cwd(), src.BASE_DIR
        os.chdir(destino)
        src.BASE_DIR = destino
        try:
            with patch.object(AudioProcessor, "_sintetizar_edge_tts", sem_tts), patch(
                "subprocess.Popen", side_effect=RuntimeError("Processo externo bloqueado")), patch(
                "requests.sessions.Session.request", side_effect=RuntimeError("HTTP externo bloqueado")), patch(
                "httpx.Client.send", side_effect=RuntimeError("HTTP SDK externo bloqueado")):
                return pytest.main(["-p", "no:cacheprovider", "testes", "-q", "--tb=short"])
        finally:
            os.chdir(anterior)
            src.BASE_DIR = base

if __name__ == "__main__":
    raise SystemExit(main())
