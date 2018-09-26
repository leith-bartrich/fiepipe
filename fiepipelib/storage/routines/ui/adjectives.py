import typing

from fiepipelib.storage.routines.localstorage import CommonAdjectivesDict


def get_common_adjectives_choices() -> typing.Dict[str:str]:
    adjectives = CommonAdjectivesDict()

    choices = typing.Dict[str:str]
    for catName in adjectives.keys():
        cat = adjectives[catName]
        for adj in cat.keys():
            desc = cat[adj]
            choice = catName + ":" + adj
            choices[choice] = adj
    return choices
