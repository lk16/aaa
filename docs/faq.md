
### Frequently Asked Questions

##### What does the name "Aaa" mean?
Naming things is notoriously hard and naming a made up programming language is no exception. The name of this language is just the first letter of the Latin alphabet repeated three times. When code in this language doesn't work, its meaning becomes an [abbreviation](https://en.uncyclopedia.co/wiki/AAAAAAAAA!).

##### How did you get the idea to make a language?
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

##### What are the key features of Aaa?
See [language features and goals](./../README.md#language-features-and-goals).

##### How do I get started with Aaa?
See the [setup page](./setup.md).

##### What are the system requirements for Aaa?
Any machine that runs Python 3.11.3 and Rust should be able to run Aaa. If you run into issues, be sure to [open a ticket](https://github.com/lk16/aaa/issues/new).

##### Is Aaa open source or proprietary?
This project is open source and is distributed under the MIT license. This effectively means: do whatever you want with the code, but you can't sue me.

##### How do I report bugs or request features?
Both bug reports and feature requests can be sent to developers by opening a ticket.
Please first check [existing tickets](https://github.com/lk16/aaa/issues), before opening a new one.

##### What is the latest version of Aaa?
At time of writing there are no releases. Checking out the `main` branch and running `git pull` will get you the latest version.

##### Can I use Aaa on different operating systems?
Yes, see `What are the system requirements` question above.

##### What kind of applications can I build with Aaa?
Anything that:
* does not depend on other libraries (such as GUI's)
* is serious production / non-"pet project" software

That being said, various tools have been written using Aaa:
* a [HTTP server](../examples/http_server.aaa)
* a [HTTP client](../examples/http_client.aaa)
* a [shell](../examples/shell.aaa)
* a [sudoku solver](../examples/sudoku_solver.aaa)
* a [game of life](../examples/game_of_life.aaa) implementation ([What is this?](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life))

##### Are there any code examples or tutorials available for Aaa?
Yes, see the [examples documentation](./examples.md)

##### How do I create a new project or file in Aaa?
At this stage of the language:
* Create a new branch from `main`
* Create a new folder in `examples`
* Create a file `main.aaa` having a `main` function
* Start typing code

##### What is the package manager for Aaa?
There is none. There is not even a well-implemented import-system at time of writing.

##### How do I install and manage packages or dependencies?
Good one.

##### How can I handle errors or exceptions in Aaa?
We don't have exceptions in this language. Functions can return an enum, with one or more error variants.

##### What is the syntax for ... in Aaa?
See the [syntax documentation](./syntax.md)

##### How do I work with classes and objects in Aaa?
It mostly revolves around [the stack](./the_stack.md).

##### What are the available data structures and collections in Aaa?
At time of writing:
* `vec`, sometimes called "dynamic array" or "list"
* `map`, sometimes called "hash table", "hash map" or "dictionary"
* `set`

##### How can I work with files and file I/O?
Use the [builtin](./../stdlib/builtins.aaa) system calls.

##### Is there a standard coding style or best practices guide for Aaa?
Yes, see the [best practices](./best_practices.md) article.

##### How do I optimize and debug code in Aaa?


##### Are there any known limitations or caveats in Aaa?
Well, this is an enormous "pet project", so nothing is considered stable or production-ready. That being said, a lot of tests are in place to prevent major issues. The main limitations have more to do with features that are not implemented, rather than existing bugs.

Main things that are not implemented:
* interfaces (as in golang, [issue](https://github.com/lk16/aaa/issues/16))
* dealing with concurrency
* having a standard library
* having a well-implemented import system
* having a package manager

##### Can I contribute to the development of Aaa?
* Clone this repo and write some code in Aaa.
* Find bugs, suggest features on the [issues](https://github.com/lk16/aaa/issues) page.

##### How do I secure my Aaa applications?
Please don't use Aaa applications with any sensitive data. Do NOT use Aaa applications in a production setting.

##### What is the support and community around Aaa?
The [issues section](https://github.com/lk16/aaa/issues) on the GithHub repository.

##### Was ChatGPT or other AI involved in the development?
ChatGPT was not used for writing code, but sometimes used to assist in refactoring. Generally speaking all code in this repo was written by humans. ChatGPT did help coming up with some of the questions on this page.
