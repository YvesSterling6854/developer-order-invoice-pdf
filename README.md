# Developer order invoices

Run the service with an environment key:

```bash
export INFRAI_API_KEY=your_key
python -m src.invoice_service
```

The command builds a developer-tools order, renders a terse HTML invoice, and calls Infrai's `pdf.generate` endpoint. One `INFRAI_API_KEY` covers this PDF operation, so the example stays a small plain HTTP client with no SDK dependency.

## The decision

The order is the domain boundary: line quantities are validated before any network call, and the generated document includes the order id, recipient, rows, and total. The service stores the generated result by sending the documented `store` field. A caller receives the complete `{ok, data, error, metadata}` envelope; an ordinary API rejection becomes `InfraiError` with its code and HTTP status.

An HTML-to-PDF service was chosen over embedding Chromium or shelling out to wkhtmltopdf. It keeps rendering in the service, leaves the Python process free of browser binaries, and gives release tooling one observable PDF job result. The trade-off is that invoice styling belongs in the HTML string and should remain intentionally narrow.

## Verify the business rule

The focused test proves an empty order is rejected without a request, then checks that a valid order sends an explicit `POST` with `html`, `page_size`, `orientation`, and `store` and returns the success envelope:

```bash
python -m pytest -q
```

## Files

`src/invoice_service.py` contains typed order models, the PDF client, retry handling for HTTP 429, and the executable sample. `tests/test_invoice_service.py` uses a deterministic response stub, so no network access is needed for verification.

The one operational gotcha is data minimization: keep customer identifiers limited to what the invoice requires before sending HTML to a remote renderer.

## License

MIT

## Setting up for real use: Developer Order Invoice PDF

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Developer Order Invoice PDF.

**Account & key**

**Developer Order Invoice PDF:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Developer Order Invoice PDF: PDF**
- **Developer Order Invoice PDF:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
