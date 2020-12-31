from .catentry import CatalogueEntry
from time import sleep, time
from pathlib import Path
from PIL import Image
from os import mkdir
import colorama

colorama.init()


class Validator:
    class Error(Exception):
        pass

    def convert_int(text: str) -> int:
        try:
            return int(text)

        except Exception:
            raise Validator.Error("Cannot be converted to int!")

    def entry_id(resp: str) -> str:
        resp = Validator.convert_int(resp)

        if resp > 999:
            raise Validator.Error("Cannot surpass 3 digits!")

        return resp

    def doujin_id(resp) -> int:
        resp = Validator.convert_int(resp)

        if resp > 999999:
            raise Validator.Error("Cannot surpass 6 digits!")

        return resp

    def file_exist(resp) -> Path:
        if not Path(resp).is_file():
            raise Validator.Error("File non-existant!")
        else:
            return Path(resp)

    def dir_create(resp) -> Path:
        if not Path(resp).is_dir():
            from shutil import rmtree

            try:
                mkdir(resp)

            except Exception as e:
                raise Validator.Error(f"Directory cannot be made! ({e})")

            else:
                rmtree(resp)

        return Path(resp)

    def platform(resp) -> list:
        if "," in resp:
            resp = resp.split(",")
        elif ";" in resp:
            resp = resp.split(";")
        elif ":" in resp:
            resp = resp.split(":")

        resp = [platform.lstrip() for platform in resp]

        incorrect = []

        for platform in resp:
            if platform not in CatalogueEntry.markdown_map:
                incorrect.append(platform)

        if len(incorrect) > 0:
            raise Validator.Error(f'Platform(s) {", ".join(incorrect)} are invalid!')

        return resp

    def yesno(resp) -> bool:
        if resp == "y" or resp == "Y":
            return True
        elif resp == "n" or resp == "N":
            return False
        else:
            raise Validator.Error("Invalid response!")


def gather_responses() -> dict:
    def ask(query, validator, required=False):
        print(f"┌─ {colorama.Style.BRIGHT}{query}{colorama.Style.RESET_ALL}")
        while True:
            try:
                response = input("└> ")

                if response == "" and required:
                    raise Validator.Error("Response required!")

                response = validator(response)

            except Validator.Error as e:
                print("\033[2K", end="\r")
                print(
                    "\033[1A"
                    f"└> {colorama.Style.BRIGHT}{colorama.Fore.RED}{e}"
                    f"{colorama.Style.RESET_ALL}",
                    end="\r",
                )
                sleep(2)
                print("\033[2K", end="\r")

            else:
                break

        return response

    responses = {}

    request_validate_map = {
        # "Displayed Text": (Validator function, responses key, required)
        "Entry ID": (Validator.entry_id, "eid", True),
        "Doujin ID": (Validator.doujin_id, "hid", True),
        "Score (out of 10)": (str, "score", True),
        "Description (optional)": (str, "desc", False),
        "Preview Image": (Validator.file_exist, "preview", True),
        "Output Directory": (Validator.dir_create, "output_dir", True),
        "Entry Platform Export (optional)": (Validator.platform, "platform", False),
        "Export Generator? (yY/nN)": (Validator.yesno, "export", True),
    }

    for query, payload in request_validate_map.items():
        responses[payload[1]] = ask(query, payload[0], payload[2])
        print()

    return responses


def main():
    print(
        f"{colorama.Style.BRIGHT}interesting images{colorama.Style.RESET_ALL} "
        "Catalogue Entry Generator"
    )
    responses = gather_responses()

    ceg = CatalogueEntry(
        eid=responses["eid"],
        hid=responses["hid"],
        score=responses["score"],
        desc=responses["desc"],
    )

    preview = Image.open(str(responses["preview"]))
    output_dir = responses["output_dir"]

    print(
        f"{colorama.Style.BRIGHT}Operations{colorama.Style.RESET_ALL}\n"
        f"├─ Entry Generation\n"
        f"└─ Thumbnail Generation"
    )

    # Entry Generation
    print(
        "\033[2F"
        f"{colorama.Fore.YELLOW}├─ Entry Generation"
        f"{colorama.Style.RESET_ALL}",
        end="\r",
    )

    entries = {}
    for platform in responses["platform"]:
        entries[platform] = ceg.entry(markdown_type=platform)

    print(
        f"├─ {colorama.Fore.GREEN}Entry Generation" f"{colorama.Style.RESET_ALL}",
        end="\r",
    )

    print("\033[1E", end="\r")

    # Thumbnail Generation
    print(
        f"\r└─ {colorama.Fore.LIGHTYELLOW_EX}Thumbnail Generation"
        f"{colorama.Style.RESET_ALL}",
        end="\r",
    )
    stime = time()

    thumbnail = ceg.thumbnail(preview=preview, suppress=True)

    otime = round(time() - stime, 3)

    print(
        f"\r└─ {colorama.Fore.GREEN}Thumbnail Generation"
        f"{colorama.Style.DIM}{colorama.Fore.RESET}"
        f" Time Taken: {otime}{colorama.Style.RESET_ALL}"
    )

    # Output
    if not output_dir.is_dir():
        mkdir(output_dir)

    for platform, text in entries.items():
        with open(
            output_dir.joinpath(f"entry-{platform}.txt"), "w", encoding="utf-8"
        ) as ef:
            ef.write(text)

    thumbnail.save(output_dir.joinpath("thumbnail.png"))

    if responses["export"]:
        with open(output_dir.joinpath("ceg.dill"), "wb") as cegdf:
            cegdf.write(ceg.export())


main()
