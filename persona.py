import pandas as pd
import Data5Royal
import math


class Persona:
    def __init__(self, arcana: str, level: int, name: str, special: bool, dlc: bool, treasure: bool):
        self.arcana = arcana
        self.level = level
        self.current_level = level
        self.name = name
        self.owned = False
        self.special = special
        self.dlc = dlc
        self.treasure_demon = treasure
        self.can_be_fused = False
        self.fusion_material_list = []

    def __str__(self):
        # return f'{self.arcana} {self.level} {self.name}'
        return f'{self.name};{self.current_level}'

    def __repr__(self):
        # return f'{self.arcana} {self.level} {self.name}'
        return f'{self.name};{self.current_level}'


class PersonaAlt:
    def __init__(self, name: str, owned: bool, can_be_fused: bool):
        self.name = name
        self.owned = owned
        self.can_be_fused = can_be_fused
        self.fusion_material_list = []
        self.prev = []

    def __str__(self):
        if self.owned:
            return f'{self.name}'
        else:
            return f'[{self.name} can be fused with {self.fusion_material_list}]'
        # return f'{self.name} {self.owned} {self.can_be_fused}'

    def __repr__(self):
        if self.owned:
            return f'{self.name}'
        else:
            return f'[{self.name} can be fused with {self.fusion_material_list}]'
        # return f'{self.name} {self.owned} {self.can_be_fused}'


class FileReader:
    def __init__(self):
        self.persona_list = self.excel_to_persona('G:\Documents\Persona5R fusion helper\compendium.xlsx')
        self.persona_map = self.create_persona_map()
        self.reverse_fusion_map = self.create_reverse_table()
        self.add_special_fusions()

    def excel_to_persona(self, path):
        data = pd.read_excel(path)
        df = pd.DataFrame(data)
        df = df.reset_index()
        persona_list = []
        for index, row in df.iterrows():
            # print(row['Arcana'], row['Level'], row['Name'])
            persona = Persona(row['Arcana'], int(row['Level']), row['Name'], str(row['Special']) == "True",
                              str(row['DLC']) == "True", str(row['Treasure']) == "True")
            persona_list.append(persona)
        print(persona_list)
        return persona_list

    def create_reverse_table(self):
        reverse_fusion_map = {}

        for first_persona_index in range(len(self.persona_list)):
            for second_persona_index in range(first_persona_index + 1, len(self.persona_list)):
                p1 = self.persona_list[first_persona_index]
                p2 = self.persona_list[second_persona_index]

                if (p1.treasure_demon and not p2.treasure_demon) or (p2.treasure_demon and not p1.treasure_demon):
                    continue

                result_arcana = ""
                for combo in Data5Royal.arcana2CombosRoyal:
                    if combo['source'] == [p1.arcana, p2.arcana] or combo['source'] == [p2.arcana, p1.arcana]:
                        result_arcana = combo['result']
                        break
                result_level = (p1.level + p2.level) / 2
                result_level += 1 if result_level.is_integer() else 0.5

                if result_arcana != "":
                    persona = self.forward_fusion(p1.name, p2.name)
                    if persona is not None:
                        if persona.name in reverse_fusion_map.keys():
                            reverse_fusion_map.get(persona.name).append((p1.name, p2.name))
                        else:
                            reverse_fusion_map[persona.name] = [(p1.name, p2.name)]

        # print(reverse_fusion_map)
        # print(len(reverse_fusion_map))
        return reverse_fusion_map

    def forward_fusion(self, persona1, persona2):
        p1 = self.persona_map[persona1]
        p2 = self.persona_map[persona2]

        if (p1.treasure_demon and not p2.treasure_demon) or (p2.treasure_demon and not p1.treasure_demon):
            self.treasure_demon_fusion(persona1, persona2)

        result_arcana = ""
        for combo in Data5Royal.arcana2CombosRoyal:
            if combo['source'] == [p1.arcana, p2.arcana] or combo['source'] == [p2.arcana, p1.arcana]:
                result_arcana = combo['result']
                break
        result_level = math.floor((p1.level + p2.level) / 2) + 1
        if result_arcana != "":
            result_arcana_list = [x for x in self.persona_list if x.arcana == result_arcana]
            if p1.arcana != p2.arcana:
                # different arcana fusion
                for persona in result_arcana_list:
                    if persona.special or persona.treasure_demon:
                        continue
                    if persona.level >= result_level:
                        return persona
            else:
                # same arcana fusion
                for persona in reversed(result_arcana_list):
                    if persona.special or persona.treasure_demon or persona == p1 or persona == p2:
                        continue
                    if persona.level <= result_level:
                        return persona

    def treasure_demon_fusion(self, persona1, persona2):
        p1 = self.persona_map[persona1]
        p2 = self.persona_map[persona2]
        treasure = p1 if p1.treasure_demon else p2
        non_treasure = p1 if not p1.treasure_demon else p2
        arcana_list = [x for x in self.persona_list if x.arcana == non_treasure.arcana and not x.special
                       and not x.treasure_demon]

        index = Data5Royal.rarePersonaeRoyal.index(treasure.name)
        rank = Data5Royal.rareCombosRoyal[non_treasure.arcana][index]

        # find "index" of non treasure persona at its current level
        counter = 0
        for item in arcana_list:
            if item.level > non_treasure.current_level:
                break
            counter += 1
        if rank > 0:
            counter -= 1

        if len(arcana_list) > counter + rank >= 0:
            return arcana_list[counter + rank]

    def create_persona_map(self):
        persona_map = {}
        for persona in self.persona_list:
            persona_map[persona.name] = persona
        return persona_map

    def add_special_fusions(self):
        data = pd.read_excel('G:\Documents\Persona5R fusion helper\special_compendium.xlsx')
        df = pd.DataFrame(data)
        df = df.reset_index()
        for index, row in df.iterrows():
            p = self.persona_map[row['Name']]
            l = []
            for i in range(1, 7):
                mat = row[f'Material{i}']
                if not pd.isna(mat):
                    l.append(mat)
            p.fusion_material_list.append(l)
            # self.reverse_fusion_map[p.name] = [tuple(l)]

    # create_reverse_table()
