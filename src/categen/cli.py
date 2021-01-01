from .catentry import CatalogueEntry, data
from time import sleep, time
from pathlib import Path
from PIL import Image
from os import mkdir
import colorama

colorama.init()


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
            f'{msgdata["prefix"]}{msgdata["colour"]}{msgdata["message"]}'
            f"{colorama.Style.RESET_ALL}{info}"
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
        resp = "." if resp == "" else resp

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
        resp = "Telegram" if resp == "" else resp
        if "," in resp:
            resp = resp.split(",")
        elif ";" in resp:
            resp = resp.split(";")
        elif ":" in resp:
            resp = resp.split(":")
        else:
            resp = [resp]

        resp = [platform.lstrip() for platform in resp if platform != ""]

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
        elif resp == "":
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
        "Description (Optional)": (str, "desc", False),
        "Preview Image": (Validator.file_exist, "preview", True),
        "Output Directory (Optional: .)": (Validator.dir_create, "output_dir", False),
        "Entry Platform Export (Optional)": (Validator.platform, "platform", False),
        "Export Generator? (yY/nN - Optional: No)": (Validator.yesno, "export", False),
    }

    try:
        config = data.Config()
        if data.Format.current_ver() != data.Format.latest_ver(
            config["Repository"]["latest_placements"]
        ):
            responses["update"] = ask(
                "Different Format version found online, "
                f"C:{data.Format.current_ver()} != "
                f"L:{data.Format.latest_ver(config['Repository']['latest_placements'])}. "
                "Update? (yY/nN - Optional: No)",
                Validator.yesno,
                False,
            )
            print()

        else:
            responses["update"] = False

    except Exception as e:
        print(
            f"{colorama.Style.DIM}{colorama.Fore.RED}"
            f"Warning: Error when trying to compare Format versions ({e})"
        )
        responses["update"] = False

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

    # Status Handling
    stsmgr = StatusManager()

    if responses["update"]:
        updtop = stsmgr.register("Repository Update")

    etcrts = []
    for platform in responses["platform"]:
        etcrts.append(stsmgr.register(f"Entry Text Generation ({platform})"))

    imgcrt = stsmgr.register("Thumbnail Generation")

    outops = stsmgr.register("Output Generated Files")

    if responses["export"]:
        genexp = stsmgr.register("Generator Serialization")

    # Repository Update
    if responses["update"]:
        updtop.colour(colorama.Fore.YELLOW)
        stime = time()

        try:
            ceg.format.pull()

        except Exception:
            from shutil import rmtree

            ceg.format.backup()
            rmtree(ceg.config["Repository"]["path"])
            ceg.format.clone()

        updtop.colour(colorama.Fore.GREEN)
        updtop.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 4)}")

    # Entry Generation
    entries = []
    for status, platform in zip(etcrts, responses["platform"]):
        status.colour(colorama.Fore.YELLOW)
        stime = time()

        entries.append(ceg.entry(markdown_type=platform))

        status.colour(colorama.Fore.GREEN)
        status.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 4)}")

    # Thumbnail Generation
    imgcrt.colour(colorama.Fore.YELLOW)
    stime = time()

    thumbnail = ceg.thumbnail(preview=preview, suppress=True)

    imgcrt.colour(colorama.Fore.GREEN)
    imgcrt.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 4)}")

    # Output
    outops.colour(colorama.Fore.YELLOW)

    if not output_dir.is_dir():
        mkdir(output_dir)

    # Entry Texts
    for platform, text, status in zip(responses["platform"], entries, etcrts):
        output_file = output_dir.joinpath(f"entry-{platform}.txt")
        outops.text(f"{platform} Entry Text --> {output_file}")
        with open(output_file, "w", encoding="utf-8") as ef:
            status.text(f"Saved as {output_file}.")
            ef.write(text)

    # Thumbnail
    thumbnail_path = output_dir.joinpath("thumbnail.png")
    outops.text(f"Thumbnail --> {thumbnail_path}")
    thumbnail.save(thumbnail_path)
    imgcrt.text(f"Saved as {thumbnail_path}")

    if responses["export"]:
        genexp.colour(colorama.Fore.YELLOW)
        stime = time()

        with open(output_dir.joinpath("ceg.dill"), "wb") as cegdf:
            cegdf.write(ceg.export())

        genexp.colour(colorama.Fore.GREEN)
        genexp.text(f"{colorama.Style.DIM}Time Taken: {round(time() - stime, 4)}")

    outops.text()
    outops.colour(colorama.Fore.GREEN)


if __name__ == "__main__":
    main()
