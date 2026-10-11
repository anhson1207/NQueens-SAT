

def positions_to_board(
    positions: list[tuple[int, int]],
    n: int,
) -> list[list[str]]:
    if n < 1:
        raise ValueError("n must be at least 1")

    board = [["." for _ in range(n)] for _ in range(n)]
    for row, col in positions:
        if not (0 <= row < n and 0 <= col < n):
            raise ValueError(f"Position {(row, col)} is outside a {n}x{n} board")
        board[row][col] = "Q"
    return board


def board_to_string(board: list[list[str]]) -> str:
    return "\n".join(" ".join(row) for row in board)


def print_board(board: list[list[str]]) -> None:
    print(board_to_string(board))


def columns_to_positions(columns: list[int]) -> list[tuple[int, int]]:
    return list(enumerate(columns))
