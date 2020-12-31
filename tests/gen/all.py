from pathlib import Path
from src import categen
from time import time
from PIL import Image
import colorama

colorama.init(autoreset=True)


class StatusManager:
    class Status:
        def __init__(self, sid, manager):
            self.manager = manager
            self.id = sid - 1

        def colour(self, colour=colorama.Style.RESET_ALL):
            self.manager.operations[self.id]["colour"] = colour
            self.manager.update(self.id)

        def text(self, text=""):
            self.manager.operations[self.id]["info"] = text
            self.manager.update(self.id)

    def __init__(self, message: str = "Operations"):
        self.operations = []
        self.current = 0

        print(f"{colorama.Style.BRIGHT}{message}")

    def update(self, sid):
        msgdata = self.operations[sid]

        if self.current > sid:
            diff = self.current - sid
            print(f"\033[{diff}A", end="\r")
        else:
            diff = sid - self.current
            print(f"\033[{diff}A", end="\r")

        info = "" if msgdata["info"] == "" else f' - {msgdata["info"]}'

        print(
            f"\033[2K"
            f'{msgdata["prefix"]}{msgdata["colour"]}{msgdata["message"]}{info}'
            f"\033[{diff}B",
            end="\r",
        )

    def register(self, message, info=None, colour=None) -> Status:
        prefix = " └─ "

        if len(self.operations) >= 1:
            print("\033[1A" " ├─ " "\033[1B", end="\r")
            self.operations[-1]["prefix"] = " ├─ "

        self.operations.append(
            {
                "prefix": prefix,
                "colour": "" if colour is None else colour,
                "message": message,
                "info": "" if info is None else info,
            }
        )

        print(
            f'{prefix}{"" if colour is None else colour}'
            f'{message}{"" if info is None else f" - {info}"}'
        )

        self.current += 1

        return self.Status(sid=len(self.operations), manager=self)


def main(test: str = "all"):
    print(
        f"{colorama.Style.BRIGHT}interesting images"
        f"{colorama.Style.RESET_ALL} Tests / Generation ({test.capitalize()})\n"
    )

    eid = 69
    hid = 177013

    # Status Creeations
    stsmgr = StatusManager()
    gencrt = stsmgr.register("Generator Creation")

    if test == "all":
        etcrts = []
        for platform in categen.CatalogueEntry.markdown_map:
            etcrts.append(stsmgr.register(f"Entry Text Generation ({platform})"))
        tmbcrt = stsmgr.register("Thumbnail Generation")

    elif test == "text":
        etcrts = []
        for platform in categen.CatalogueEntry.markdown_map:
            etcrts.append(stsmgr.register(f"Entry Text Generation ({platform})"))

    elif test == "image":
        tmbcrt = stsmgr.register("Thumbnail Generation")

    resout = stsmgr.register("Result Output")

    # Operations
    gencrt.colour(colorama.Fore.YELLOW)
    stime = time()

    generator = categen.CatalogueEntry(
        eid=eid, hid=hid, score="test", desc="No description provided."
    )

    gencrt.colour(colorama.Fore.GREEN)
    gencrt.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 5)}")

    # Generation - Text
    if test == "all" or test == "text":
        entries = []
        for platform, status in zip(categen.CatalogueEntry.markdown_map.keys(), etcrts):
            status.colour(colorama.Fore.YELLOW)

            entries.append(generator.entry(markdown_type=platform))

            status.colour(colorama.Fore.GREEN)
            status.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 5)}")

    # Generation - Image
    if test == "all" or test == "image":
        tmbcrt.colour(colorama.Fore.YELLOW)

        preview = Image.open(
            str(Path(__file__).parent.joinpath("verycool23ar.png"))
        ).convert("RGBA")
        thumbnail = generator.thumbnail(preview=preview, suppress=True)

        tmbcrt.colour(colorama.Fore.GREEN)
        tmbcrt.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 5)}")

    # Output
    output_dir = Path(__file__).parent.joinpath("output/")

    resout.colour(colorama.Fore.YELLOW)
    stime = time()

    if test == "all" or test == "text":
        for platform, text in zip(categen.CatalogueEntry.markdown_map.keys(), entries):
            with open(
                output_dir.joinpath(f"entry-{platform}.txt"), "w", encoding="utf-8"
            ) as ef:
                ef.write(text)

    if test == "all" or test == "image":
        thumbnail.save(output_dir.joinpath("thumbnail.png"))

    resout.colour(colorama.Fore.GREEN)
    resout.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 5)}")


if __name__ == "__main__":
    main()
