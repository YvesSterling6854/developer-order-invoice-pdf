import json

import pytest

from src.invoice_service import DeveloperOrder, InfraiPdfClient, OrderLine, create_invoice


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode()


def test_invoice_rejects_empty_order_before_network():
    calls = []
    client = InfraiPdfClient(api_key="test-key", opener=lambda request: calls.append(request))
    order = DeveloperOrder("ord-1", "dev@example.org", ())
    with pytest.raises(ValueError, match="at least one"):
        create_invoice(order, client)
    assert calls == []


def test_invoice_sends_html_and_returns_envelope():
    seen = {}

    def opener(request):
        seen["method"] = request.method
        seen["body"] = json.loads(request.data)
        return FakeResponse({"ok": True, "data": {"job_id": "job-1"}, "error": None, "metadata": {}})

    order = DeveloperOrder("ord-2", "dev@example.org", (OrderLine("sdk", "SDK", 2, 1250),))
    result = create_invoice(order, InfraiPdfClient(api_key="test-key", opener=opener))
    assert result["ok"] is True
    assert seen["method"] == "POST"
    assert seen["body"]["page_size"] == "A4"
    assert "ord-2" in seen["body"]["html"]
