"""FastAPI serverless entry point for Vercel."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from telecom.engine import SimulationConfig, simulate, SUPPORTED

app = FastAPI(title='TelecomLink Verification API', version='1.0.0', docs_url='/api/docs', openapi_url='/api/openapi.json')
# Frontend and API share an origin in production; permissive local development is unnecessary.
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'], allow_methods=['GET','POST'], allow_headers=['*'])

class Request(BaseModel):
    modulation: str = 'QPSK'
    ebn0_start: int = Field(default=0, ge=-4, le=24)
    ebn0_stop: int = Field(default=12, ge=-4, le=24)
    ebn0_step: int = Field(default=2, ge=1, le=8)
    num_bits: int = Field(default=100_000, ge=1000, le=300_000)
    seed: int = Field(default=42, ge=0, le=2**32-1)

@app.get('/api/health')
def health():
    return {'status':'ok','service':'TelecomLink','supported_modulations':SUPPORTED}

@app.post('/api/simulate')
def run_simulation(request: Request):
    try:
        return simulate(SimulationConfig(**request.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
