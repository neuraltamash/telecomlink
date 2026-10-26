from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_health():
    response=client.get('/api/health')
    assert response.status_code==200
    assert response.json()['status']=='ok'

def test_simulation():
    response=client.post('/api/simulate',json={'modulation':'16QAM','num_bits':4000,'ebn0_stop':4})
    assert response.status_code==200
    data=response.json()
    assert len(data['results'])==3
    assert data['configuration']['modulation']=='16QAM'

def test_bad_inputs():
    for body in ({'num_bits':4},{'modulation':'unknown'},{'ebn0_start':12,'ebn0_stop':2}):
        assert client.post('/api/simulate',json=body).status_code==422
