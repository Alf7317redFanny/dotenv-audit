# dotenv-audit

A utility that scans project directories for `.env` files and flags exposed secrets or mismatched keys across environments.

---

## Installation

```bash
pip install dotenv-audit
```

Or install from source:

```bash
git clone https://github.com/your-username/dotenv-audit.git
cd dotenv-audit
pip install .
```

---

## Usage

Run an audit against your project directory:

```bash
dotenv-audit scan ./my-project
```

Compare keys across multiple environment files:

```bash
dotenv-audit compare .env .env.staging .env.production
```

**Example output:**

```
[WARN]  .env.production  — Missing key: DATABASE_URL
[ALERT] .env             — Possible secret exposed: AWS_SECRET_KEY matches common pattern
[OK]    .env.staging     — All keys accounted for
```

You can also use it programmatically:

```python
from dotenv_audit import audit

results = audit.scan("./my-project")
for finding in results:
    print(finding.level, finding.message)
```

---

## Options

| Flag | Description |
|------|-------------|
| `--strict` | Exit with non-zero code if any issues are found |
| `--ignore` | Comma-separated list of keys to ignore |
| `--format` | Output format: `text` (default) or `json` |

---

## License

This project is licensed under the [MIT License](LICENSE).