# Setup

Using a python venv at the root of the project is suggested.

```
tnc-edge-service $ python3 -m venv venv
tnc-edge-service $ . ./venv/bin/activate
(venv) tnc-edge-service $ pip install -r requirements.txt
```

# Invocation

Tests should be invoked from the root of the project using `python -m` syntax.

Some tests use `click` module for intuitive command line arguments.

ex:

```
(venv) tnc-edge-service $ python -m tests.ondeck_json_to_tracks --help
Usage: python -m tests.ondeck_json_to_tracks [OPTIONS] COMMAND [ARGS]...

Options:
  --dbname TEXT
  --dbuser TEXT
  --help         Show this message and exit.

Commands:
  archive
```


