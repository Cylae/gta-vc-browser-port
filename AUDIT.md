# Full Audit Report: GTA Vice City Browser Port (`gta-vc-browser-port`)

**Audit Date:** February 2025
**Auditor:** Jules (AI Software Engineer)
**Target Repository:** `developeranku/gta-vc-browser-port`

---

## Executive Summary

This report presents a full technical audit of the **GTA Vice City Browser Port** project. The project consists of two core components:
1. **`game-engine`**: A FastAPI-based backend written in Python that serves the WASM game runtime, manages static assets, streams compressed `.bin` archives using Brotli compression, handles proxy caching from upstream CDNs, and manages cloud save states.
2. **`web-launcher`**: An Astro-based frontend application providing a retro 1980s Vice City-themed UI that mounts the game engine inside an isolated, sandboxed `<iframe>`.

---

## Architecture Overview

```
+-----------------------------------------------------------------------+
|                             WEB LAUNCHER                              |
|                      Astro Frontend (:4321)                           |
|  +-----------------------------------------------------------------+  |
|  | Landing Page / HUD / Canvas Scene / Controls                    |  |
|  | +-------------------------------------------------------------+ |  |
|  | | <iframe src="PUBLIC_GAME_URL" sandbox="...">                | |  |
|  | +-------------------------------------------------------------+ |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
                                   | (Cross-Origin Frame Load)
                                   v
+-----------------------------------------------------------------------+
|                             GAME ENGINE                               |
|                    FastAPI Backend / WASM (:8000)                     |
|  +---------------------+ +--------------------+ +-------------------+ |
|  | Static Assets (dist)| | Saves API (/saves) | | Proxy / Packed    | |
|  | WASM Runtime & JS   | | Custom saves route | | Cache Streamer    | |
|  +---------------------+ +--------------------+ +-------------------+ |
+-----------------------------------------------------------------------+
```

---

## Detailed Audit Findings

### 1. Security Analysis

#### 🔴 High Vulnerability: Path Traversal in Custom Saves Endpoint
* **Location:** `game-engine/additions/saves.py`
* **Details:**
  While `fileName` is sanitized using `os.path.basename(fileName)`, the `token` parameter in both `upload_save` and `download_save` is used directly in path construction:
  ```python
  save_path = os.path.join(SAVES_DIR, f"{token}_{safe_filename}")
  ```
  If an attacker sends a `token` containing path traversal characters (e.g., `../../`), files can be written or read outside of the intended `saves/` directory.
* **Remediation:**
  Sanitize `token` using `os.path.basename` or validate it against a strict alphanumeric whitelist regex (`^[a-zA-Z0-9_-]+$`).

#### 🟡 Medium Concern: Legacy PHP Script Security Exposure
* **Location:** `game-engine/index.php`
* **Details:**
  The codebase contains an unmaintained `index.php` file alongside `server.py`. If deployed on a web server running PHP, `proxy_request()` blindly forwards headers and body data to external endpoints without input filtering or rate limiting.
* **Remediation:**
  Remove `index.php` if FastAPI (`server.py`) is the sole supported server, or ensure equivalent security controls are implemented.

#### 🟡 Medium Concern: Basic Authentication Error Handling & Formatting
* **Location:** `game-engine/additions/auth.py`
* **Details:**
  In `BasicAuthMiddleware`, if the incoming `Authorization` header contains malformed base64 or non-standard characters, `base64.b64decode` or string splitting may raise unexpected exceptions. While wrapped in `try...except`, returning a generic 401 response is correct, but constant-time comparison is only partially applied (`secrets.compare_digest` is used, but length/splitting can leak timing details).
* **Remediation:**
  Enhance validation and exception safety in `BasicAuthMiddleware`.

#### 🟢 Low Risk: Web Launcher Iframe Sandboxing
* **Location:** `web-launcher/src/components/GameOverlay.astro`
* **Details:**
  The `<iframe>` uses sandbox attributes: `allow-scripts allow-same-origin allow-pointer-lock allow-forms allow-popups-to-escape-sandbox allow-modals`.
  `allow-same-origin` with `allow-scripts` allows the iframe to access its own origin's IndexedDB and cookies. Because the game engine runs on a separate origin (`PUBLIC_GAME_URL`), it cannot access the parent web launcher's DOM or cookies.

---

### 2. Code Quality & Maintainability

* **Test Suite:** Prior to this audit, there were no automated tests in the repository. We added unit tests in `game-engine/tests/` covering authentication, save operations, ULEB128 encoding/decoding, and Brotli packing/unpacking routines.
* **Code Modularization:** Clean separation between `game-engine` and `web-launcher`. `game-engine/additions/` and `game-engine/utils/` modules are structured logically.
* **Dependency Management:** Python dependencies are pinned minimalistically in `game-engine/requirements.txt`. Web Launcher uses `pnpm` with locked versions in `pnpm-lock.yaml`.

---

### 3. Performance & Asset Streaming

* **Brotli Compression & Streaming:**
  `game-engine/utils/packer_brotli.py` and `downloader_brotli.py` implement parallel Brotli quality-11 compression and stream unpacking using `asyncio.Queue`. This significantly reduces download size and bandwidth requirements.
* **Coop/Coep Isolation Headers:**
  Responses serve `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers, enabling `SharedArrayBuffer` required for WASM multi-threading and low-latency audio/video output.

---

### 4. Containerization & CI/CD Infrastructure

* **Docker Configurations:**
  - `game-engine/docker/Dockerfile` builds from `python:3.11-slim`.
  - Containers run as `root` by default. Creating a dedicated non-privileged user in Dockerfiles is recommended for hardened production environments.
* **GitHub Actions:**
  - `.github/workflows/build-engine.yml` and `build-web-launcher.yml` build and push images to GitHub Container Registry (`ghcr.io`) on pushes to `main`.
  - Workflow caching (`cache-from: type=gha`) is properly configured.

---

## Action Plan & Summary of Recommendations

| Priority | Category | Recommendation | Status |
|---|---|---|---|
| **High** | Security | Sanitize `token` parameter in `game-engine/additions/saves.py` | Recommended Fix |
| **Medium** | Security | Remove legacy `game-engine/index.php` or align with Python server | Recommended Fix |
| **Medium** | DevOps | Configure non-root execution in Dockerfiles | Recommended Improvement |
| **Low** | Testing | Maintain and expand automated test coverage in `game-engine/tests/` | Implemented Base Tests |
