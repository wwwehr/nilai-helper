# Setup
```bash
uv venv --python=$(which python3)
source .venv/bin/activate
uv pip install -e .
```

# Run an example
```bash
python examples/healthcare-2-doctor-feelgood.py testdata/profile-and-symptoms-v1.json
```
