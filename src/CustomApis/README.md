# Custom APIs

Custom APIs are the only mutation boundary for PCF schedule/configuration commands. Contracts are versioned and include authorization, validation, correlation, idempotency, row-version concurrency, deterministic errors, affected-scope results, and audit evidence.

Initial endpoint families include validation/execution, publish/rollback, and board-version validation/activation. `Contracts` must remain transport-focused; `Handlers` delegate to shared application services.

