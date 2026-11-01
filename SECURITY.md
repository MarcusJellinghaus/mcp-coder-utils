# Security Policy

## Reporting a Vulnerability

Report vulnerabilities through GitHub private vulnerability reporting only: in this repository, go to **Security → Report a vulnerability**.

Do not open public issues for security problems.

## Response

Reports are handled on a best-effort basis. There is no fixed response time.

## Supported Versions

Only the latest release on PyPI receives security fixes.

## Scope

In scope are bypasses of intended restrictions, such as:

- path security (escaping the project directory via `fs.path_security`)
- secret redaction (credentials leaking past `redaction` into logs)
- subprocess handling (command injection through `subprocess_runner` / `subprocess_streaming`)
