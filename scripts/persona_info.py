import locale
from sys import platform

from customtkinter import CTkToplevel, CTkLabel

from scripts.data_path import resource_path
from scripts.persona import Persona
import mouse


class PersonaInfo(CTkToplevel):
    def __init__(self, target_persona: Persona, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = 250
        self.height = 150
        self.title("Persona info")
        self.spawn_x = int((self.winfo_screenwidth() - self.width) / 2)
        self.spawn_y = int((self.winfo_screenheight() - self.height) / 2)
        self.geometry(f"{self.width}x{self.height}+{self.spawn_x}+{self.spawn_y}")
        self.iconbitmap(resource_path("Assets/compendium_icon.ico"))
        if platform.startswith("win"):
            self.after(200, lambda: self.iconbitmap(resource_path("Assets/compendium_icon.ico")))

        self.name = CTkLabel(self, text=f'Name: {target_persona.name}')
        self.name.pack()
        self.level = CTkLabel(self, text=f'Level: {target_persona.level}')
        self.level.pack()
        self.current_level = CTkLabel(self, text=f'Current Level: {target_persona.current_level}')
        self.current_level.pack()
        self.arcana = CTkLabel(self, text=f'Arcana: {target_persona.arcana}')
        self.arcana.pack()
        self.cost = CTkLabel(self, text=f'Cost: {locale.currency(target_persona.cost, grouping=True)}')
        self.cost.pack()
        if not target_persona.owned:
            self.cost.configure(text="Cost: N/A")
        self._add_hook()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _add_hook(self):
        self._hook = mouse.on_button(self._close, buttons=mouse.LEFT, types=mouse.DOWN)

    def _close(self):
        # self.update()
        position = mouse.get_position()
        try:
            x_min = self.winfo_x()
            x_max = x_min + self.winfo_width()
            y_min = self.winfo_y()
            y_max = y_min + self.winfo_height()
            if not x_min <= position[0] <= x_max or not y_min <= position[1] <= y_max:
                self._on_closing()
        except:
            print("window already closed")

    def _on_closing(self):
        mouse.unhook(self._hook)
        self.destroy()
