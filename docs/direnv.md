
### About `direnv`

Direnv is a tool to load environments and settings per folder. This is saves time and sometimes makes commands more readable (example: omit `pdm run` prefix).

Files used by `direnv`:
* `.envrc` in the root of your project, to setup environment variables and use shell functions.
* `.direnvrc` in your home folder, to define shell functions that can be used by `.envrc` in projects.

For more details on `direnv`, see their [official site](https://direnv.net/).

Note that the files below can also be found in a [howto section in my dotfiles](https://github.com/lk16/dotfiles/blob/master/howto/direnv.md).

---

### Setup `direnv`

* On debian-based linux, run `sudo apt-get install direnv`, for other systems see [this page](https://direnv.net/docs/installation.html).
* Follow [instructions](https://direnv.net/docs/hook.html) for your shell
* Be sure to reload your shell config (for bash run `. ~/.bashrc`)
* Save this bash script as `.direnvrc` in your home folder. It defines the `layout_pdm` function which we use below.

```sh
layout_pdm() {
    PYPROJECT_TOML="${PYPROJECT_TOML:-pyproject.toml}"
    if [ ! -f "$PYPROJECT_TOML" ]; then
        log_status "No pyproject.toml found. Executing \`pmd init\` to create a \`$PYPROJECT_TOML\` first."
        pdm init --non-interactive --python "$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1-2)"
    fi

    VIRTUAL_ENV=$(pdm venv list | grep "^\*"  | awk -F" " '{print $3}')

    if [ -z "$VIRTUAL_ENV" ] || [ ! -d "$VIRTUAL_ENV" ]; then
        log_status "No virtual environment exists. Executing \`pdm info\` to create one."
	pdm info
        VIRTUAL_ENV=$(pdm venv list | grep "^\*"  | awk -F" " '{print $3}')
    fi

    PATH_add "$VIRTUAL_ENV/bin"
    export PDM_ACTIVE=1
    export VIRTUAL_ENV
}
```

* Next: save this bash script as `.envrc` in the root of this project. It calls the `layout_pdm` function, to set relevant environment variables. It also sets `AAA_STDLIB_PATH`, which is used by this project. The `.envrc` file is not tracked by git, [it is](../.gitignore) in `.gitignore`.
```sh
layout_pdm
export AAA_STDLIB_PATH=$(pwd)/stdlib
```
* Run `direnv allow` to tell `direnv` that this file is safe to run.
* You should be good to go. Try running this (note: no `pdm run` prefix):
```sh
./manage.py run 'fn main { "Hello world\n" . }'
```
* You can now omit `pdm run` prefix for all commands.
* Happy coding!
