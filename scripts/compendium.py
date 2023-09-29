import locale
from sys import platform
from tkinter import StringVar

from PIL import Image
from customtkinter import CTkToplevel, CTkEntry, CTkScrollableFrame, CTkButton, CTkCheckBox, CTkLabel, CTkFrame, \
    CTkImage
from CTkToolTip import CTkToolTip

from fusion_helper import FusionHelper
from scripts.data_path import resource_path


class Compendium(CTkToplevel):
    def __init__(self, compendium, fusion_helper: FusionHelper):
        super().__init__()
        self.title("Compendium")
        self.compendium = compendium
        self.fusion_helper = fusion_helper
        self.iconbitmap(resource_path("Assets/compendium_icon.ico"))
        if platform.startswith("win"):
            self.after(200, lambda: self.iconbitmap(resource_path("Assets/compendium_icon.ico")))

        # GUI
        sv = StringVar()
        sv.trace("w", lambda name, index, mode, sv=sv: self._callback(sv))
        self.search_field = CTkEntry(self, placeholder_text="search...", textvariable=sv)
        self.search_field.pack(padx=10, pady=10)
        self.compendium_container = CTkScrollableFrame(self, width=200, height=200)
        self.compendium_container.pack(padx=10, pady=10)
        self.apply_button = CTkButton(self, text="Apply", command=lambda: self._apply())
        self.apply_button.pack(padx=10, pady=10)
        self.persona_checkboxes = {}
        self.labels = []
        self._init_checkboxes(compendium)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _init_checkboxes(self, compendium):
        img = CTkImage(dark_image=Image.open(resource_path('Assets/info1.png')), size=(15, 15))
        for p in compendium.values():
            combo = CTkFrame(self.compendium_container)
            combo.pack(anchor='w')
            box = CTkCheckBox(combo, text=f'{p.name}', width=1)
            info = CTkLabel(combo, text='', image=img)

            self.labels.append(info)

            cost = locale.currency(p.cost, grouping=True) if p.cost > 0 else 'N/A'
            CTkToolTip(info, message=f'lvl: {p.current_level} | cost: {cost}')
            self.persona_checkboxes[p.name] = combo
            if p.owned:
                box.select()
            box.pack(pady=5, anchor='w', side='left')
            info.pack(pady=5, padx=5, anchor='e', side='right')

    def update_checkboxes(self):
        for name, box in self.persona_checkboxes.items():
            if self.compendium[name].owned:
                box.winfo_children()[0].select()
            else:
                box.winfo_children()[0].deselect()

    def _callback(self, sv: StringVar):
        print(sv.get())
        for box in self.persona_checkboxes.keys():
            self.persona_checkboxes[box].pack_forget()
        for box in self.persona_checkboxes.keys():
            if box.lower().startswith(sv.get().lower()):
                self.persona_checkboxes[box].pack(anchor='w')

    def _apply(self):
        for name, box in self.persona_checkboxes.items():
            self.compendium[name].set_owned(box.winfo_children()[0].get() == 1)
        self.fusion_helper.update_my_personas()
        self.hide()
        self.fusion_helper.save_compendium()

    def show(self):
        self.attributes('-alpha', 0)
        self.deiconify()
        self.update()
        for i in range(0, 101, 10):
            if not self.winfo_exists():
                break
            self.attributes("-alpha", i/100)
            self.update()
            # time.sleep(1/100)
        for i in range(5, len(self.labels)):
            self.labels[i].pack(pady=5, padx=5, anchor='e', side='right')
        # self.update()
        # self.attributes('-alpha', 1)

    def hide(self):
        self.grab_release()
        self.withdraw()
        for i in range(20, len(self.labels)):
            self.labels[i].pack_forget()

    def _on_closing(self):
        self.hide()
