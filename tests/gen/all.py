from pathlib import Path
from src import categen
from time import time
from PIL import Image
import colorama

colorama.init(autoreset=True)


def main(test: str = "all"):
    print(
        f"{colorama.Style.BRIGHT}interesting images"
        f"{colorama.Style.RESET_ALL} Tests / Generation ({test.capitalize()})\n"
    )

    eid = 69
    hid = 177013

    # Status Creeations
    stsmgr = categen.cli.StatusManager()
    gencrt = stsmgr.register("Generator Creation")

    if test == "all" or test == "text":
        etcrts = []
        for platform in categen.CatalogueEntry.markdown_map:
            etcrts.append(stsmgr.register(f"Entry Text Generation ({platform})"))

    if test == "all" or test == "image":
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
            stime = time()

            entries.append(generator.entry(markdown_type=platform))

            status.colour(colorama.Fore.GREEN)
            status.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 5)}")

    # Generation - Image
    if test == "all" or test == "image":
        tmbcrt.colour(colorama.Fore.YELLOW)
        stime = time()

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
