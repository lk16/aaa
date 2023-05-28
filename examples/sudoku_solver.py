# This is an extremely inefficient sudoku solver.
# It was translated from the solver in Aaa, keeping the code as close to the original as possible.

from typing import List, Set


def load_sudoku(s: str) -> List[int]:
    v: List[int] = []
    for i in range(len(s)):
        char = s[i : i + 1]
        try:
            n = int(char)
        except ValueError:
            if char == ".":
                v.append(0)
        else:
            v.append(n)

    if len(v) != 81:
        print(f"Expected 81 chars to be either a period or a digit, found {len(v)}\n")
        exit(1)

    return v


def print_sudoku(cells: List[int]) -> None:
    for y in range(9):
        if y in [3, 6]:
            print("------+-------+------")
        for x in range(9):
            if x in [3, 6]:
                print("| ", end="")
            i = 9 * y + x
            c = cells[i]
            if c == 0:
                print(". ", end="")
            else:
                print(f"{c} ", end="")
        print()


def solve_sudoku(cells: List[int]) -> None:
    solve_sudoku_recursive(cells, 0)


def solve_sudoku_recursive(cells: List[int], index: int) -> None:
    if check_sudoku(cells):
        if index == 81:
            print_sudoku(cells)
            exit(0)
        else:
            if cells[index] != 0:
                solve_sudoku_recursive(cells, index + 1)
            else:
                for n in range(1, 10):
                    cells[index] = n
                    solve_sudoku_recursive(cells, index + 1)

                    # If we get here the sudoku wasn't solved
                    # Wipe cell
                    cells[index] = 0


def check_sudoku(cells: List[int]) -> bool:
    # NOTE: use `all()` instead of `and` to prevent python boolean short-circuiting
    return all(
        [
            check_sudoku_row(cells, 0),
            check_sudoku_row(cells, 1),
            check_sudoku_row(cells, 2),
            check_sudoku_row(cells, 3),
            check_sudoku_row(cells, 4),
            check_sudoku_row(cells, 5),
            check_sudoku_row(cells, 6),
            check_sudoku_row(cells, 7),
            check_sudoku_row(cells, 8),
            check_sudoku_column(cells, 0),
            check_sudoku_column(cells, 1),
            check_sudoku_column(cells, 2),
            check_sudoku_column(cells, 3),
            check_sudoku_column(cells, 4),
            check_sudoku_column(cells, 5),
            check_sudoku_column(cells, 6),
            check_sudoku_column(cells, 7),
            check_sudoku_column(cells, 8),
            check_sudoku_block(cells, 0, 0),
            check_sudoku_block(cells, 0, 3),
            check_sudoku_block(cells, 0, 6),
            check_sudoku_block(cells, 3, 0),
            check_sudoku_block(cells, 3, 3),
            check_sudoku_block(cells, 3, 6),
            check_sudoku_block(cells, 6, 0),
            check_sudoku_block(cells, 6, 3),
            check_sudoku_block(cells, 6, 6),
        ]
    )


def check_sudoku_row(cells: List[int], y: int) -> bool:
    ok = True
    values: Set[int] = set()

    for x in range(9):
        n = cells[9 * y + x]

        if n != 0 and n in values:
            ok = False

        values.add(n)

    return ok


def check_sudoku_column(cells: List[int], x: int) -> bool:
    ok = True
    values: Set[int] = set()

    for y in range(9):
        n = cells[9 * y + x]

        if n != 0 and n in values:
            ok = False

        values.add(n)

    return ok


def check_sudoku_block(cells: List[int], x_start: int, y_start: int) -> bool:
    ok = True
    values: Set[int] = set()

    for y_delta in range(3):
        for x_delta in range(3):
            y = y_start + y_delta
            x = x_start + x_delta
            n = cells[y * 9 + x]

            if n != 0 and n in values:
                ok = False

            values.add(n)

    return ok


def main() -> None:
    solve_sudoku(
        load_sudoku(
            "9.458....2.8..9..........1...5743.8...........9.8623...5..........3..6.4....571.2"
        )
    )

    # unreachable if sudoku is solved
    print("Sudoku solving failed")
    exit(1)


if __name__ == "__main__":
    main()
