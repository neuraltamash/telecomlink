# TelecomLink — Signal Verification Studio

An interactive, resume-ready **digital communication link verification dashboard** with an actual Python/Numpy simulation engine, automated tests, data exports and a Vercel-ready React frontend.

> **Scope:** This is a software simulation for educational/product-verification practice, **not** a production optical modem, a networking device emulator, or a tool connected to Ciena equipment.

## Capabilities

- Coherent **BPSK, QPSK, and Gray-coded 16-QAM** mapping and hard decision demodulation
- Complex AWGN channel with per-symbol noise variance properly calculated from **Eb/N0** and bits/symbol
- Measured **bit error rate vs Eb/N0** compared with theory; 16-QAM uses nearest-neighbor BER approximation
- 95% Wilson binomial intervals included in the JSON and CSV results
- Interactive BER and I/Q constellation plots, responsive dark dashboard
- Reproducible seeded experiments; bounded samples to fit serverless usage
- CSV / JSON report exports, parameter validation, API error handling
- Pytest engine + FastAPI route tests, GitHub Actions build verification
- Single GitHub repository, React/Vite frontend + FastAPI serverless API

## Local setup

Requires **Python 3.12+**, **Node.js 20+**, npm.

**Terminal 1 — Python API**

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m uvicorn api.index:app --reload --port 8000
```

`uvicorn` is a local-development dependency; if it is not installed, run `pip install uvicorn`.

**Terminal 2 — dashboard**

```bash
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to FastAPI on port 8000.

### Run automated checks

```bash
python -m pytest -q
npm run build
```

### Test the API without the browser

```bash
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/simulate \
  -H 'Content-Type: application/json' \
  -d '{"modulation":"QPSK","num_bits":10000,"ebn0_start":0,"ebn0_stop":10,"ebn0_step":2,"seed":42}'
```

## Deploy on Vercel

1. Extract ZIP, push **the contents of this directory** to a GitHub repository (root contains `package.json`, `vercel.json`, `api/`).
2. Go to [Vercel](https://vercel.com/new), import your repository.
3. Choose **Vite** (or Other with the project settings below). **Root Directory**: repository root.
4. **Build Command**: `npm run build`; **Output Directory**: `dist`; **Install Command**: `npm install` (or auto-detect).
5. Keep Python backend in `api/index.py` — `vercel.json` rewrites `/api/*` to this handler.
6. Deploy, then open `https://YOUR-DOMAIN.vercel.app/api/health`; you should receive `{"status":"ok",...}`.
7. Open the homepage, choose a modulation, and click **Run Simulation**.

**No database or environment variables are required.** API and frontend use the same origin, so no production CORS configuration is necessary. The API is intentionally stateless: refreshes clear the last run unless you've exported it.

**Notes:** Python function size and execution-time limits depend on Vercel plan; each request is capped at 300,000 bits and 16 SNR points to keep resource use bounded. This project has not been live deployed by its authoring environment; verify your first Vercel build and test both `/api/health` and `/api/simulate` after import. See Vercel's [Python runtime docs](https://vercel.com/docs/functions/runtimes/python).

## Architecture

```text
Browser React / Vite
     |
     | POST /api/simulate
     v
FastAPI (api/index.py) [Vercel Python Function]
     |
     v
telecom/engine.py [NumPy]
     |  random bits -> modulation -> AWGN -> demodulation -> BER
     v
JSON response -> Recharts BER and constellation -> CSV/JSON exports
```

## Important modeling assumptions

- **AWGN only**. No fiber nonlinearity, chromatic dispersion, FEC, synchronization errors, fading, packet loss, or real optical equipment.
- Constellation diagrams display received samples from the **middle SNR point** (not all points).
- BPSK and QPSK use exact coherent AWGN theoretical BER `0.5 * erfc(sqrt(Eb/N0))`.
- 16-QAM uses a **nearest-neighbor approximation**: `0.375 * erfc(sqrt(0.4*Eb/N0))`.
- A measured BER of zero means no observed errors in the **finite sample**, not guaranteed zero true BER. Log chart clips zero at `1e-7` for visual display; exports retain exact zero.
- Wilson 95% confidence intervals are for binomial error proportions; finite deterministic pseudo-random simulation is not a real-world performance guarantee.

## API

- `GET /api/health` returns service health and supported schemes.
- `POST /api/simulate` accepts:

```json
{"modulation":"QPSK","ebn0_start":0,"ebn0_stop":12,"ebn0_step":2,"num_bits":100000,"seed":42}
```

Parameters: modulation `BPSK|QPSK|16QAM`, Eb/N0 bounds -4..24 dB, step 1..8 dB, bit count 1000..300000, seed 0..4294967295. Invalid requests return HTTP 422.

## Suggested interview explanation

"I implemented a coherent baseband digital-link simulator in Python, generated BPSK/QPSK/16-QAM constellations, injected noise calibrated to Eb/N0 and measured BER versus theoretical predictions. I added automated tests and confidence intervals, exposed the simulator through a FastAPI interface, and built a Vercel-deployable React dashboard with downloadable verification reports. The simulation intentionally models AWGN rather than production optical fiber behavior."

## Next extensions

- Fiber attenuation and chromatic dispersion channel model
- Automated threshold/quality gates and failed-test records
- Packetized TCP traffic plus network impairment testing
- Background queue for large-scale Monte Carlo analysis

MIT licensed. See `LICENSE`.
