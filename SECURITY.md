# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please **do not** open a public issue for security-sensitive reports.

1. Email or use GitHub **Private vulnerability reporting** on this repository when enabled.  
2. Include reproduction steps, affected component (safety, drivers, LLM tool-calling, etc.), and impact.  
3. Allow reasonable time for a fix before public disclosure.

## Robot-specific notes

- Treat motor enable and e-stop bypass bugs as **high severity**.  
- Prompt injection that causes unsafe motion commands should be reported.  
- Never commit API keys; NestWeaver is designed for **local** Ollama by default.
