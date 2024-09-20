class Code:
    def __init__(
        self, line: str | None = None, unindent: int = 0, indent: int = 0
    ) -> None:
        self.lines: list[str] = []
        self.indent_level = 0

        if line is not None:
            self.__add_line(line, bool(unindent), bool(indent))

    def __add_line(self, line: str, unindent: bool, indent: bool) -> None:
        if line.endswith("\n"):
            raise ValueError("Line should not end with newline.")

        if unindent:
            self.indent_level -= 1

        if self.indent_level < 0:
            raise ValueError("Indentation can't be negative.")

        indented_line = "    " * self.indent_level + line
        self.lines.append(indented_line)

        if indent:
            self.indent_level += 1

    def __add_code(self, code: "Code") -> None:
        for line in code.lines:
            self.__add_line(line, False, False)

    def add(self, added: "str | Code", unindent: int = 0, indent: int = 0) -> None:
        if isinstance(added, str):
            self.__add_line(added, bool(unindent), bool(indent))
        elif isinstance(added, Code):
            self.__add_code(added)

    def add_joined(self, join_line: str, joined: list["Code"]) -> None:
        for offset, line in enumerate(joined):
            self.add(line)
            if offset != len(joined) - 1:
                self.add(join_line)

    def get(self) -> str:
        return "\n".join(self.lines) + "\n"
