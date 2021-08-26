from field.cell import *
from field.wall import *

info = {
    Cell: {'ru': 'суша'},
    CellRiver: {'ru': 'река'},
    CellRiverMouth: {'ru': 'устье'},
    CellExit: {'ru': 'выход'},
    CellClinic: {'ru': 'Медпункт'},
    CellArmory: {'ru': 'Арсенал'},
    CellArmoryWeapon: {'ru': 'Склад оружия'},
    CellArmoryExplosive: {'ru': 'Склад взрывчатки'},

    WallEmpty: {'ru': 'пустая стена', 'en': ''},
    WallConcrete: {'ru': 'стена'},
    WallOuter: {'ru': 'внешняя стена'},
    WallRubber: {'ru': 'резиновая стена'},
    WallExit: {'ru': 'выход'},
    WallEntrance: {'ru': 'вход'},
}


class Host:
    def __init__(self, rules: dict):
        self.rules = rules

    def give_info(self, turn_info: dict):
        res = []
        print(turn_info)
        if self.rules:
            pass
        # return f"{turn_info['player']}"
        try:
            inf = turn_info['response']['info']
            for elem in inf:
                res.append(info[elem]['ru'])
            print(', '.join(res))
            # return f"cell = {[turn_info['response']['info'][i] for i in range(turn_info['response']['info'])]}"

        except Exception:
            print("!!! не ожидаемый response")
