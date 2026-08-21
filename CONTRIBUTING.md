# Contributing

Create a focused branch and pull request. New agent behavior requires a versioned prompt, structured schema, deterministic controls where possible, positive/negative/security tests, evaluation cases, and documentation. Do not weaken approval, traceability, path, command, or tenant controls.

Run before opening a PR:

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy app tests
pytest
python scripts/validate_prompts.py
python scripts/run_evaluations.py --provider mock
cd automation/playwright && npm ci && npm run format:check && npm run lint && npm run typecheck && npm test
```

Never commit credentials, generated execution evidence containing personal data, `.env`, databases, or provider responses with sensitive content.

