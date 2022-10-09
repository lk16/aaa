from typing import Optional


def format_str(string: str, max_length: Optional[int] = None) -> str:  # pragma: nocover
    string = string.replace("\n", "\\n")

    if max_length is not None and len(string) > max_length:
        string = string[: max_length - 1] + "…"

    return string
