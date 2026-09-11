"""Servidor local de voz do mod Mobs Falantes.

Tudo roda na sua maquina (so baixa os modelos na primeira vez):
  - STT (voz -> texto): faster-whisper, entende ~100 idiomas     POST /stt?lang=pt_br   corpo = WAV
  - TTS (texto -> voz): Piper, vozes escolhidas automaticamente   POST /tts               corpo = JSON
    pelo catalogo oficial (56 idiomas) no idioma de cada jogador
  - POST /prepare?lang=xx   baixa as vozes de um idioma em segundo plano (o mod chama ao entrar no mundo)
  - GET  /languages         idiomas com voz
  - GET  /health            estado do servidor

O /tts devolve PCM 16 bits mono 48 kHz (formato do Simple Voice Chat), ou WAV com "format": "wav".
"""

import argparse
import io
import json
import logging
import threading
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from piper import PiperVoice, SynthesisConfig

LOG = logging.getLogger("voz")
OUT_RATE = 48000
REPO = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
CATALOG_MAX_AGE = 7 * 24 * 3600
QUALITY_RANK = {"medium": 0, "high": 1, "low": 2, "x_low": 3}
MAX_SINGLE_MODELS = 4   # vozes de 1 locutor por idioma
MAX_SPEAKERS = 8        # locutores usados de um modelo com varios locutores
# Codigos de idioma do Minecraft que o Piper chama diferente
FAMILY_ALIASES = {"nb": "no", "nn": "no"}

# Ajuda o Whisper a reconhecer palavras do jogo.
STT_HINTS = {
    "pt": "Conversa no Minecraft com um aldeão, zumbi, creeper, esqueleto, porco, vaca, lobo, gato.",
    "en": "A Minecraft conversation with a villager, zombie, creeper, skeleton, pig, cow, wolf, cat.",
    "es": "Una conversación en Minecraft con un aldeano, zombi, creeper, esqueleto, cerdo, vaca, lobo.",
}

# Frases que o Whisper costuma "inventar" quando so ha silencio/ruido.
STT_HALLUCINATIONS = (
    "amara.org", "legendas pela comunidade", "obrigado por assistir", "inscreva-se",
    "thanks for watching", "subtitles by", "subtítulos realizados",
)


class NoVoiceForLanguage(Exception):
    pass


def parse_lang(lang: str) -> tuple[str, str]:
    parts = (lang or "").lower().replace("-", "_").split("_")
    family = FAMILY_ALIASES.get(parts[0], parts[0])
    region = parts[1].upper() if len(parts) > 1 else ""
    return family, region


def download(url: str, dest: Path) -> None:
    part = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(url, timeout=60) as response, open(part, "wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    part.replace(dest)


class Catalog:
    """Catalogo oficial de vozes do Piper (voices.json), guardado em cache por 7 dias."""

    def __init__(self, cache: Path):
        self.cache = cache
        self.voices: dict = {}

    def load(self) -> None:
        fresh = self.cache.exists() and time.time() - self.cache.stat().st_mtime < CATALOG_MAX_AGE
        if not fresh:
            try:
                download(REPO + "voices.json", self.cache)
            except Exception as e:
                LOG.warning("Nao consegui atualizar o catalogo de vozes (%s); usando o cache", e)
        if self.cache.exists():
            self.voices = json.loads(self.cache.read_text("utf-8"))
        LOG.info("Catalogo do Piper: %d vozes em %d idiomas", len(self.voices), len(self.languages()))

    def languages(self) -> list[str]:
        return sorted({v["language"]["code"] for v in self.voices.values()})

    def slots(self, lang: str) -> list[tuple[str, int | None]]:
        """Lista estavel de (modelo, locutor) para um idioma. Cada mob usa sempre o mesmo indice."""
        family, region = parse_lang(lang)
        pool = [v for v in self.voices.values() if v["language"]["family"] == family]
        # Mesmo pais primeiro (pt_BR antes de pt_PT), depois qualidade media (melhor custo/beneficio).
        pool.sort(key=lambda v: (v["language"]["region"] != region, QUALITY_RANK.get(v["quality"], 9), v["key"]))
        singles = [v for v in pool if v["num_speakers"] == 1][:MAX_SINGLE_MODELS]
        multi = next((v for v in pool if v["num_speakers"] > 1), None)
        slots: list[tuple[str, int | None]] = [(v["key"], None) for v in singles]
        if multi:
            n = multi["num_speakers"]
            count = min(MAX_SPEAKERS, n)
            slots += [(multi["key"], i * n // count) for i in range(count)]
        return slots

    def files(self, key: str) -> list[str]:
        return list(self.voices[key]["files"])


class VoiceBank:
    def __init__(self, voices_dir: Path, catalog: Catalog):
        self.dir = voices_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.catalog = catalog
        self.loaded: dict[str, PiperVoice] = {}
        self.locks: dict[str, threading.Lock] = {}
        self.locks_guard = threading.Lock()

    def _lock(self, key: str) -> threading.Lock:
        with self.locks_guard:
            return self.locks.setdefault(key, threading.Lock())

    def get(self, key: str) -> PiperVoice:
        voice = self.loaded.get(key)
        if voice is not None:
            return voice
        with self._lock(key):
            if key in self.loaded:
                return self.loaded[key]
            model = self.dir / f"{key}.onnx"
            config = self.dir / f"{key}.onnx.json"
            if not (model.exists() and config.exists()):
                LOG.info("Baixando voz %s ...", key)
                for path in self.catalog.files(key):
                    url = REPO + urllib.parse.quote(path)
                    if path.endswith(".onnx"):
                        download(url, model)
                    elif path.endswith(".onnx.json"):
                        download(url, config)
            voice = PiperVoice.load(model, config_path=config)
            self.loaded[key] = voice
            LOG.info("Voz carregada: %s", key)
            return voice

    def prepare(self, lang: str) -> None:
        for key in dict.fromkeys(k for k, _ in self.catalog.slots(lang)):
            try:
                self.get(key)
            except Exception:
                LOG.exception("Falha ao preparar a voz %s", key)

    def synthesize(self, text: str, lang: str, voice_idx: int, pitch: float, speed: float) -> np.ndarray:
        slots = self.catalog.slots(lang)
        if not slots:
            raise NoVoiceForLanguage(lang)
        key, speaker = slots[voice_idx % len(slots)]
        voice = self.get(key)
        pitch = float(np.clip(pitch, 0.5, 2.0))
        speed = float(np.clip(speed, 0.5, 2.0))

        # Truque para mudar o tom sem mudar a duracao: gera a fala mais lenta
        # (length_scale * pitch) e depois "acelera" reamostrando pelo mesmo fator.
        cfg = SynthesisConfig(speaker_id=speaker, length_scale=voice.config.length_scale * pitch / speed)
        sr = voice.config.sample_rate
        gap = np.zeros(int(sr * 0.12), dtype=np.float32)
        parts = []
        for chunk in voice.synthesize(text, cfg):
            parts.append(chunk.audio_int16_array.astype(np.float32) / 32768.0)
            parts.append(gap)
        if not parts:
            return np.zeros(0, dtype="<i2")
        audio = np.concatenate(parts)

        out_len = max(1, int(len(audio) * OUT_RATE / (sr * pitch)))
        audio = np.interp(np.linspace(0, len(audio) - 1, out_len), np.arange(len(audio)), audio)
        peak = float(np.max(np.abs(audio))) or 1.0
        audio = audio * (0.9 / peak)
        return (audio * 32767).astype("<i2")


class Stt:
    def __init__(self, model_name: str, threads: int):
        self.model_name = model_name
        self.threads = threads
        self.model = None
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            if self.model is None:
                from faster_whisper import WhisperModel

                LOG.info("Carregando Whisper '%s' (a primeira vez baixa o modelo) ...", self.model_name)
                self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8",
                                          cpu_threads=self.threads)
                LOG.info("Whisper pronto.")
            return self.model

    def _run(self, wav_bytes: bytes, family: str | None):
        segments, info = self.get().transcribe(
            io.BytesIO(wav_bytes),
            language=family,
            beam_size=1,
            vad_filter=True,
            initial_prompt=STT_HINTS.get(family or ""),
            condition_on_previous_text=False,
        )
        return list(segments), info

    def transcribe(self, wav_bytes: bytes, lang: str) -> dict:
        family, _ = parse_lang(lang)
        try:
            segments, info = self._run(wav_bytes, family or None)
        except ValueError:
            # Idioma que o Whisper nao conhece pelo codigo: deixa ele detectar sozinho.
            segments, info = self._run(wav_bytes, None)
        text = " ".join(s.text.strip() for s in segments).strip()
        if any(h in text.lower() for h in STT_HALLUCINATIONS):
            text = ""
        return {"text": text, "language": info.language}


class TtsRequest(BaseModel):
    text: str
    lang: str = "pt_br"
    voice: int = 0
    pitch: float = 1.0
    speed: float = 1.0
    format: str = "pcm"


def build_app(catalog: Catalog, bank: VoiceBank, stt: Stt, preload: list[str]) -> FastAPI:
    app = FastAPI(title="Mobs Falantes - Voz")
    state = {"ready": False}
    preparing: set[str] = set()

    def warm_up():
        try:
            catalog.load()
            for lang in preload:
                bank.prepare(lang)
            stt.get()
            state["ready"] = True
            LOG.info("Tudo pronto! Pode abrir o Minecraft.")
        except Exception:
            LOG.exception("Falha ao pre-carregar modelos")

    threading.Thread(target=warm_up, daemon=True).start()

    @app.get("/health")
    def health():
        return {"ok": True, "ready": state["ready"], "whisper": stt.model_name,
                "languages": len(catalog.languages()), "voices_loaded": sorted(bank.loaded)}

    @app.get("/languages")
    def languages():
        return catalog.languages()

    @app.post("/prepare")
    def prepare(lang: str):
        slots = catalog.slots(lang)
        if not slots:
            raise HTTPException(422, f"sem voz para o idioma {lang}")
        family, region = parse_lang(lang)
        if lang not in preparing:
            preparing.add(lang)
            LOG.info("Preparando vozes para %s: %s", lang, sorted({k for k, _ in slots}))
            threading.Thread(target=bank.prepare, args=(lang,), daemon=True).start()
        return {"lang": lang, "voices": len(slots), "models": sorted({k for k, _ in slots})}

    @app.post("/stt")
    async def speech_to_text(request: Request, lang: str = ""):
        data = await request.body()
        if len(data) < 1000:
            raise HTTPException(400, "audio vazio")
        t = time.perf_counter()
        result = await run_in_threadpool(stt.transcribe, data, lang)
        LOG.info("STT %.2fs [%s] %s", time.perf_counter() - t, result["language"], result["text"])
        return result

    @app.post("/tts")
    async def text_to_speech(req: TtsRequest):
        text = req.text.strip()[:600]
        if not text:
            raise HTTPException(400, "texto vazio")
        t = time.perf_counter()
        try:
            pcm = await run_in_threadpool(bank.synthesize, text, req.lang, req.voice, req.pitch, req.speed)
        except NoVoiceForLanguage:
            raise HTTPException(422, f"sem voz para o idioma {req.lang}")
        LOG.info("TTS %.2fs [%s] voz=%d tom=%.2f vel=%.2f %s", time.perf_counter() - t,
                 req.lang, req.voice, req.pitch, req.speed, text)
        if req.format == "wav":
            buf = io.BytesIO()
            with wave.open(buf, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(OUT_RATE)
                w.writeframes(pcm.tobytes())
            return Response(buf.getvalue(), media_type="audio/wav")
        return Response(pcm.tobytes(), media_type="application/octet-stream",
                        headers={"X-Sample-Rate": str(OUT_RATE)})

    return app


def main():
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="Servidor de voz do Mobs Falantes")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5005)
    p.add_argument("--whisper-model", default="small",
                   help="tiny, base, small, medium, large-v3 (maior = melhor e mais lento)")
    p.add_argument("--threads", type=int, default=6)
    p.add_argument("--voices-dir", default=str(here / "vozes"))
    p.add_argument("--preload", default="",
                   help="idiomas para baixar ja na abertura, ex: pt_br,en_us (o mod tambem pede sozinho)")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    voices_dir = Path(args.voices_dir)
    catalog = Catalog(voices_dir / "voices.json")
    bank = VoiceBank(voices_dir, catalog)
    stt = Stt(args.whisper_model, args.threads)
    preload = [x.strip() for x in args.preload.split(",") if x.strip()]
    # log_level="error": esconde avisos inofensivos do uvicorn (ex.: algum programa do PC tentando abrir
    # WebSocket na porta). Os logs do servidor de voz ("voz") continuam aparecendo normalmente.
    uvicorn.run(build_app(catalog, bank, stt, preload), host=args.host, port=args.port, log_level="error")


if __name__ == "__main__":
    main()
