# cronwatch

Lightweight cron job monitor that sends alerts when jobs fail or run too long.

## Installation

```bash
pip install cronwatch
```

## Usage

Wrap any cron command with `cronwatch` to monitor it:

```bash
cronwatch --name "daily-backup" --timeout 300 -- /usr/local/bin/backup.sh
```

Configure alerts in `~/.cronwatch.yml`:

```yaml
alerts:
  email: ops@example.com
  slack_webhook: https://hooks.slack.com/services/xxx/yyy/zzz

jobs:
  daily-backup:
    timeout: 300       # seconds before alert fires
    on_failure: true   # alert if job exits non-zero
    on_timeout: true   # alert if job exceeds timeout
```

Then add it to your crontab:

```
0 2 * * * cronwatch --name "daily-backup" --timeout 300 -- /usr/local/bin/backup.sh
```

cronwatch will send an alert if the job:
- Exits with a non-zero status code
- Exceeds the configured timeout
- Fails to start

## Options

| Flag | Description |
|------|-------------|
| `--name` | Unique job name for identification in alerts |
| `--timeout` | Max allowed runtime in seconds |
| `--config` | Path to config file (default: `~/.cronwatch.yml`) |
| `--quiet` | Suppress stdout output from the wrapped command |

## License

MIT