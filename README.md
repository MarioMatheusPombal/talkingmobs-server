# TalkingMobs Server 🗣️

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

---

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

---

## English

**TalkingMobs Server** is the local voice server for the **Mobs Falantes** Minecraft mod: speech-to-text with
faster-whisper (~100 languages) and text-to-speech with Piper (voices auto-downloaded for 57 languages), fully
offline on your own PC. Run `iniciar-voz.bat` (Windows) or `sh iniciar-voz.sh` (Linux/macOS), wait for
`Tudo pronto!`, and start the game. HTTP API above. If you enjoy it, please
**[support me on Ko-fi](https://ko-fi.com/mariomatheuspombal)** ☕

## Licença e créditos

- Este servidor é distribuído sob a **GPL-3.0** (veja [`LICENSE`](LICENSE)), porque usa o Piper, que também é GPL-3.0.
- [Piper](https://github.com/OHF-Voice/piper1-gpl) (GPL-3.0) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) ·
  [FastAPI](https://fastapi.tiangolo.com) (MIT).
- As vozes vêm do catálogo [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) e cada uma tem a sua
  licença (veja o `MODEL_CARD` de cada voz). As vozes brasileiras usadas por padrão: faber, cadu e jeff (CC0) e
  edresson (CC BY 4.0, dataset de Edresson Casanova).
