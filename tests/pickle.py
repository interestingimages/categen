from src import categen
from tests import utils
import colorama


def main():
    print(
        f"{colorama.Style.BRIGHT}interesting images"
        f"{colorama.Style.RESET_ALL} Tests / Pickling\n"
    )

    traces = utils.TracebackCollector()
    stsmgr = categen.cli.StatusManager()

    gencrt = stsmgr.register("Generator Creation")
    entgen = stsmgr.register("Entry Generation")
    pexpop = stsmgr.register("Pure Export")
    exptop = stsmgr.register("Export")
    imptop = stsmgr.register("Import")

    def op_gencrt():
        return categen.CatalogueEntry(eid=1, hid=300000)

    catentry = utils.attempt(gencrt, traces, op_gencrt)

    def op_entegen(catentry: categen.CatalogueEntry):
        catentry.entry()

    utils.attempt(entgen, traces, op_entegen, catentry)

    def op_pexpop(catentry: categen.CatalogueEntry):
        return {"text": f"Size: {len(catentry.pure_export())}"}

    utils.attempt(pexpop, traces, op_pexpop, catentry)

    def op_exptop(catentry: categen.CatalogueEntry):
        _op = catentry.export()
        return {"result": _op, "text": f"Size: {len(_op)}"}

    exp = utils.attempt(exptop, traces, op_exptop, catentry)

    def op_imptop(catentry: categen.CatalogueEntry, dilled: bytes):
        categen.catentry.instance(dilled)

    utils.attempt(imptop, traces, op_imptop, catentry, exp)

    traces.display()


if __name__ == "__main__":
    main()
