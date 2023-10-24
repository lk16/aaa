### How to run examples

```sh
# Run the obligatory hello world example
pdm run ./manage.py run 'fn main { "Hello world\n" . }'

# Run code from a file. Implements the famous fizzbuzz interview question.
pdm run ./manage.py run examples/fizzbuzz.aaa

# Run bare-bones HTTP server in Aaa
pdm run ./manage.py run examples/http_server.aaa

# Send request from different shell
curl http://localhost:8080
```

More examples can be found in the [examples folder](./../examples/)

### How to run tests

```sh
# Run tests written in Aaa
pdm run ./manage.py test .

# Run tests written in Python
pdm run pytest
```
