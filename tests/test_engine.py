import numpy as np
import pytest
from telecom.engine import SimulationConfig, modulate, demodulate, simulate, theoretical_ber

@pytest.mark.parametrize('modulation',['BPSK','QPSK','16QAM'])
def test_noiseless_roundtrip(modulation):
    rng = np.random.default_rng(9)
    bits = rng.integers(0,2,4000,dtype=np.uint8)
    assert np.array_equal(bits,demodulate(modulate(bits, modulation),modulation))

@pytest.mark.parametrize('modulation',['BPSK','QPSK','16QAM'])
def test_average_symbol_energy_near_one(modulation):
    rng = np.random.default_rng(10)
    bits = rng.integers(0,2,80000,dtype=np.uint8)
    assert abs(np.mean(np.abs(modulate(bits, modulation))**2)-1) < 0.025

def test_reproducibility_and_bounds():
    cfg = SimulationConfig(modulation='QPSK', num_bits=10_000, ebn0_stop=6)
    a,b = simulate(cfg),simulate(cfg)
    assert a == b
    assert all(0 <= p['ber'] <= 1 for p in a['results'])
    assert len(a['constellation']) <= 280

def test_error_probability_decreases_approximately():
    rows=simulate(SimulationConfig(modulation='BPSK', num_bits=200_000, ebn0_start=0, ebn0_stop=8, ebn0_step=4))['results']
    assert rows[0]['ber'] > rows[1]['ber'] > rows[2]['ber']
    assert abs(rows[0]['ber'] - theoretical_ber('BPSK',1)) < .005

def test_input_validation():
    with pytest.raises(ValueError): simulate(SimulationConfig(num_bits=999))
    with pytest.raises(ValueError): simulate(SimulationConfig(ebn0_start=15,ebn0_stop=2))
    with pytest.raises(ValueError): simulate(SimulationConfig(modulation='OFDM'))
