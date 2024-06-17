# About API

This folder contains all HTTP-api code. The Flask App `edge_http.py` will import files in this folder and serve them as api routes, using Flask's register_blueprint feature.

Relevant code in `edge_http.py`:

```
from api import deckhand
app.register_blueprint(deckhand, url_prefix='/deckhand')
```
