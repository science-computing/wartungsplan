# Wartungsplan development documentation

## Run the test suite

```
source venv/bin/activate
# install optional dependencies
pip install ".[otrs,exchange]"
test/test.py
```

## Pypi release

 * Update CHANGELOG.md
 * Set the correct version in `pyproject.toml`
 * Set a git tag on the commit
 * Commit to `main`.

Then create and upload the package to Pypi:

```
cd /tmp
python3 -m venv venv
source venv/bin/activate
git clone git@github.com:science-computing/wartungsplan
cd wartungsplan
pip install -r dev-requirements.txt
python3 -m build --sdist .
python3 -m build --wheel .
twine upload dist/*
```

Note: Dev requirements are maintained in `dev-requirements.txt` while runtime
dependencies are hold inside `pyproject.toml`.


## Container

Build:

```
podman build -t wartungsplan .
```

Run:

```
podman run -it -v ./plan.conf:/etc/plan.conf -v ./test.ical:/data/test.ical wartungsplan:latest list
```


## TLS server OTRS backend test

```
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
openssl s_server -key key.pem -cert cert.pem -accept 4433 -www
```
