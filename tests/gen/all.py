from pathlib import Path
import colorama

from src import categen
from tests import utils

colorama.init(autoreset=True)


def main(test: str = "all"):
    print(
        f"{colorama.Style.BRIGHT}interesting images"
        f"{colorama.Style.RESET_ALL} Tests / Generation ({test.capitalize()})\n"
    )

    eid = 69
    hid = 177013

    collector = utils.TracebackCollector()
    stsmgr = categen.cli.StatusManager()

    # Status Creations
    gencrt = stsmgr.register("Generator Creation")

    if test == "all" or test == "text":
        etcrts = []
        for platform in categen.CatalogueEntry.markdown_map:
            etcrts.append(stsmgr.register(f"Entry Text Generation ({platform})"))

    if test == "all" or test == "image":
        tmbcrt = stsmgr.register("Thumbnail Generation")
    # Output Dir
    output_dir = Path(__file__).parent.joinpath("output/")

    if not output_dir.is_dir():
        from os import mkdir

        mkdir(output_dir)

    # Operations
    def gencreate():
        return categen.CatalogueEntry(
            eid=eid, hid=hid, score="test", desc="No description provided."
        )

    generator = utils.attempt(gencrt, collector, gencreate)

    if generator is None:
        collector.display()
        exit(1)

    # Generation - Text
    def textgen(platform):
        entries.append(generator.entry(markdown_type=platform))

    if test == "all" or test == "text":
        entries = []

        for platform, status in zip(categen.CatalogueEntry.markdown_map.keys(), etcrts):
            text = utils.attempt(status, collector, textgen, platform)
            if text is not None:
                with open(
                    output_dir.joinpath(f"entry-{platform}.txt"), "w", encoding="utf-8"
                ) as ef:
                    ef.write(text)

    # Generation - Image
    def imagegen():
        from PIL import Image

        preview = Image.open(
            str(Path(__file__).parent.joinpath("verycool23ar.png"))
        ).convert("RGBA")
        generator.thumbnail(preview=preview, suppress=True).save(
            output_dir.joinpath("thumbnail.png")
        )

    if test == "all" or test == "image":
        utils.attempt(tmbcrt, collector, imagegen)

    if len(collector.tracebacks) >= 1:
        collector.display()
        exit(1)


if __name__ == "__main__":
    main()
