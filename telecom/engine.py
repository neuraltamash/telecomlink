"""Vectorized coherent baseband AWGN simulator; all SNR values are Eb/N0 in dB."""
from __future__ import annotations
from dataclasses import dataclass
from math import erfc, sqrt
import numpy as np

SUPPORTED = ('BPSK', 'QPSK', '16QAM')

@dataclass(frozen=True)
class SimulationConfig:
    modulation: str = 'QPSK'
    ebn0_start: int = 0
    ebn0_stop: int = 12
    ebn0_step: int = 2
    num_bits: int = 100_000
    seed: int = 42

    def validate(self):
        if self.modulation not in SUPPORTED: raise ValueError('Unsupported modulation')
        if not (-4 <= self.ebn0_start <= 24 and -4 <= self.ebn0_stop <= 24):
            raise ValueError('Eb/N0 bounds must be between -4 and 24 dB')
        if self.ebn0_start > self.ebn0_stop: raise ValueError('Start must be <= stop')
        if not 1 <= self.ebn0_step <= 8: raise ValueError('Step must be 1 to 8 dB')
        if not 1000 <= self.num_bits <= 300_000: raise ValueError('Bits must be 1,000 to 300,000')
        if not 0 <= self.seed <= 2**32 - 1: raise ValueError('Seed out of bounds')
        if len(range(self.ebn0_start, self.ebn0_stop + 1, self.ebn0_step)) > 16:
            raise ValueError('Too many SNR points')
        return self

def bits_per_symbol(modulation):
    return {'BPSK':1, 'QPSK':2, '16QAM':4}[modulation]

def modulate(bits, modulation):
    bits = np.asarray(bits, dtype=np.uint8)
    k = bits_per_symbol(modulation)
    if len(bits) % k: raise ValueError('Bit count must be divisible by bits per symbol')
    if modulation == 'BPSK':
        return (1 - 2 * bits.astype(np.float64)).astype(np.complex128)
    if modulation == 'QPSK':
        pairs = bits.reshape(-1, 2).astype(np.float64)
        return ((1 - 2*pairs[:, 0]) + 1j*(1 - 2*pairs[:, 1]))/np.sqrt(2)
    groups = bits.reshape(-1, 4)
    # Gray-coded levels 00:-3, 01:-1, 11:+1, 10:+3.
    table = np.array([-3, -1, 3, 1], dtype=np.float64)
    i = table[2*groups[:,0] + groups[:,1]]
    q = table[2*groups[:,2] + groups[:,3]]
    return (i + 1j*q)/np.sqrt(10)

def demodulate(symbols, modulation):
    z = np.asarray(symbols)
    if modulation == 'BPSK': return (z.real < 0).astype(np.uint8)
    if modulation == 'QPSK':
        out = np.empty((len(z), 2), dtype=np.uint8)
        out[:,0] = z.real < 0
        out[:,1] = z.imag < 0
        return out.ravel()
    def decisions(values):
        scaled = values * np.sqrt(10)
        idx = np.digitize(scaled, [-2, 0, 2])
        # -3=>00, -1=>01, 1=>11, 3=>10
        a = np.array([0,0,1,1],dtype=np.uint8)[idx]
        b = np.array([0,1,1,0],dtype=np.uint8)[idx]
        return a,b
    ia,ib = decisions(z.real)
    qa,qb = decisions(z.imag)
    out = np.column_stack([ia, ib, qa, qb])
    return out.ravel()

def theoretical_ber(modulation, linear_ebn0):
    if modulation in ('BPSK','QPSK'):
        return 0.5 * erfc(sqrt(linear_ebn0))
    # Gray-coded square 16-QAM, conventional nearest-neighbor approximation.
    return 0.375 * erfc(sqrt(0.4 * linear_ebn0))

def simulate(config: SimulationConfig):
    config.validate()
    rng = np.random.default_rng(config.seed)
    k = bits_per_symbol(config.modulation)
    actual_bits = (config.num_bits // k) * k
    transmitted_bits = rng.integers(0, 2, actual_bits, dtype=np.uint8)
    symbols = modulate(transmitted_bits, config.modulation)
    rows = []
    representative = None
    values = list(range(config.ebn0_start, config.ebn0_stop+1, config.ebn0_step))
    for ix, db in enumerate(values):
        gamma = 10 ** (db / 10)
        # With Es normalized to 1, N0 = 1 / (k*EbN0).
        noise_std = sqrt(1 / (2*k*gamma))
        noise = noise_std * (rng.standard_normal(len(symbols)) + 1j*rng.standard_normal(len(symbols)))
        received = symbols + noise
        recovered = demodulate(received, config.modulation)
        errors = int(np.count_nonzero(transmitted_bits != recovered))
        measured = errors / actual_bits
        theory = theoretical_ber(config.modulation, gamma)
        # Approximate 95% Wilson interval for observed Bernoulli bit errors.
        z = 1.96
        p = measured
        den = 1 + z*z/actual_bits
        center = (p + z*z/(2*actual_bits)) / den
        half = (z / den) * sqrt(p*(1-p)/actual_bits + z*z/(4*actual_bits**2))
        rows.append({'ebn0_db':db, 'ber':measured, 'theoretical_ber':theory,
                     'bit_errors':errors, 'bits_tested':actual_bits,
                     'ci_low':max(0,center-half), 'ci_high':min(1,center+half)})
        if ix == len(values)//2:
            # Downsample plotting payload for predictable serverless response size.
            n = min(280, len(symbols))
            representative = [{'i':round(float(x.real),4),'q':round(float(x.imag),4)} for x in received[:n]]
    return {'configuration': {'modulation': config.modulation,'ebn0_start':config.ebn0_start,
                'ebn0_stop':config.ebn0_stop,'ebn0_step':config.ebn0_step,
                'num_bits':actual_bits,'seed':config.seed},
            'results': rows, 'constellation':representative,
            'summary':{'total_tested_bits':actual_bits*len(rows),
                'total_bit_errors':sum(row['bit_errors'] for row in rows),
                'snr_points':len(rows),
                'zero_error_points':sum(row['bit_errors']==0 for row in rows)},
            'notes':{'model':'Coherent baseband AWGN; ideal synchronization, no coding or fading.',
                     'theory':'16-QAM theoretical BER is a nearest-neighbor approximation.',
                     'confidence':'Wilson 95% confidence intervals. Zero measured BER is not proof of zero true BER.'}}
