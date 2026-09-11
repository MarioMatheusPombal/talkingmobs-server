<a name="english"></a>

# TalkingMobs Server 🗣️

**English** · [Português](#portugues)

The **local voice server** for the **Mobs Falantes** Minecraft mod: it lets mobs **understand what you say** and
**answer with their own voice**, in **57 languages**, running 100% on your computer (no cloud, no paid API).

<p align="center">
  <a href="https://ko-fi.com/mariomatheuspombal">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support me on Ko-fi" height="42">
  </a>
</p>

> ☕ **Enjoying the project?** It's made in my free time and it's free to use.
> **[Support me on Ko-fi](https://ko-fi.com/mariomatheuspombal)** so I can keep making mobs feel more alive:
> new voices, quests, mob armies and the next add-on, **MobsActions**. Every bit helps! 💚

---

## What it does

| | Technology | What it does |
|---|---|---|
| 🎤 **Speech → text** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Understands your speech in ~100 languages |
| 🔊 **Text → speech** | [Piper](https://github.com/OHF-Voice/piper1-gpl) | Gives mobs a voice, automatically picking and downloading voices for your game's language |
| 🎭 **Voice per mob** | pitch + speed | Deep, slow zombies, high-pitched cats, squeaky babies... each mob always keeps the same voice |

- **57 languages with voices**: English, Portuguese, Spanish, French, German, Italian, Japanese, Korean, Chinese,
  Russian... The server uses Piper's official voice catalog and only downloads voices for the language you play in.
- **Fast on CPU**: ~0.3 s to generate a sentence and ~2 s to understand a short phrase (tested on a Ryzen 7 5700X,
  no NVIDIA GPU).
- **Private**: everything runs on `127.0.0.1`. Only the first run downloads the models.

## How to use

### 1. Requirements

- **Python 3.10 to 3.13** ([python.org](https://www.python.org/downloads/)). On Windows, check *"Add Python to PATH"*.
- ~0.5 GB for Whisper + ~60 MB per downloaded voice.
- To play: Minecraft 1.21.8 with NeoForge, the **Mobs Falantes** mod,
  [Simple Voice Chat](https://modrinth.com/plugin/simple-voice-chat) and [Ollama](https://ollama.com) with the
  `llama3.2` model.

### 2. Download

```bash
git clone https://github.com/MarioMatheusPombal/talkingmobs-server.git
cd talkingmobs-server
```

(or *Code → Download ZIP* here on GitHub)

### 3. Start

- **Windows:** double-click **`iniciar-voz.bat`**
- **Linux/macOS:** `sh iniciar-voz.sh`

On the first run it creates a Python environment (`.venv`), installs the dependencies and downloads Whisper.
Wait for **`Tudo pronto! Pode abrir o Minecraft.`** ("All set! You can open Minecraft.") and keep the window open
while you play.

When you join a world, the mod tells the server your game's language and the server downloads the right voices in
the background.

### Options

```bash
iniciar-voz.bat --whisper-model medium      # understands better, but slower
iniciar-voz.bat --preload en_us,pt_br       # downloads these languages' voices at startup
iniciar-voz.bat --port 5005 --threads 6
```

| Option | Default | Purpose |
|---|---|---|
| `--whisper-model` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3` (bigger = better and slower) |
| `--preload` | empty | Languages to download at startup, e.g. `en_us,pt_br` |
| `--host` / `--port` | `127.0.0.1` / `5005` | Where the server listens (the mod uses `http://127.0.0.1:5005`) |
| `--threads` | `6` | CPU cores used by Whisper |
| `--voices-dir` | `./vozes` | Where downloaded voices are stored |

## HTTP API

Any program can use the server, not just the mod.

| Route | Usage |
|---|---|
| `POST /stt?lang=en_us` | body = WAV audio → `{"text": "...", "language": "en"}` |
| `POST /tts` | JSON `{"text", "lang", "voice", "pitch", "speed"}` → 16-bit mono 48 kHz PCM. With `"format": "wav"` it returns a WAV |
| `POST /prepare?lang=xx` | downloads the language's voices in the background (`422` = no voice for that language) |
| `GET /languages` | languages with voices |
| `GET /health` | server status |

Example (PowerShell):

```powershell
$body = @{ text = "Hello, traveler! Seen any creepers around?"; lang = "en_us"; voice = 2; pitch = 0.75; format = "wav" } | ConvertTo-Json
Invoke-WebRequest http://127.0.0.1:5005/tts -Method Post -ContentType "application/json; charset=utf-8" `
  -Body ([Text.Encoding]::UTF8.GetBytes($body)) -OutFile zombie.wav
```

`voice` picks one of the language's voices (each mob always uses the same number); `pitch` and `speed` go from 0.5 to 2.

## Troubleshooting

- **"only one usage of each socket address"**: a server is already running on port 5005. Close the other window.
- **Slow first run**: that's the download of Whisper (~480 MB) and the voices. It starts fast after that.
- **"sem voz para o idioma" (no voice for the language)**: Piper doesn't have a voice for that language yet; mobs
  answer in text only.
- **Whisper mishearing you**: speak closer to the microphone or use `--whisper-model medium`.

## Support ☕

If the project made you smile, a coffee goes a long way toward keeping everything free and new features coming:

<p align="center">
  <a href="https://ko-fi.com/mariomatheuspombal">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support me on Ko-fi" height="42">
  </a>
</p>

Other ways to help: star ⭐ the repository, report bugs in *Issues* and show your friends the talking mobs.

## License and credits

- This server is distributed under the **GPL-3.0** (see [`LICENSE`](LICENSE)), because it uses Piper, which is also GPL-3.0.
- [Piper](https://github.com/OHF-Voice/piper1-gpl) (GPL-3.0) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) ·
  [FastAPI](https://fastapi.tiangolo.com) (MIT).
- Voices come from the [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) catalog and each one has its
  own license (see each voice's `MODEL_CARD`). The default Brazilian Portuguese voices: faber, cadu and jeff (CC0) and
  edresson (CC BY 4.0, dataset by Edresson Casanova).

<br>

---
---

<br>

<a name="portugues"></a>

# Versão em português

[English](#english) · **Português**

**Servidor de voz local** do mod **Mobs Falantes** para Minecraft: faz os mobs **entenderem o que você fala**
e **responderem com voz própria**, em **57 idiomas**, rodando 100% no seu computador (sem nuvem, sem API paga).

<p align="center">
  <a href="https://ko-fi.com/mariomatheuspombal">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Apoie no Ko-fi" height="42">
  </a>
</p>

> ☕ **Curtiu o projeto?** Ele é feito nas horas vagas e é de graça.
> **[Me apoie no Ko-fi](https://ko-fi.com/mariomatheuspombal)** para eu continuar criando mobs cada vez mais
> vivos: novas vozes, missões, exércitos de mobs e o próximo add-on, o **MobsActions**. Qualquer valor ajuda! 💚

## O que ele faz

| | Tecnologia | O que faz |
|---|---|---|
| 🎤 **Voz → texto** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Entende a sua fala em ~100 idiomas |
| 🔊 **Texto → voz** | [Piper](https://github.com/OHF-Voice/piper1-gpl) | Dá voz aos mobs, escolhendo e baixando sozinho as vozes do idioma do seu jogo |
| 🎭 **Voz por mob** | tom + velocidade | Zumbi grave e lento, gato agudo, filhote mais fino... cada mob fica sempre com a mesma voz |

- **57 idiomas com voz**: português, inglês, espanhol, francês, alemão, italiano, japonês, coreano, chinês, russo...
  O servidor usa o catálogo oficial do Piper e baixa só as vozes do idioma que você está usando.
- **Rápido na CPU**: ~0,3 s para gerar uma frase e ~2 s para entender uma fala curta (testado num Ryzen 7 5700X,
  sem placa de vídeo NVIDIA).
- **Privado**: tudo roda em `127.0.0.1`. Só a primeira execução baixa os modelos.

## Como usar

### 1. Requisitos

- **Python 3.10 a 3.13** ([python.org](https://www.python.org/downloads/)). No Windows, marque *"Add Python to PATH"*.
- ~0,5 GB para o Whisper + ~60 MB por voz baixada.
- Para jogar: Minecraft 1.21.8 com NeoForge, o mod **Mobs Falantes**, o
  [Simple Voice Chat](https://modrinth.com/plugin/simple-voice-chat) e o [Ollama](https://ollama.com)
  com o modelo `llama3.2`.

### 2. Baixar

```bash
git clone https://github.com/MarioMatheusPombal/talkingmobs-server.git
cd talkingmobs-server
```

(ou *Code → Download ZIP* aqui no GitHub)

### 3. Iniciar

- **Windows:** dois cliques em **`iniciar-voz.bat`**
- **Linux/macOS:** `sh iniciar-voz.sh`

Na primeira vez ele cria um ambiente Python (`.venv`), instala as dependências e baixa o Whisper. Espere aparecer
**`Tudo pronto! Pode abrir o Minecraft.`** e deixe a janela aberta enquanto joga.

Quando você entra num mundo, o mod avisa o idioma do seu jogo e o servidor baixa as vozes certas em segundo plano.

### Opções

```bash
iniciar-voz.bat --whisper-model medium      # entende melhor, mas é mais lento
iniciar-voz.bat --preload pt_br,en_us       # já baixa as vozes desses idiomas na abertura
iniciar-voz.bat --port 5005 --threads 6
```

| Opção | Padrão | Para quê |
|---|---|---|
| `--whisper-model` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3` (maior = melhor e mais lento) |
| `--preload` | vazio | Idiomas para baixar já na abertura, ex.: `pt_br,en_us` |
| `--host` / `--port` | `127.0.0.1` / `5005` | Onde o servidor escuta (o mod usa `http://127.0.0.1:5005`) |
| `--threads` | `6` | Núcleos da CPU usados pelo Whisper |
| `--voices-dir` | `./vozes` | Onde as vozes baixadas ficam |

## API HTTP

Qualquer programa pode usar o servidor, não só o mod.

| Rota | Uso |
|---|---|
| `POST /stt?lang=pt_br` | corpo = áudio WAV → `{"text": "...", "language": "pt"}` |
| `POST /tts` | JSON `{"text", "lang", "voice", "pitch", "speed"}` → PCM 16 bits mono 48 kHz. Com `"format": "wav"` devolve WAV |
| `POST /prepare?lang=xx` | baixa as vozes do idioma em segundo plano (`422` = idioma sem voz) |
| `GET /languages` | idiomas com voz |
| `GET /health` | estado do servidor |

Exemplo (PowerShell):

```powershell
$body = @{ text = "Olá, viajante! Viu algum creeper por aí?"; lang = "pt_br"; voice = 2; pitch = 0.75; format = "wav" } | ConvertTo-Json
Invoke-WebRequest http://127.0.0.1:5005/tts -Method Post -ContentType "application/json; charset=utf-8" `
  -Body ([Text.Encoding]::UTF8.GetBytes($body)) -OutFile zumbi.wav
```

`voice` escolhe uma das vozes do idioma (cada mob usa sempre o mesmo número); `pitch` e `speed` vão de 0,5 a 2.

## Problemas comuns

- **"only one usage of each socket address"**: já existe um servidor aberto na porta 5005. Feche a outra janela.
- **Primeira execução demorada**: é o download do Whisper (~480 MB) e das vozes. Das próximas vezes abre rápido.
- **"sem voz para o idioma"**: o Piper ainda não tem voz para esse idioma; os mobs respondem só em texto.
- **Whisper entendendo errado**: fale mais perto do microfone ou use `--whisper-model medium`.

## Apoie ☕

Se o projeto te divertiu, um café ajuda muito a manter tudo de graça e sair novidade:

<p align="center">
  <a href="https://ko-fi.com/mariomatheuspombal">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Apoie no Ko-fi" height="42">
  </a>
</p>

Outras formas de ajudar: dar ⭐ no repositório, reportar bugs nas *Issues* e mostrar os mobs falando para os amigos.

## Licença e créditos

- Este servidor é distribuído sob a **GPL-3.0** (veja [`LICENSE`](LICENSE)), porque usa o Piper, que também é GPL-3.0.
- [Piper](https://github.com/OHF-Voice/piper1-gpl) (GPL-3.0) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) ·
  [FastAPI](https://fastapi.tiangolo.com) (MIT).
- As vozes vêm do catálogo [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) e cada uma tem a sua
  licença (veja o `MODEL_CARD` de cada voz). As vozes brasileiras usadas por padrão: faber, cadu e jeff (CC0) e
  edresson (CC BY 4.0, dataset de Edresson Casanova).
