from sys import platform

from CTkToolTip import CTkToolTip
from PIL import Image
from customtkinter import *

from data import Data5Royal
from scripts.fusion_helper import FusionHelper
from data_path import resource_path


class SLink(CTkToplevel):
    def __init__(self, fusion_helper: FusionHelper):
        super().__init__()
        self.title("Social Links")
        self.fusion_helper = fusion_helper
        self.iconbitmap(resource_path("Assets/compendium_icon.ico"))
        if platform.startswith("win"):
            self.after(200, lambda: self.iconbitmap(resource_path("Assets/compendium_icon.ico")))

        self.slink_checkboxes = {}
        self.slink_container = CTkScrollableFrame(self, width=200, height=200)
        self.slink_container.pack(padx=10, pady=10)
        # all arcana but world have a slink tied to it
        self.all_arcana = [x for x in Data5Royal.rareCombosRoyal.keys() if x != "World"]
        self._init_checkboxes(fusion_helper)
        self.apply_button = CTkButton(self, text="Apply", command=lambda: self._apply())
        self.apply_button.pack(padx=10, pady=10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _init_checkboxes(self, fusion_helper):
        img = CTkImage(dark_image=Image.open(resource_path('Assets/info1.png')), size=(15, 15))
        for arcana in self.all_arcana:
            combo = CTkFrame(self.slink_container)
            combo.pack(anchor='w')
            box = CTkCheckBox(combo, text=f'{arcana}', width=1)
            info = CTkLabel(combo, text='', image=img)
            CTkToolTip(info, message=f'Persona: {fusion_helper.get_ultimate_persona(arcana).name}')
            self.slink_checkboxes[arcana] = box
            if fusion_helper.slink_map[arcana]:
                box.select()
            box.pack(pady=5, anchor='w', side='left')
            info.pack(pady=5, padx=5, anchor='e', side='right')

    def _apply(self):
        for name, box in self.slink_checkboxes.items():
            max_link = box.get() == 1
            self.fusion_helper.slink_map[name] = max_link
            if not max_link:
                ultimate = self.fusion_helper.get_ultimate_persona(name)
                ultimate.can_be_fused = False
        self.fusion_helper.update_my_personas()
        self.destroy()
        self.fusion_helper.save_compendium()
        print(self.fusion_helper.slink_map)

    def show(self):
        self.attributes('-alpha', 0)
        self.deiconify()
        for i in range(0, 101, 10):
            if not self.winfo_exists():
                break
            self.attributes("-alpha", i/100)
            self.update()
            # time.sleep(1/100)

    def hide(self):
        self.grab_release()
        self.withdraw()

    def _on_closing(self):
        self.hide()
