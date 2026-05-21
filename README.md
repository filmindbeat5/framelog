# framelog

Lightweight logging utility for tracking render job statuses across distributed media servers.

---

## Installation

```bash
pip install framelog
```

---

## Usage

```python
from framelog import RenderLogger

logger = RenderLogger(server_id="render-node-03", log_path="/var/log/framelog")

# Log a job status update
logger.log(job_id="job_8821", frame=142, status="completed", duration=4.37)

# Query recent failures
failures = logger.query(status="failed", limit=10)
for entry in failures:
    print(entry)
```

**Example output:**

```
[2024-11-12 08:45:01] [render-node-03] job_8821 | frame=142 | status=completed | duration=4.37s
[2024-11-12 08:44:58] [render-node-01] job_8819 | frame=137 | status=failed | duration=0.00s
```

framelog writes structured logs in JSON format by default, making them easy to ingest into external monitoring tools like Grafana or Elasticsearch.

---

## Features

- Minimal setup — works out of the box with no external dependencies
- Thread-safe logging across multiple render nodes
- Supports JSON and plaintext output formats
- Simple query interface for filtering by job, frame, or status

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.