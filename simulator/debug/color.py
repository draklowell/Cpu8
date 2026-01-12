"""
ANSI color codes and terminal styling utilities.
"""


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def colored(text: str, *colors: str) -> str:
    """
    Color the text

    Args:
        text (str): The text to be colored

    Returns:
        str: The colored text
    """
    return "".join(colors) + text + Color.RESET


def print_header(text: str, char: str = "-", width: int = 30) -> None:
    """
    Print a header line with centered text
    Args:
        text (str): The header text
        char (str, optional): The character to use for the line. Defaults to "-".
        width (int, optional): The total width of the header line. Defaults to 30.
    """
    padding = (width - len(text) - 2) // 2
    line = char * padding + f" {text} " + char * padding
    if len(line) < width:
        line += char
    print(colored(line, Color.CYAN, Color.BOLD))


def print_separator(char: str = "-", width: int = 30) -> None:
    """
    Print a separator line
    Args:
        char (str, optional): The character to use for the line. Defaults to "-".
        width (int, optional): The total width of the separator line. Defaults to 30.
    """
    print(colored(char * width, Color.GRAY))
