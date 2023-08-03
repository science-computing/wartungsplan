# Wartungsplan development documentation

## Run the test suite

   source venv/bin/activate
   # install optional dependencies
   pip install pyotrs

## Pypi release

   cd /tmp
   python3 -m venv venv
   source venv/bin/activate
   git clone git@github.com:science-computing/wartungsplan
   cd wartungsplan
   pip install -r dev-requirements.txt
   python3 -m build --sdist .
   python3 -m build --wheel .
   twine upload dist/*
