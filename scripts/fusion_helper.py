import os
from time import time, sleep

import matplotlib.pyplot as plt
import pygetwindow as gw
from CTkMessagebox import CTkMessagebox
from pynput.keyboard import Controller

from data import Data5Royal
import persona
from scripts.compendium_scanner import CompendiumScanner
from scripts.data_path import resource_path
from scripts.graph_generator import GraphGenerator
from persona_info import PersonaInfo


class FusionHelper:
    def __init__(self, center_popup, plotframe, set_current_node):
        self.center_popup = center_popup
        self.plotframe = plotframe
        self.set_current_node = set_current_node

        self.file_reader = persona.FileReader()
        self.persona_map = self.file_reader.persona_map
        self._reverse_map = self.file_reader.reverse_fusion_map
        self._compendium_scanner = CompendiumScanner(self.persona_map, center_popup)
        self._counter = 0
        all_arcana = [x for x in Data5Royal.rareCombosRoyal.keys() if x != "World"]
        self.slink_map = {arcana: False for arcana in all_arcana}
        self.use_dlc = True

        self._keyboard = Controller()
        self._load_compendium()
        self._scan_in_progress = False
        self._current_node = None
        self._node_to_label: dict[str, plt.text] = {}
        self._current_graph_personas = []
        self._pos = None
        self._current_indices = {}
        self._current_result = ""
        self._dropdown = None
        self._graph_generator = GraphGenerator(self.plotframe, self.persona_map)

    # def scan_compendium(self):
    #     thread = Thread(target=self._scan_compendium)
    #     thread.start()
    #     return thread

    def scan_compendium(self):
        self._scan_in_progress = True
        windows = gw.getWindowsWithTitle("Persona 5 Royal")
        if len(windows) > 1:
            win = windows[1]
        else:
            self.center_popup(CTkMessagebox(title="Error", icon="cancel", message="Game could not be found.\n"
                                                                                  "Please start the game and try again"))
            return
        win.activate()
        sleep(0.5)

        if self._compendium_scanner.check_conditions():
            # popup = CTkMessagebox(title="Info", message="Scan in progress.\nPlease wait until scan is complete.\n"
            #                                             "Press ESC to abort")
            # self.center_popup(popup)
            personas = self._compendium_scanner.scan_compendium()
            if personas is not None:
                # save persona list in a compendium.txt
                self.can_fuse_all()
                self.save_compendium()
                self._scan_in_progress = False
            # popup.destroy()

    def update_my_personas(self):
        # update which personas can be fused after change
        self.can_fuse_all()

    def can_fuse_all(self):
        self._can_fuse_iterative()
        for p in self.persona_map.values():
            if p.special and not p.owned:
                fusible = True
                # print(p)
                for mat in p.fusion_material_list[0]:
                    mat_persona = self.persona_map[mat]
                    if not (mat_persona.owned or mat_persona.can_be_fused):
                        fusible = False
                        break
                if fusible:
                    p.can_be_fused = True

    # flooding the entire compendium to find every persona that is somehow fusible
    def _can_fuse_iterative(self):
        treasure_demons = [x for x in self.persona_map.values() if x.owned and x.treasure_demon]
        while True:
            stop = True
            for p in self.persona_map.keys():
                # skip if no recipe is available (special fusion)
                if p not in self._reverse_map.keys():
                    continue

                # skip persona if already owned
                if self.persona_map[p].owned:
                    continue

                # skip ultimate persona for which the slink isnt finished
                if self.persona_map[p].ultimate and not self.slink_map[self.persona_map[p].arcana]:
                    continue

                fusion_list = self._reverse_map[p]
                # check if a recipe is already available
                if not self.persona_map[p].can_be_fused:
                    for pair in fusion_list:
                        personas = [p for p in pair]
                        own_or_can_fuse_all = all(self.persona_map[p].owned or self.persona_map[p].can_be_fused for
                                                  p in personas)
                        # violate_dlc_use = not self.use_dlc and any(self.persona_map[p].dlc for p in personas)
                        # check if both materials for the recipe are owned or can be fused
                        if own_or_can_fuse_all:# and not violate_dlc_use:
                            # avoid duplicate recipe being added (shouldnt be possible)
                            # if [pair[0], pair[1]] not in self.persona_map[p].fusion_material_list:
                            if not self.persona_map[p].special:
                                self.persona_map[p].fusion_material_list.append([pair[0], pair[1]])
                            self.persona_map[p].can_be_fused = True
                            stop = False
            for treasure_demon in treasure_demons:
                for p in self.persona_map.values():
                    if (p.owned or p.can_be_fused) and not p.treasure_demon:
                        result = self.file_reader.treasure_demon_fusion(treasure_demon.name, p.name)

                        if result is not None:
                            if result.ultimate and not self.slink_map[result.arcana]:
                                continue
                            if not result.can_be_fused and not result.owned:
                                self.persona_map[result.name].fusion_material_list.append([treasure_demon.name, p.name])
                                self.persona_map[result.name].can_be_fused = True
                                stop = False
            # stop if after a full cycle no new recipes have been added
            if stop:
                break

    def can_fuse(self, target_persona, indices: dict = None, new_fusion: bool = False):
        for key in self.persona_map.keys():
            if key.lower() == target_persona.lower():
                target_persona = key
                break

        if not new_fusion:
            self._graph_generator.current_node = None

        if indices is None:
            indices = {}
        self._current_indices = indices
        start = time()
        if target_persona in self.persona_map.keys():
            p = self.persona_map[target_persona]
            if p.owned:
                print(p.name)
                print("This Persona is already owned")
                self.center_popup(CTkMessagebox(title="Info", message="This Persona is already owned"))
            elif p.ultimate and not self.slink_map[p.arcana]:
                self.center_popup(
                    CTkMessagebox(title="Info", message=f"This Persona requires the {p.arcana} Arcana "
                                                        "maxed out in order to be fused."))
            elif not p.can_be_fused:
                self.center_popup(CTkMessagebox(title="Info", message="This Persona cannot be fused with "
                                                                      "the current Compendium."))
            else:
                # resolve_persona_fusion(target_persona)
                if target_persona in self._reverse_map:
                    print(self._reverse_map[target_persona])

                if p.name in indices.keys():
                    index = indices[p.name]
                else:
                    index = 0
                self._current_result = target_persona
                # check that the material list is not empty
                if p.fusion_material_list:
                    self._current_graph_personas = self._resolve_list(p.fusion_material_list[index].copy(), indices)
                    self._generate_graph(self._current_graph_personas, p.name)
                return len(p.fusion_material_list)
        else:
            self.center_popup(
                CTkMessagebox(title="Error", message="This Persona does not exist. Please check again.", icon="cancel"))
        # print(total_material_list)
        print(f"Duration: {time() - start}")
        return 0

    # turn given list into one that only contains owned personas
    def _resolve_list(self, persona_list, indices):
        copy_list = persona_list.copy()
        for c in copy_list:
            if isinstance(c, list):
                continue
            if not self.persona_map[c].owned:
                if c in indices.keys():
                    index = indices[c]
                else:
                    index = 0
                # replace not owned persona by its first fusion_material_list entry
                persona_list.remove(c)
                persona_list.append(self.persona_map[c].fusion_material_list[index].copy())
                l = persona_list[-1]
                self._resolve_list(l, indices)
        return persona_list

    def _generate_graph(self, personas, target_persona):
        canvas, self._pos = self._graph_generator.list_to_graph(personas, target_persona)
        canvas.mpl_connect('button_press_event', self._click_node)

    def _click_node(self, event):
        print(event)
        # Get the clicked node data from the event object
        if event.xdata is not None and event.ydata is not None:
            x, y = event.xdata, event.ydata
            node = None
            for n, (pos_x, pos_y) in self._pos.items():
                if abs(pos_x - x) < 10 and abs(pos_y - y) < 10:
                    node = n
                    break

            if node is not None:
                print(f"Clicked node: {node}")
                # left click
                if event.button == 1:
                    # open persona information pop-up in the middle of the parent window
                    self.center_popup(PersonaInfo(self.persona_map[node]))
                # right click
                if event.button == 3:
                    self._graph_generator.current_node = node
                    self.set_current_node(node)
                    self.can_fuse(self._current_result, self._current_indices, True)
                    print(f"INDEX: {self._current_indices[node]}")

    def get_ultimate_persona(self, arcane):
        sub_list = reversed([x for x in self.persona_map.values() if x.arcana == arcane])
        for p in sub_list:
            if p.ultimate:
                return p

    def calculate_fusion_cost(self):
        total_cost = 0
        current_graph = self._graph_generator.current_graph
        if current_graph is None:
            return
        leaf_nodes = self.get_leaf_nodes()
        for leaf in leaf_nodes:
            total_cost += current_graph.out_degree(leaf) * self.persona_map[leaf].cost
        return total_cost

    def get_leaf_nodes(self):
        current_graph = self._graph_generator.current_graph
        return [node for node in current_graph.nodes() if current_graph.in_degree(node) == 0]

    def calculate_cheapest_fusion(self, target_persona):
        p = self.persona_map[target_persona]
        if p.owned:
            return p.cost, {target_persona: 0}
        mats = p.fusion_material_list
        mats_cost = []
        index_map = []
        for combo in mats:
            cost = 0
            maps = {}
            for p in combo:
                cost += self.calculate_cheapest_fusion(p)[0]
                maps = maps | self.calculate_cheapest_fusion(p)[1]
            mats_cost.append(cost)
            index_map.append(maps)
        min_cost = min(mats_cost)
        index = mats_cost.index(min_cost)
        return min_cost, {target_persona: index} | index_map[index]

    def save_compendium(self):
        with open(resource_path('data/compendium.txt'), 'w') as f:
            my_personas = [p for p in self.persona_map.values() if p.owned]
            for p in my_personas:
                f.write(str(p) + "\n")

        with open(resource_path('data/slink.txt'), 'w') as f:
            for name, value in self.slink_map.items():
                f.write(f"{name}:{value}\n")

        ratio = len([x for x in self.persona_map.values() if x.owned or x.can_be_fused]) / len(self.persona_map.keys())
        ratio = round(ratio * 100, 2)
        # self.center_popup(CTkMessagebox(title="Info", message=f"With the current Compendium a {ratio}% "
        #                                                       f"completion rate can be achieved."))
        self._dropdown.configure(values=self.persona_map.values())

    def _load_compendium(self):
        # read compendium.txt if available and write its content in my_personas
        if os.path.isfile(resource_path('data/compendium.txt')):
            with open(resource_path('data/compendium.txt'), 'r') as f:
                for line in f:
                    info = line.replace("\n", "").split(";")
                    # self.my_personas.append(persona.Persona("", int(info[1]), info[0], False, False, False, False))
                    name = info[0]
                    current_level = info[1]
                    cost = info[2]
                    p = self.persona_map[name]
                    p.owned = True
                    p.current_level = int(current_level)
                    p.cost = int(cost)
        if os.path.isfile(resource_path('data/slink.txt')):
            with open(resource_path('data/slink.txt'), 'r') as f:
                for line in f:
                    item = line.replace("\n", "").split(":")
                    self.slink_map[item[0]] = item[1] == 'True'

    def get_current_result(self):
        return self._current_result

    def get_current_graph(self):
        return self._graph_generator.current_graph

    def set_dropdown(self, dropdown):
        self._dropdown = dropdown
