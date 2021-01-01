from traceback import print_tb
from time import time
import colorama

from src import categen


class TracebackCollector:
    def __init__(self):
        self.tracebacks = []

    def add(self, status: categen.cli.StatusManager.Status, exc: Exception):
        self.tracebacks.append(
            (
                f"{colorama.Style.BRIGHT}{colorama.Fore.RED}"
                f"[{status.manager.operations[status.id]['message']}] "
                f"{exc.__class__.__name__}: {exc}\n{colorama.Style.RESET_ALL}",
                exc.__traceback__,
            )
        )

    def display(self):
        for payload in self.tracebacks:
            msg, obj = payload

            print(f"\n{msg}", end="\r")
            print_tb(obj)


def attempt(
    status: categen.cli.StatusManager.Status,
    collector: TracebackCollector,
    operation,
    *args,
    ret=None,
):
    status.colour(colorama.Fore.YELLOW)
    stime = time()

    try:
        stime = time()
        result = operation(*args)

    except Exception as e:
        status.colour(colorama.Fore.RED)
        status.text(f"{e.__class__.__name__}: {e}")
        collector.add(status, e)
        return ret

    else:
        if isinstance(result, dict) and "text" in result:
            add_text = f'{result["text"]} - '
        else:
            add_text = ""

        status.colour(colorama.Fore.GREEN)
        status.text(
            f"{colorama.Style.DIM}{add_text}Time Taken: {round(time() - stime, 3)}"
        )

        if isinstance(result, dict) and "result" in result:
            return result["result"]
        else:
            return result
