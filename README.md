# Regnskab

To start, create `regnskabsite/settings/__init__.py` with the following contents:

```
from .common import *

DEBUG = True
SECRET_KEY = r'''fill me in from pwgen -sy 50 1'''
```

... where you use `pwgen -sy 50 1` to create a random secret key.
