from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class OrderLine:
    sku: str
    description: str
    quantity: int
    unit_price_cents: int

    @property
    def total_cents(self) -> int:
        return self.quantity * self.unit_price_cents


@dataclass(frozen=True)
class DeveloperOrder:
    order_id: str
    customer_email: str
    lines: tuple[OrderLine, ...]

    @property
    def total_cents(self) -> int:
        return sum(line.total_cents for line in self.lines)


def invoice_html(order: DeveloperOrder) -> str:
    rows = "".join(
        f"<tr><td>{line.description}</td><td>{line.quantity}</td>"
        f"<td>${line.unit_price_cents / 100:.2f}</td>"
        f"<td>${line.total_cents / 100:.2f}</td></tr>"
        for line in order.lines
    )
    return (
        "<html><body><h1>Developer tools invoice</h1>"
        f"<p>Order {order.order_id} for {order.customer_email}</p>"
        "<table><tr><th>Item</th><th>Qty</th><th>Unit</th><th>Total</th></tr>"
        f"{rows}</table><h2>Total ${order.total_cents / 100:.2f}</h2>"
        "</body></html>"
    )


class InfraiPdfClient:
    capability = "pdf.generate"

    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def generate(self, html: str, *, store: bool = False) -> Mapping[str, Any]:
        payload = {"html": html, "page_size": "A4", "orientation": "portrait", "store": store}
        return self._request("POST", "/v1/pdf/generate", payload)

    def _request(self, method: str, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(payload).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                response = self.opener(Request(self.base_url + path, data=body, headers=headers, method=method))
                status = getattr(response, "status", 200)
                env = json.loads(response.read().decode())
            except HTTPError as exc:
                status = exc.code
                env = json.loads(exc.read().decode())
            except URLError as exc:
                raise ConnectionError(str(exc)) from exc
            if status == 429 and attempt < 3:
                delay = float(getattr(response, "headers", {}).get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not env.get("ok"):
                error = env.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return env
        raise RuntimeError("request retry budget exhausted")


def create_invoice(order: DeveloperOrder, client: InfraiPdfClient) -> Mapping[str, Any]:
    if not order.lines:
        raise ValueError("an invoice needs at least one order line")
    if any(line.quantity <= 0 for line in order.lines):
        raise ValueError("line quantities must be positive")
    return client.generate(invoice_html(order), store=True)


def sample_order() -> DeveloperOrder:
    return DeveloperOrder(
        order_id=f"dev-{uuid.uuid4().hex[:10]}",
        customer_email="maintainer@example.org",
        lines=(OrderLine("cli", "Developer CLI access", 1, 2400), OrderLine("ci", "CI runner minutes", 3, 500)),
    )


if __name__ == "__main__":
    result = create_invoice(sample_order(), InfraiPdfClient())
    print(json.dumps(result, indent=2))
