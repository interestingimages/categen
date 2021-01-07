from PrintingPress import Placements, operate
from hentai import Hentai, Format
from datetime import datetime
from copy import deepcopy
from pathlib import Path
from PIL import Image
from json import load

from . import data


class Utils:
    def sanitize(name) -> str:
        # TODO: This goes up to 2 nested [tags (long)], if the edge
        # case becomes existant - remake this.

        # Really old [] removal from InterestingSystems/Author,
        # since nhentai doesnt give pretty Japanese titles.

        stop = [")", "]"]
        watching = False
        detagged = name
        keyword = ""
        signal = ""

        for letter in name:
            if watching:
                keyword = keyword + letter

            if letter == "[" and signal == "":
                signal = "]"
                watching = True
                keyword = letter

            if letter == "(" and signal == "":
                signal = ")"
                watching = True
                keyword = letter

            if letter in stop and letter == signal:
                watching = False
                signal = ""
                detagged = detagged.replace(keyword, "")
                keyword = ""

        detagged = detagged.split(" ")
        pure = [elem for elem in detagged if elem != ""]

        return " ".join(pure)


class CatalogueEntry:
    markdown_map = {
        "WhatsApp": {
            "bold": ["*", "*"],
            "italic": ["_", "_"],
            "scode": ["```", "```"],
            "mcode": ["```", "```"],
        },
        "Telegram": {
            "bold": ["**", "**"],
            "italic": ["__", "__"],
            "scode": ["`", "`"],
            "mcode": ["```\n", "\n```"],
        },
    }

    def __init__(
        self, eid: int, hid: int, score: str, desc: str = "", markdown: str = "Telegram"
    ) -> None:
        self.config = data.Config()

        if not Path(self.config["Repository"]["path"]).is_dir():
            print(
                f'categen: {self.config["Repository"]["path"]} is non-existant, '
                "attempting to download Format."
            )
            try:
                data.Format.retrieve_online(
                    url=self.config["Repository"]["link"],
                    path=self.config["Repository"]["path"],
                )

            except Exception as e:
                print(
                    "categen: Error encountered while attempting to download format. "
                    f"({e}) categen will use the local Format shipped with the package."
                )
                data.Format.retrieve_local(format_dir=self.config["Repository"]["path"])

        self.format = data.Format(repo_config=self.config["Repository"])
        self.doujin = Hentai(hid)

        self.markdown = self.markdown_map[markdown]
        self.id = "0" * (3 - len(str(eid))) + str(eid)
        self.score = str(score)
        self.description = str(desc)

        assert self.config["Settings"]["divide"] in ["both", "left", "right"], (
            f'config:General:divide - "{self.config["Settings"]["divide"]}"'
            "is not a valid divide value!"
        )
        self.divide = self.config["Settings"]["divide"]

        placements_path = Path(self.config["Repository"]["path"]).joinpath(
            "placements.json"
        )
        assert placements_path.exists(), f"{placements_path}: Non-existant"
        with open(placements_path, "r", encoding="utf-8") as pf:
            self.placements = load(pf)

        entry_path = Path(self.config["Repository"]["path"]).joinpath("entry.txt")
        assert entry_path.exists(), f"{entry_path}: Non-existant"
        with open(entry_path, "r", encoding="utf-8") as ef:
            self.entry_text = ef.read()

        tagsofinterest_path = Path(self.config["Repository"]["path"]).joinpath(
            "tagsofinterest.json"
        )
        assert tagsofinterest_path.exists(), f"{tagsofinterest_path}: Non-existant"
        with open(tagsofinterest_path, "r", encoding="utf-8") as toif:
            self.tagsofinterest = load(toif)

        formatting_map_path = Path(self.config["Repository"]["path"]).joinpath(
            "formatting.json"
        )
        if formatting_map_path.is_file():
            with open(formatting_map_path, "r", encoding="utf-8") as fmf:
                self.formatting_map = load(fmf)
        else:
            self.formatting_map = {}

        template_path = Path(self.config["Repository"]["path"]).joinpath(
            "thumbnail/template.png"
        )
        assert template_path.is_file(), f"{template_path}: Non-existant"
        self.template = Image.open(str(template_path))

        self._thumbnail = None
        self._entry = None

    def _divide(self, text: str) -> str:
        if "|" in text and self.divide != "both":
            if self.divide == "left":
                divided = text.split("|")[0].lstrip().rstrip()
            else:
                divided = text.split("|")[1].lstrip().rstrip()

            return divided

        else:
            return text

    def _strf(
        self, text: str, markdown_type: str = None, disable_override: bool = False
    ) -> str:
        def fword(keyword: str) -> str:
            override = self.formatting_map.get(keyword, None)
            return (
                f"{keyword}:-sep-:{override}"
                if not any([override is None, override == "", disable_override])
                else keyword
            )

        if markdown_type is None:
            markdown_type = self.config["Settings"]["markdown_type"]

        # Title Generation
        title_p_en = self._divide(self.doujin.title(Format.Pretty))
        title_p_jp = self._divide(Utils.sanitize(self.doujin.title(Format.Japanese)))

        markdown = self.markdown_map[markdown_type]

        bold = markdown["bold"][0]
        _bold = markdown["bold"][1]

        if title_p_en != "" and title_p_jp != "":
            title = f"{bold}{title_p_en}{_bold} - {bold}{title_p_jp}{_bold}"
        elif title_p_en != "" and title_p_jp == "":
            title = f"{bold}{title_p_en}{_bold}"
        elif title_p_en == "" and title_p_jp != "":
            title = f"{bold}{title_p_jp}{_bold}"
        else:
            title = "Unnamed"

        # Creator Text Generation
        artist_names = [tag.name for tag in self.doujin.artist]
        artist_names_str = ", ".join(artist_names)

        group_names = [tag.name for tag in self.doujin.group]
        group_names_str = ", ".join(group_names)

        if len(artist_names) > 0 and len(group_names) > 0:
            creator = f"({artist_names_str} / {group_names_str})"
        elif len(artist_names) > 0 and len(group_names) == 0:
            creator = f"({artist_names_str})"
        elif len(artist_names) == 0 and len(group_names) > 0:
            creator = f"({group_names_str})"
        else:
            creator = "(No Creator Info)"

        # Tags
        tags = [self._divide(tag.name) for tag in self.doujin.tag]
        tags_interest = [tag for tag in tags if tag in self.tagsofinterest]
        tags_remainder = [tag for tag in tags if tag not in tags_interest]

        format_map = {
            "bold": markdown["bold"][0],
            "-bold": markdown["bold"][1],
            "italic": markdown["italic"][0],
            "-italic": markdown["italic"][1],
            "scode": markdown["scode"][0],
            "-scode": markdown["scode"][1],
            "mcode": markdown["mcode"][0],
            "-mcode": markdown["mcode"][1],
            fword("entry_id"): self.id,
            fword("score"): self.score,
            fword("description"): self.description,
            fword("title.english"): self._divide(self.doujin.title()),
            fword("title.english.pretty"): title_p_en,
            fword("title.japanese:"): self._divide(self.doujin.title(Format.Japanese)),
            fword("title.japanese.pretty"): title_p_jp,
            fword("title"): title,
            fword("tags.interest"): ", ".join(tags_interest),
            fword("tags.remainder"): ", ".join(tags_remainder),
            fword("tags"): ", ".join(tags),
            fword("creator.scanlator"): self.doujin.scanlator,
            fword("creator.artist"): ", ".join([t.name for t in self.doujin.artist]),
            fword("creator.group"): ", ".join([t.name for t in self.doujin.group]),
            fword("creator"): creator,
            fword("doujin_id"): self.doujin.id,
            fword("pages"): self.doujin.num_pages,
            fword("favourites"): self.doujin.num_favorites,
            fword("link"): self.doujin.url,
            fword("time"): datetime.fromtimestamp(self.doujin.epos).strftime(
                "%B %d %Y, %H:%M:%S"
            ),
            fword("parody"): ", ".join([t.name for t in self.doujin.parody]),
            fword("characters"): ", ".join([t.name for t in self.doujin.character]),
            fword("slink"): f"nh.{self.doujin.id}",
            fword("submission"): "",
            fword("rating"): "",
        }

        for keyword, replacement in format_map.items():
            conditions = [
                "parody" in keyword and replacement == "original",
                "parody" in keyword and replacement == "",
                "favourites" in keyword and replacement == "0",
                "characters" in keyword and replacement == "",
                "creator.group" in keyword and replacement == "",
                "description" in keyword and replacement == "",
                "tags.remainder" in keyword and replacement == "",
            ]
            if not any(conditions):
                if ":-sep-:" in keyword:
                    # keyword:-sep-:\nkeyword\n
                    _keyword = keyword
                    keyword = keyword.split(":-sep-:")[0]
                    override = _keyword.lstrip(keyword + ':-sep-:')

                    replacement = self._strf(
                        text=override,
                        markdown_type=markdown_type,
                        disable_override=True,
                    )

                text = text.replace(f"<[{keyword}]>", str(replacement))

            else:
                if ":-sep-:" in keyword:
                    keyword = keyword.split(":-sep-:")[0]

                text = text.replace(f"<[{keyword}]>", "")

        return text

    def thumbnail(self, preview: Image.Image, suppress: bool = False) -> Image.Image:
        placements = deepcopy(self.placements)

        if ".meta" in placements:
            placements.pop(".meta")

        for area in [
            area for area in placements if placements[area].get("type") == "text"
        ]:
            placements[area]["text"] = self._strf(placements[area]["text"])

        for area in [area for area in placements if placements[area]["path"] != ""]:
            placements[area]["path"] = str(
                Path(self.config["Repository"]["path"]).joinpath(
                    placements[area]["path"]
                )
            )

        placements["viewfinder"]["path"] = preview

        self._thumbnail = operate(
            image=self.template,
            placements=Placements.parse(placements),
            suppress=suppress,
        )
        return self._thumbnail

    def entry(self, markdown_type: str = None) -> str:
        self._entry = self._strf(self.entry_text, markdown_type=markdown_type)
        return self._entry

    def export(self) -> bytes:
        from dill import dumps

        return dumps(self)
