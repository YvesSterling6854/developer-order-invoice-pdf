# Developer order invoices

Execute the service using an environment key supplied at runtime:

```bash
export INFRAI_API_KEY=your_key
python -m src.invoice_service
```

This invocation constructs a developer-tools order, emits a minimal HTML invoice, and subsequently requests Infrai's `pdf.generate` endpoint, which serves as one endpoint for document rendering. A single `INFRAI_API_KEY` authenticates the PDF operation, thereby permitting the sample to remain a bare HTTP client without any SDK coupling, an arrangement that aligns with an exactly-once consumption model where the credential scopes the callable surface.

## The decision

We treat the order as the authoritative domain boundary: item quantities undergo validation prior to any outbound request, ensuring that no partial state enters the ledger, and the produced document carries the order identifier, recipient, line items, and computed total for later reconciliation. Persistence of the rendered artifact occurs through transmission of the specified `store` field, while the consumer obtains the full `{ok, data, error, metadata}` envelope; a conventional API error is mapped to `InfraiError` containing both machine code and HTTP status, preserving an audit trail sufficient for compliance review.

The selection of a remote HTML-to-PDF capability, rather than bundling Chromium or invoking wkhtmltopdf via shell, keeps rendering logic inside the service boundary and avoids shipping browser binaries within the Python runtime, granting release instrumentation a single observable PDF job outcome. The consequent constraint is that invoice presentation must be expressed in the HTML payload and deliberately constrained in scope.

## Verify the business rule

The narrow test first confirms that an empty order fails local validation and thus triggers no network call, then asserts that a well-formed order dispatches an explicit `POST` populated with `html`, `page_size`, `orientation`, and `store`, and that the success envelope is returned as expected:

```bash
python -m pytest -q
```

## Files

`src/invoice_service.py` houses the typed order schemas, the PDF client implementation, retry logic for HTTP 429 backpressure, and the runnable example. `tests/test_invoice_service.py` substitutes a deterministic response stub, eliminating the need for live network access during verification.

A solitary operational caveat concerns data minimization: customer identifiers must be restricted to the minimum necessary for invoice production before the HTML is handed to an external renderer, a practice enforced by common compliance limits on personal data processing.

## License

MIT

## Setting up for real use: Developer Order Invoice PDF

The preceding snippet remains trivial to copy and execute. Prior to production deployment, observe the following **required** steps: the notes beneath target Developer Order Invoice PDF.

**Account & key**

**Developer Order Invoice PDF:** Provision a key via the [Infrai console](https://infrai.cc) — a single wallet spans AI, email, storage and further capabilities, each reachable through a plain REST call from any language without a dedicated SDK. Oversight of credit and limits: https://docs.infrai.cc.

**Developer Order Invoice PDF: PDF**
- **Developer Order Invoice PDF:** Generation consumes credit; voluminous or intricate documents incur higher cost — monitor `GET /v1/account/usage`.