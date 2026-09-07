# GTA Vice City: Browser Port

Self-hostable GTA Vice City that runs in the browser. Two pieces: a backend that streams the game, and a standalone landing page that wraps it.

## Quick start (pull the prebuilt image)

```bash
docker run -d \
  --name gtavc-engine \
  -p 8443:8000 \
  --restart unless-stopped \
  ghcr.io/developeranku/gta-vc-browser-port-engine:latest
```

Open `http://localhost:8443` and play.

The image has `PACKED=https://folder.morgen.qzz.io/revcdos.bin` baked in, so first start downloads the asset archive once and serves from it.

### Update later

```bash
docker pull ghcr.io/developeranku/gta-vc-browser-port-engine:latest
docker rm -f gtavc-engine
# re-run the `docker run` command above
```

## Quick start (clone and compose)

```bash
git clone https://github.com/developeranku/gta-vc-browser-port.git
cd gta-vc-browser-port/game-engine
docker compose up -d
```

Compose pulls the same `:latest` image. Add `--build` only if you want to rebuild locally.

## Quick start (web launcher, prebuilt image)

```bash
docker run -d \
  --name gtavc-web \
  -p 8080:4321 \
  --restart unless-stopped \
  ghcr.io/developeranku/gta-vc-browser-port-web:latest
```

Open `http://localhost:8080`. The image ships with `PUBLIC_GAME_URL=https://engine.gtavice.city:8443` baked in at build time (it's a static site, no runtime env vars). To point at a different backend, build your own image: `docker build --build-arg PUBLIC_GAME_URL=https://your-host:8443 -t my-web-launcher web-launcher/`.

## Repo layout

```
gta-vc-browser-port/
├── game-engine/        Backend. FastAPI + WASM runtime. Builds the published image.
│   ├── docker/         Dockerfile
│   ├── docker-compose.yml
│   ├── server.py       Entrypoint
│   └── README.md       Backend docs, all server flags, env vars
│
├── web-launcher/       Standalone landing page wrapping the backend in an iframe.
│   ├── src/            Astro sources
│   ├── Dockerfile      Builds Astro, serves it via `astro preview`
│   ├── docker-compose.yml
│   └── README.md       Launcher docs, dev setup, sandbox details
│
└── .github/workflows/
    ├── build-engine.yml        Builds and pushes the engine image to GHCR on push to main
    └── build-web-launcher.yml  Builds and pushes the web-launcher image to GHCR on push to main
```

## Components

| Component | Path | Docs |
|---|---|---|
| Backend engine | [`game-engine/`](./game-engine) | [game-engine/README.md](./game-engine/README.md) |
| Web launcher | [`web-launcher/`](./web-launcher) | [web-launcher/README.md](./web-launcher/README.md) |

## Configuration

Default image runs with sane defaults. To override (custom port, auth, local assets, packed/unpacked modes, language), use the compose flow and read [game-engine/README.md](./game-engine/README.md) for the full env var and CLI flag tables.

## Testing & Quality Assurance

The codebase includes automated unit test suites for the game engine and build verification for the web launcher.

### Backend Engine Tests (PyTest)

To run the full backend test suite:

```bash
pip install -r game-engine/requirements.txt pytest pytest-asyncio httpx
PYTHONPATH=game-engine python -m pytest game-engine/tests
```

Test coverage includes:
- **Authentication (`test_auth.py`)**: Basic Auth header parsing, CORS bypass, malformed base64, missing fields.
- **Save Operations & Security (`test_saves.py`)**: Token and filename sanitization, path traversal prevention, null byte protection.
- **Cache & Decompression (`test_cache.py`)**: Local file serving, client Brotli header evaluation, on-the-fly streaming decompression, resource cleanup.
- **Packed Archive (`test_packed.py`)**: Packed `.bin` loading, streaming responses, Brotli passthrough, and URL resolution.
- **Brotli Packing (`test_packer.py`, `test_downloader.py`)**: ULEB128 encoding/decoding, folder & file deduplication, parallel Brotli quality-11 compression, async streaming unpack.
- **FastAPI Server (`test_server.py`)**: Route handling, `dist/index.html` script injection, CLI argument parsing isolation.

### Web Launcher Verification

To build and verify the static web launcher application:

```bash
cd web-launcher
pnpm install
pnpm build
```

## License and credit

Backend is MIT, originally by [DOS Zone](https://dos.zone) and [@Lolendor](https://github.com/Lolendor). See [game-engine/LICENSE](./game-engine/LICENSE). Not affiliated with Rockstar Games.
