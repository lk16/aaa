
### How to setup this project

Start by cloning this repository.

All these commands should be run from the root of this repository.

This project requires Python 3.12.1 or later, consider using [pyenv](https://github.com/pyenv/pyenv) to select a python version.

```sh
# Download python 3.12.1
pyenv install 3.12.1

# Use it in this project
pyenv local 3.12.1
```

This project also requires Rust, see instructions [here](https://www.rust-lang.org/tools/install) on how to install.

After you setup Rust and Python, run the following commands.

```sh
# Install dependencies
pdm install

# Tell Aaa where the standard library lives
export AAA_STDLIB_PATH=$(pwd)/stdlib

# Run hello world program
pdm run ./manage.py run 'fn main { "Hello world\n" . }'

# Run tests
pdm run pytest

# Setup pre-commit hooks
pdm run pre-commit install
```

Now you can start running code in Aaa or develop the language!

Tips to make your life better:
* Enable syntax highlighting for VS Code, enable the [Aaa language extension](./aaa-vscode-extension/README.md)
* Use `direnv` as described [here](./direnv.md) so you don't have to type `pdm run` all the time.
