import os
import time
import tkinter
from time import time
from time import sleep

import customtkinter
import matplotlib.pyplot as plt
import mss
import networkx as nx
import pygetwindow as gw
import tesserocr
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from networkx.drawing.nx_agraph import graphviz_layout
from pynput.keyboard import Controller

import persona
from CTkScrollableDropdown import *
from CTkMessagebox import CTkMessagebox
from difflib import SequenceMatcher
import PIL.ImageOps
from threading import Thread
from keyboard import add_hotkey


class PersonaInfo(customtkinter.CTkToplevel):
    def __init__(self, target_persona: persona.Persona):
        super().__init__()
        self.width = 250
        self.height = 150
        self.spawn_x = int((self.winfo_screenwidth() - self.width) / 2)
        self.spawn_y = int((self.winfo_screenheight() - self.height) / 2)
        self.geometry(f"{self.width}x{self.height}+{self.spawn_x}+{self.spawn_y}")
        self.name = customtkinter.CTkLabel(self, text=f'name: {target_persona.name}')
        self.name.pack()
        self.level = customtkinter.CTkLabel(self, text=f'Level: {target_persona.level}')
        self.level.pack()
        self.arcana = customtkinter.CTkLabel(self, text=f'arcana: {target_persona.arcana}')
        self.arcana.pack()


class FusionHelper:
    def __init__(self):
        self.my_personas = []
        self.file_reader = persona.FileReader()
        self.persona_map = self.file_reader.persona_map
        self._reverse_map = self.file_reader.reverse_fusion_map
        self._canvas = ""
        self._pos = ""
        self._counter = 0
        self._sct = mss.mss()
        self._api = tesserocr.PyTessBaseAPI(lang="eng")
        self._api.SetPageSegMode(7)
        self._keyboard = Controller()
        self._load_compendium()
        self._set_owned()
        self._scan_in_progress = False
        add_hotkey("esc", lambda: self._scan_in_progress)

    def _abort_scan(self):
        self._scan_in_progress = False

    def scan_compendium(self):
        Thread(target=self._scan_compendium).start()

    def _scan_compendium(self):

        self._scan_in_progress = True

        personas = []
        windows = gw.getWindowsWithTitle("Persona 5 Royal")
        if len(windows) > 1:
            win = windows[1]
        else:
            center_popup(CTkMessagebox(title="Error", icon="cancel", message="Game could not be found.\n"
                                                                             "Please start the game and try again"))
            return
        win.activate()

        popup = CTkMessagebox(title="Info", message="Scan in progress.\nPlease wait until scan is complete.\n"
                                                    "Press ESC to abort")
        center_popup(popup)

        x1 = 410
        y1 = 280  # 250
        x2 = 730
        y2 = 335
        height = 75

        check_box = self.take_screenshot({"top": 710, "left": 1000, "width": 1, "height": 1})
        started_scroll = False
        i = 0

        while self._contains_red(check_box) or not started_scroll:
            # abort scan if _scan_in_progress = False
            if not self._scan_in_progress:
                return

            # takes a screenshot to the right of the second bottom most persona to check it for red color
            # it will only not be red for the first 6 entries or once the end has been reached
            check_box = self.take_screenshot({"top": 687, "left": 1080, "width": 1, "height": 1})
            # persona name label screenshot
            im = self.take_screenshot({"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1})
            im = im.convert('L')
            im = PIL.ImageOps.invert(im)

            # move down 6 entries before the list starts to scroll
            if not self._contains_red(check_box):
                y1 += height
                y2 += height
                x1 += 16
                x2 += 16
                i += 1
            else:
                started_scroll = True

            # use ocr to access the text
            self._api.SetImage(im)
            text = self._api.GetUTF8Text()
            if text == "":
                im.show()
                break
            print(f'before: {text}')
            if text not in self.persona_map.keys():
                text = self._find_closest_match(text)

            # add persona name to the list of personas
            personas.append(text)
            # im.save('screenshots/' + str(i) + '.png')
            # go down by one
            self._keyboard.press('s')
            sleep(0.1)
            self._keyboard.release('s')
            print(f'after: {text}')
        self.my_personas = personas
        # save persona list in a compendium.txt
        self.save_compendium()
        self._set_owned()
        self.can_fuse_all()
        self._scan_in_progress = False
        popup.destroy()

    def _find_closest_match(self, text):
        max_match_percentage = 0
        result = ""
        for p in self.persona_map.keys():
            current_match_percentage = SequenceMatcher(None, text, p).ratio()
            if current_match_percentage > max_match_percentage:
                max_match_percentage = current_match_percentage
                result = p
        return result

    def _set_owned(self):
        # mark all owned persona
        dlc_owned = False
        for p in self.persona_map.keys():
            if p in self.my_personas:
                self.persona_map[p].owned = True
                dlc_owned = True
        # mark all dlc personas as owned if one is owned
        if dlc_owned:
            for value in self.persona_map.values():
                if value.dlc:
                    value.owned = True

    def update_my_personas(self):
        new = []
        for p in self.persona_map.values():
            if p.owned:
                new.append(p.name)
        self.my_personas = new
        # update which personas can be fused after change
        self.can_fuse_all()

    def take_screenshot(self, area):
        sct_img = self._sct.grab(area)
        # convert to PIL image
        img = Image.new("RGB", sct_img.size)
        pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
        img.putdata(list(pixels))
        return img

    def _contains_red(self, image):
        image = image.convert('RGBA')
        pixdata = image.load()
        # check all pixels for red color
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                if pixdata[x, y] == (255, 0, 0, 255):
                    return True
        return False

    def can_fuse_all(self):
        self._can_fuse_iterative()
        for p in self.persona_map.values():
            if p.special and not p.owned:
                fusible = True
                print(p)
                for mat in p.fusion_material_list[0]:
                    mat_persona = self.persona_map[mat]
                    if not (mat_persona.owned or mat_persona.can_be_fused):
                        fusible = False
                        break
                if fusible:
                    p.can_be_fused = True

    # flooding the entire compendium to find every persona that is somehow fusible
    def _can_fuse_iterative(self):
        while True:
            stop = True
            for p in self.persona_map.keys():
                # skip if no recipe is available (special fusion)
                if p not in self._reverse_map.keys():
                    continue

                # skip persona if already owned
                if self.persona_map[p].owned:
                    continue

                fusion_list = self._reverse_map[p]
                # check if a recipe is already available
                if not self.persona_map[p].can_be_fused:
                    for pair in fusion_list:
                        p1 = self.persona_map[pair[0]]
                        p2 = self.persona_map[pair[1]]
                        # check if both materials for the recipe are owned or can be fused
                        if (p1.owned or p1.can_be_fused) and (p2.owned or p2.can_be_fused):
                            # avoid duplicate recipe being added (shouldnt be possible)
                            if [pair[0], pair[1]] not in self.persona_map[p].fusion_material_list:
                                self.persona_map[p].fusion_material_list.append([pair[0], pair[1]])
                                self.persona_map[p].can_be_fused = True
                                stop = False
            # stop if after a full cycle no new recipes have been added
            if stop:
                break

    def can_fuse(self, target_persona):
        start = time()
        if target_persona in self.persona_map.keys():
            p = self.persona_map[target_persona]
            if p.owned:
                print(p.name)
                print("This Persona is already owned")
                center_popup(CTkMessagebox(title="Info", message="This Persona is already owned"))
            else:
                # resolve_persona_fusion(target_persona)
                print(self._reverse_map[target_persona])
                # check that the material list is not empty
                if p.fusion_material_list:
                    self._resolve_list(p.fusion_material_list[0])
                    self._list_to_graph(p.fusion_material_list[0], p.name)
                print(p.fusion_material_list[0])
                print(len(p.fusion_material_list))
                print(self._reverse_map[target_persona])
                print(len(self._reverse_map[target_persona]))
        else:
            center_popup(
                CTkMessagebox(title="Error", message="This Persona does not exist. Please check again.", icon="cancel"))
        # print(total_material_list)
        print(f"Duration: {time() - start}")

    def _resolve_list(self, persona_list):
        copy_list = persona_list.copy()
        for c in copy_list:
            if isinstance(c, list):
                continue
            if not self.persona_map[c].owned:
                # replace not owned persona by its first fusion_material_list entry
                persona_list.remove(c)
                persona_list.append(self.persona_map[c].fusion_material_list[0])
                l = persona_list[-1]
                self._resolve_list(l)

    def _list_to_graph(self, persona_list: list, target_persona):
        list_copy = persona_list.copy()
        # break down all nested lists to end up with one list which contains all required personas
        while True:
            for p in list_copy:
                if isinstance(p, list):
                    list_copy.remove(p)
                    list_copy += p
            if not any(isinstance(el, list) for el in list_copy):
                break

        # create digraph with all required personas + the result as nodes
        G = nx.DiGraph()
        G.add_node(target_persona)
        G.add_nodes_from(list_copy)
        self._graph_recursive(G, target_persona, persona_list)
        H = self._relabel_fusion_nodes(G)

        # apply tree layout for the graph
        self._pos = graphviz_layout(H, prog='dot')
        print("############")
        print(self._pos)
        nx.draw(H, with_labels=True, pos=self._pos)

        for node, (x, y) in self._pos.items():
            plt.text(x, y, str(node), ha='center', va='center',
                     bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.2'))

        # Clear the previous canvas if it exists
        if self._canvas != "":
            self._canvas.get_tk_widget().destroy()
        # Add the Matplotlib plot to a Tkinter canvas
        self._canvas = FigureCanvasTkAgg(plt.gcf(), master=plotframe)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)

        self._canvas.mpl_connect('button_press_event', self._click_node)

        # plt.draw()
        plt.show()

    def _click_node(self, event):
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
                # open persona information pop-up in the middle of the parent window
                center_popup(PersonaInfo(self.persona_map[node]))

    def _graph_recursive(self, g: nx.Graph, root, persona_list: list):
        for p in persona_list:
            if not isinstance(p, list):
                g.add_edge(p, root)
            else:
                # temporary fusion nodes as a placeholder. proper names can only be applied afterwards
                name = f'FUSION{self._counter}'
                self._counter += 1
                g.add_node(name)
                g.add_edge(name, root)
                self._graph_recursive(g, name, p)

    def _relabel_fusion_nodes(self, g: nx.Graph):
        h = g.copy()
        while True:
            nodes = h.copy().nodes()
            for node in nodes:
                # find placeholder fusion nodes
                if str(node).startswith('FUSION'):
                    in_edges = list(h.in_edges(node, data=True))
                    p1 = in_edges[0][0]
                    p2 = in_edges[1][0]
                    name = None
                    # check that both materials (ingoing edges) are named nodes (not fusion or resolved ones)
                    if p1 in self.persona_map.keys() and p2 in self.persona_map.keys():
                        name = self.file_reader.forward_fusion(p1, p2).name
                    # relabel node if possible
                    if name is not None:
                        mapping = {node: name}
                        h = nx.relabel_nodes(h, mapping, copy=False)
            done = True
            for node in h.nodes():
                if str(node).startswith('FUSION'):
                    done = False
            # stop once no nodes starting with FUSION are left
            if done:
                break
        return h

    def save_compendium(self):
        with open('compendium.txt', 'w') as f:
            for p in self.my_personas:
                f.write(p + "\n")

    def _load_compendium(self):
        # read compendium.txt if available and write its content in my_personas
        if os.path.isfile('compendium.txt'):
            with open('compendium.txt', 'r') as f:
                for line in f:
                    self.my_personas.append(line.replace("\n", ""))


class Compendium(customtkinter.CTkToplevel):
    def __init__(self, compendium, fusion_helper: FusionHelper):
        super().__init__()
        self.title("Compendium")
        self.compendium = compendium
        self.fusion_helper = fusion_helper
        self.compendium_container = customtkinter.CTkScrollableFrame(self, width=200, height=200)
        self.compendium_container.pack(padx=10, pady=10)
        self.apply_button = customtkinter.CTkButton(self, text="Apply", command=lambda: self._apply())
        self.apply_button.pack(padx=10, pady=10)
        self.persona_checkboxes = {}
        for p in compendium.values():
            box = customtkinter.CTkCheckBox(self.compendium_container, text=p.name)
            self.persona_checkboxes[p.name] = box
            if p.owned:
                box.select()
            box.pack(pady=5, anchor='w')

    def _apply(self):
        for name, box in self.persona_checkboxes.items():
            self.compendium[name].owned = box.get() == 1
        self.fusion_helper.update_my_personas()
        self.fusion_helper.save_compendium()
        self.destroy()


def center_popup(popup):
    x = app.winfo_x()
    y = app.winfo_y()
    w = app.winfo_width()
    h = app.winfo_height()
    popup.geometry("+%d+%d" % (x + w / 2 - popup.winfo_width() / 2, y + h / 2 - popup.winfo_height() / 2))


def fill_text(text):
    text_field.delete(0, 'end')
    text_field.insert(0, text)


def open_compendium():
    compendium_popup = Compendium(helper.persona_map, helper)
    center_popup(compendium_popup)
    compendium_popup.grab_set()


helper = FusionHelper()
helper.can_fuse_all()
# Compendium(helper.persona_map.values())
c = 0
for p in helper.persona_map.values():
    if p.owned:
        # print(p)
        c += 1
print(f'{c} personas owned')
# helper.take_screenshot({"top": 687, "left": 1080, "width": 1, "height": 1}).show()

# setup UI
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry("640x630")
app.title("Persona 5 Royal Fusion Helper")

app.resizable(False, False)

# option_menu = customtkinter.CTkOptionMenu(app, values=['Name', 'Level'], command=optionmenu_callback)
# option_menu.grid(row=0, column=0, padx=10, pady=10)
compendium_button = customtkinter.CTkButton(app, text="Compendium", command=lambda: open_compendium())
compendium_button.place(x=490, y=10)

text_field = customtkinter.CTkEntry(app, width=200)
text_field.grid(row=0, column=0, padx=10, pady=10)

dropdown = CTkScrollableDropdown(text_field, values=helper.persona_map.values(),
                                 command=lambda e: fill_text(e), autocomplete=True)  # Using autocomplete

scan = customtkinter.CTkButton(app, text="Scan Compendium", command=lambda: helper.scan_compendium())
scan.grid(row=1, column=0, padx=10, pady=10)

check = customtkinter.CTkButton(app, text="Check", command=lambda: helper.can_fuse(text_field.get()))
check.grid(row=2, column=0, padx=10, pady=10)

plotframe = customtkinter.CTkFrame(master=app, fg_color="white", width=640, height=480)
plotframe.grid(row=3, column=0)

app.mainloop()
