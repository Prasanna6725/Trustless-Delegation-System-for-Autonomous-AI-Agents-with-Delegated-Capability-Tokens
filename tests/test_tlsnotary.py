import pytest

from backend import tlsnotary


class DummyResp:
    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        return None


def test_init_tlsnotary_session(monkeypatch):
    called = {}

    def fake_post(url):
        called['url'] = url
        return DummyResp({'session_id': 'sess-123'})

    monkeypatch.setattr('requests.post', fake_post)
    sid = tlsnotary.init_tlsnotary_session('http://notary.example')
    assert sid == 'sess-123'


def test_execute_notarized_request(monkeypatch):
    def fake_post(url, json):
        return DummyResp({'url': json['url'], 'method': json['method'], 'status': 200, 'body_hash': json.get('body_hash',''), 'signature': 'sig'})

    monkeypatch.setattr('backend.tlsnotary.get_notary_base', lambda: 'http://notary.example/notary')
    monkeypatch.setattr('requests.post', fake_post)
    proof = tlsnotary.execute_notarized_request('sess-1', 'https://api.example/foo', 'GET')
    assert proof['url'] == 'https://api.example/foo'
    assert proof['method'] == 'GET'
    assert 'signature' in proof
