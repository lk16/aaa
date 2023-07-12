from typing import List, Optional


class Code:
    def __init__(self, line: Optional[str] = None, l: int = 0, r: int = 0) -> None:
        self.lines: List[str] = []
        self.indent_level = 0

        if line is not None:
            self.__add_line(line, bool(l), bool(r))

    def __add_line(self, line: str, l: bool, r: bool) -> None:
        if line.endswith("\n"):
            raise ValueError("Line should not end with newline.")

        if l:
            self.indent_level -= 1

        if self.indent_level < 0:
            raise ValueError("Indentation can't be negative.")

        indented_line = "    " * self.indent_level + line
        self.lines.append(indented_line)

        if r:
            self.indent_level += 1

    def __add_code(self, code: "Code") -> None:
        for line in code.lines:
            self.__add_line(line, False, False)

    def add(self, added: "str | Code", l: int = 0, r: int = 0) -> "Code":
        if isinstance(added, str):
            self.__add_line(added, bool(l), bool(r))
        elif isinstance(added, Code):
            self.__add_code(added)

        return self

    def get(self) -> str:
        return "\n".join(self.lines) + "\n"
