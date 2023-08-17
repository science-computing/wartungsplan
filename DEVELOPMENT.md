# Wartungsplan development documentation

## Run the test suite

```
source venv/bin/activate
# install optional dependencies
pip install pyotrs
```

## Pypi release

Set the correct version in `pyproject.toml`, set a git tag on the commit, and
commit to `main`.

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
dependencies are hold in inside `pyproject.toml`.


## Container

Build:

```
podman build -t wartungsplan .
```

Run:

```
podman run -it -v ./plan.conf:/etc/plan.conf -v ./test.ical:/data/test.ical wartungsplan:latest list
```
