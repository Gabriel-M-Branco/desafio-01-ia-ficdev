"""
Módulo de Processamento de Áudio: STT (Whisper HF) e TTS com Acessibilidade (RF06, RF07)
"""

import os
import json
import asyncio
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import re
import unicodedata
import wave
import time
import uuid
import base64
import hashlib
import subprocess

from src import resolver_caminho, caminho_relativo
from src.llm_client import LLMClient

MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}


class AudioProcessor:
    """
    Orquestrador para Transcrição de Voz (STT) e Síntese de Voz Institucional (TTS).
    """

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.llm_client = LLMClient(config_path)
        self.stt_model = self.config.get("models", {}).get("stt", "openai/whisper-large-v3-turbo")
        if os.getenv("STT_PROVIDER", "huggingface").strip().lower() == "local":
            self.stt_model = "small"
        self.tts_voice = self.config.get("models", {}).get("tts_voice", "pt-BR-AntonioNeural")
        self.audios_dir = resolver_caminho(self.config.get("paths", {}).get("resultados_audios", "resultados/audios"))
        self.audios_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            p = resolver_caminho(config_path)
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def validar_arquivo_audio(self, caminho_audio: str) -> Tuple[bool, str]:
        """Valida arquivo, extensão, tamanho e cabeçalho/duração legíveis."""
        path = resolver_caminho(caminho_audio)
        try:
            if not path.is_file():
                return False, "Arquivo de áudio não encontrado."
            if path.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
                return False, "Formato de áudio não permitido."
            if not 0 < path.stat().st_size <= MAX_AUDIO_SIZE_BYTES:
                return False, "áudio vazio ou maior que 25 MB."
            self.extrair_metadados_audio(str(path))
        except (OSError, ValueError, ImportError):
            return False, "áudio ilegível, inválido ou dependência de leitura indisponível."
        return True, "Arquivo de áudio válido."

    def extrair_metadados_audio(self, caminho_audio: str) -> Dict[str, Any]:
        path = resolver_caminho(caminho_audio)
        if path.suffix.lower() == ".wav":
            try:
                with wave.open(str(path), "rb") as audio:
                    duracao = audio.getnframes() / audio.getframerate()
            except (wave.Error, EOFError, ZeroDivisionError) as exc:
                raise ValueError("WAV inválido") from exc
        else:
            import mutagen
            try:
                audio = mutagen.File(str(path))
                duracao = audio.info.length if audio is not None and audio.info is not None else 0
            except Exception as exc:
                raise ValueError("áudio inválido") from exc
        if duracao <= 0:
            raise ValueError("Duração de áudio inválida")
        return {
            "arquivo": path.name,
            "duracao_segundos": round(duracao, 3),
            "tamanho_bytes": path.stat().st_size,
            "modelo_stt": self.stt_model,
            # O endpoint STT não garante detecção de idioma; não presumir português.
            "idioma_detectado": "não localizado",
        }

    def _transcrever_local(self, path: Path) -> Dict[str, Any]:
        """Usa somente modelo previamente baixado; nunca baixa nem aciona API."""
        from faster_whisper import WhisperModel
        model = WhisperModel("small", device="cpu", compute_type="int8", local_files_only=True)
        segmentos, info = model.transcribe(str(path), language="pt")
        # A inferência é lazy: consumir dentro do tratamento de erros do chamador.
        return {"text": "".join(segmento.text for segmento in segmentos),
                "language": info.language}

    def transcrever_audio(self, caminho_audio: str) -> Dict[str, Any]:
        """STT real; indisponibilidade nunca produz transcrição simulada."""
        valido, mensagem = self.validar_arquivo_audio(caminho_audio)
        if not valido:
            return {"sucesso": False, "erro": mensagem, "codigo_erro": "arquivo_invalido"}
        provider = os.getenv("STT_PROVIDER", "huggingface").strip().lower()
        if provider not in {"local", "huggingface"}:
            return {"sucesso": False, "erro": "STT_PROVIDER deve ser local ou huggingface.",
                    "codigo_erro": "provedor_invalido"}
        token = os.getenv("HF_TOKEN", "").strip()
        if provider == "huggingface" and (os.getenv("EXECUTION_MODE", "auto").lower() == "mock" or not token):
            return {"sucesso": False, "erro": "STT real requer HF_TOKEN e modo diferente de mock.",
                    "codigo_erro": "stt_indisponivel"}
        path = resolver_caminho(caminho_audio)
        inicio = time.perf_counter()
        try:
            if provider == "local":
                resultado = self._transcrever_local(path)
            else:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=token, timeout=self.config.get(
                    "generation_params", {}).get("timeout_seconds", 30))
                resultado = client.automatic_speech_recognition(str(path), model=self.stt_model)
            bruta = resultado.get("text") if isinstance(resultado, dict) else resultado.text
            if not isinstance(bruta, str) or not bruta.strip():
                return {"sucesso": False, "erro": "Provedor retornou transcrição vazia.",
                        "codigo_erro": "resposta_vazia"}
            metadados = self.extrair_metadados_audio(str(path))
            if provider == "local":
                metadados.update(modelo_stt="small", dispositivo="cpu", compute_type="int8",
                                 idioma_configurado="pt")
            idioma = resultado.get("language") if isinstance(resultado, dict) else getattr(resultado, "language", None)
            if isinstance(idioma, str) and idioma.strip():
                metadados["idioma_detectado"] = idioma.strip()
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if provider == "local" and isinstance(exc, FileNotFoundError):
                codigo = "modelo_local_indisponivel"
            elif status in (401, 403):
                codigo = "autenticacao"
            elif status == 429:
                codigo = "limite_requisicoes"
            elif "timeout" in type(exc).__name__.lower() or isinstance(exc, TimeoutError):
                codigo = "timeout"
            elif isinstance(exc, ImportError):
                codigo = "dependencia_ausente"
            else:
                codigo = "falha_provedor"
            # Não propagar mensagens externas que possam conter credenciais.
            return {"sucesso": False, "erro": "Não foi possível concluir o STT.", "codigo_erro": codigo}
        revisada = re.sub(r"\s+", " ", bruta).strip()
        return {
            "sucesso": True, "arquivo_audio": caminho_relativo(path), "metadados": metadados,
            "transcricao_bruta": bruta, "transcricao_revisada": revisada,
            "revisao_aplicada": "Normalização de espaços; conteúdo pendente de revisão humana.",
            "origem_processamento": "local" if provider == "local" else "api_remota",
            "provedor": "faster-whisper" if provider == "local" else "HuggingFace",
            "tempo_processamento_segundos": round(time.perf_counter() - inicio, 3),
            "exige_confirmacao_humana": True,
            "comparacao_gabarito": self.comparar_com_gabarito(bruta),
        }

    def processar_com_auditoria(self, audit_logger) -> Dict[str, Any]:
        """Transcreve, persiste o resultado RF06 e registra o provedor efetivo."""
        inicio = time.perf_counter()
        caminho = resolver_caminho("dados/originais/entrada_audio.mp3")
        resultado = self.transcrever_audio(str(caminho))
        if resultado.get("sucesso"):
            diretorio = resolver_caminho(self.config.get("paths", {}).get(
                "dados_processados", "dados/processados"))
            arquivo = diretorio / f"transcricao_audio_{uuid.uuid4().hex}.json"
            try:
                diretorio.mkdir(parents=True, exist_ok=True)
                resultado["arquivo_transcricao"] = caminho_relativo(arquivo)
                arquivo.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                resultado.pop("arquivo_transcricao", None)
                resultado.update(sucesso=False, codigo_erro="falha_persistencia",
                                 erro="Não foi possível salvar a transcrição.")
        provider = resultado.get("provedor") or (
            "faster-whisper" if os.getenv("STT_PROVIDER", "huggingface").strip().lower() == "local"
            else "HuggingFace")
        exec_id = audit_logger.registrar_execucao(
            modalidade="audio",
            arquivo_origem="dados/originais/entrada_audio.mp3",
            provedor=provider,
            modelo=resultado.get("metadados", {}).get("modelo_stt", self.stt_model),
            versao_prompt="N/A (STT Direto)",
            parametros={},
            resultado=resultado,
            duracao_segundos=time.perf_counter() - inicio,
            erros=[] if resultado.get("sucesso") else [resultado.get("codigo_erro", "falha_stt")],
        )
        resultado["id_execucao"] = exec_id
        return resultado

    @staticmethod
    def _normalizar_comparacao(texto: str) -> str:
        texto = "".join(c for c in unicodedata.normalize("NFKD", texto.casefold())
                        if not unicodedata.combining(c))
        meses = "janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro".split()
        for numero, mes in enumerate(meses, 1):
            texto = re.sub(r"\b(\d{1,2}) de " + mes + r" de (\d{4})\b",
                           lambda m: f"{int(m[1]):02d}/{numero:02d}/{m[2]}", texto)
        texto = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
                       lambda m: f"{int(m[1]):02d}/{int(m[2]):02d}/{m[3]}", texto)
        return re.sub(r"\s+", " ", texto).strip()

    def comparar_com_gabarito(self, transcricao: str) -> Dict[str, Any]:
        path = resolver_caminho("dados/gabaritos/gabarito_audio.json")
        try:
            gabarito = json.loads(path.read_text(encoding="utf-8"))
            entidades = gabarito["entidades_criticas"]
            if not isinstance(entidades, dict) or not entidades:
                raise ValueError("Gabarito vazio")
        except (OSError, ValueError, KeyError):
            return {"status": "gabarito_indisponivel", "todos_campos_criticos_conferidos": False,
                    "acuracia_entidades": "0/0", "detalhes": {}}
        texto = self._normalizar_comparacao(transcricao)
        detalhes = {}
        for campo, valor in entidades.items():
            esperado = self._normalizar_comparacao(str(valor))
            localizado = bool(esperado) and bool(re.search(r"(?<!\w)" + re.escape(esperado) + r"(?!\w)", texto))
            detalhes[campo] = {"valor_esperado": valor, "localizado_na_transcricao": localizado}
        erros = [campo for campo, item in detalhes.items() if not item["localizado_na_transcricao"]]
        return {"todos_campos_criticos_conferidos": not erros, "detalhes": detalhes,
                "campos_divergentes_ou_ausentes": erros,
                "acuracia_entidades": f"{len(detalhes)-len(erros)}/{len(detalhes)}",
                "confirmacao_humana_pendente": True}

    def preparar_texto_para_acessibilidade(self, texto_minuta: str) -> str:
        aviso = "Atenção: informação pendente de localização no sistema."
        return re.sub(r"n[ãa]o localizado", aviso, texto_minuta, flags=re.IGNORECASE)

    async def _sintetizar_edge_tts(self, texto: str, caminho_saida: str) -> bool:
        import edge_tts
        await edge_tts.Communicate(texto, self.tts_voice).save(caminho_saida)
        return True

    def _sintetizar_sapi5(self, texto, caminho_saida):
        """SAPI5 local: entrada JSON evita interpolar texto em código PowerShell."""
        if os.name != "nt":
            raise RuntimeError("SAPI5 requer Windows.")
        script = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
$voice = New-Object -ComObject SAPI.SpVoice
$tokens = $voice.GetVoices('Language=416')
$selected = $null
for ($i = 0; $i -lt $tokens.Count; $i++) {
    $token = $tokens.Item($i)
    if ($token.GetDescription().IndexOf($data.voz, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
        $selected = $token
        break
    }
}
if ($null -eq $selected) { throw 'Voz pt-BR solicitada indisponivel.' }
$voice.Voice = $selected
$voice.Rate = 0
$voice.Volume = 100
$stream = New-Object -ComObject SAPI.SpFileStream
try {
    $stream.Open($data.caminho, 3, $false)
    $voice.AudioOutputStream = $stream
    [void]$voice.Speak($data.texto)
} finally {
    $stream.Close()
}
@{ voz = $selected.GetDescription() } | ConvertTo-Json -Compress
"""
        executavel = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        resposta = subprocess.run(
            [str(executavel), "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(script.encode("utf-16le")).decode("ascii")],
            input=json.dumps({"texto": texto, "caminho": caminho_saida,
                              "voz": os.getenv("TTS_LOCAL_VOICE", "Microsoft Maria")}).encode("ascii"),
            capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if resposta.returncode:
            raise RuntimeError("Falha no SAPI5.")
        return json.loads(resposta.stdout.decode("utf-8-sig"))["voz"]

    @staticmethod
    def _validar_audio_tts(path, provider):
        if not path.is_file() or path.stat().st_size <= 44:
            raise ValueError("Áudio ausente ou vazio.")
        if provider == "sapi5":
            with wave.open(str(path), "rb") as wav:
                frames, rate = wav.getnframes(), wav.getframerate()
                esperado = frames * wav.getnchannels() * wav.getsampwidth()
                if frames <= 0 or rate <= 0 or len(wav.readframes(frames)) != esperado:
                    raise ValueError("WAV incompleto.")
                return frames / rate
        from mutagen.mp3 import MP3
        duracao = MP3(str(path)).info.length
        if duracao <= 0:
            raise ValueError("MP3 inválido.")
        return duracao

    def sintetizar_minuta_audio(self, texto_minuta: str, nome_arquivo_saida: str = "minuta_acessivel.mp3",
                               id_execucao: Optional[str] = None, audit_logger=None) -> Dict[str, Any]:
        """Exige aprovação persistida exata; nunca gera áudio simulado."""
        from src.audit import AuditLogger
        logger = audit_logger or AuditLogger(self.config.get("paths", {}).get("resultados_logs", "resultados/logs"))
        inicio = time.perf_counter()
        provider = os.getenv("TTS_PROVIDER", "sapi5").strip().lower()
        resultado = {"sucesso": False, "provedor": provider, "metodo": provider,
                     "id_execucao_aprovacao": id_execucao}
        caminho = None

        def registrar():
            resultado["tempo_processamento_segundos"] = time.perf_counter() - inicio
            try:
                identificador = logger.registrar_execucao(
                    modalidade="tts", arquivo_origem=str(logger.log_dir / f"{id_execucao}.json") if id_execucao else "",
                    provedor=provider, modelo=resultado.get("voz_utilizada", "não localizado"),
                    versao_prompt="N/A (síntese de texto aprovado)",
                    parametros={"id_execucao_aprovacao": id_execucao,
                                "hash_texto_aprovado": resultado.get("hash_texto_aprovado")},
                    resultado=resultado, duracao_segundos=resultado["tempo_processamento_segundos"],
                    decisao_humana=aprovacao if resultado["sucesso"] else None,
                    erros=[] if resultado["sucesso"] else [resultado.get("codigo_erro", "falha_tts")])
                resultado["id_execucao"] = identificador
                resultado["caminho_metadados"] = caminho_relativo(logger.log_dir / f"{identificador}.json")
            except OSError:
                if caminho and caminho.exists():
                    caminho.unlink()
                resultado.pop("caminho_arquivo", None)
                resultado.update(sucesso=False, codigo_erro="falha_auditoria",
                                 erro="Não foi possível registrar a síntese.")
            return resultado

        aprovacao = logger.obter_aprovacao_texto(id_execucao, texto_minuta) if isinstance(texto_minuta, str) and texto_minuta.strip() else None
        if not aprovacao:
            resultado.update(codigo_erro="texto_nao_aprovado",
                             erro="Aprove o texto exato antes de gerar o áudio.")
            return registrar()
        if provider not in {"sapi5", "edge-tts"}:
            resultado.update(codigo_erro="provedor_invalido", erro="TTS_PROVIDER deve ser sapi5 ou edge-tts.")
            return registrar()
        try:
            nome = Path(nome_arquivo_saida)
            if nome.name != nome_arquivo_saida or "/" in nome_arquivo_saida or "\\" in nome_arquivo_saida:
                raise ValueError("Nome de saída inválido.")
            extensao = ".wav" if provider == "sapi5" else ".mp3"
            caminho = (self.audios_dir / f"{nome.stem}_{uuid.uuid4().hex}{extensao}").resolve()
            if not caminho.is_relative_to(self.audios_dir.resolve()):
                raise ValueError("Caminho inválido.")
            caminho.parent.mkdir(parents=True, exist_ok=True)
            acessivel = self.preparar_texto_para_acessibilidade(texto_minuta)
            if provider == "sapi5":
                voz = self._sintetizar_sapi5(acessivel, str(caminho))
            else:
                asyncio.run(self._sintetizar_edge_tts(acessivel, str(caminho)))
                voz = self.tts_voice
            duracao = self._validar_audio_tts(caminho, provider)
            atual = logger.obter_aprovacao_texto(id_execucao, texto_minuta)
            if not atual or atual["id_aprovacao"] != aprovacao["id_aprovacao"]:
                raise ValueError("Aprovação revogada durante a síntese.")
            resultado.update(
                sucesso=True, caminho_arquivo=caminho_relativo(caminho), voz_utilizada=voz,
                formato=extensao[1:], tamanho_bytes=caminho.stat().st_size, duracao_segundos=duracao,
                id_aprovacao=aprovacao["id_aprovacao"], hash_texto_aprovado=logger.hash_texto(texto_minuta),
                texto_sintetizado=acessivel, hash_texto_sintetizado=logger.hash_texto(acessivel),
                sha256_audio=hashlib.sha256(caminho.read_bytes()).hexdigest(),
                aviso_acessibilidade_aplicado=acessivel != texto_minuta,
                impacto_acessibilidade="Leitura da minuta aprovada com aviso explícito sobre informações pendentes.")
        except Exception as exc:
            if caminho and caminho.exists():
                caminho.unlink()
            resultado.update(sucesso=False, codigo_erro="timeout" if isinstance(exc, subprocess.TimeoutExpired) else "falha_tts",
                             erro="Não foi possível gerar e validar o áudio institucional.")
        return registrar()
