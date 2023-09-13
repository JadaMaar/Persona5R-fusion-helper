from customtkinter import CTkToplevel, CTkLabel, CTkImage

from scripts.data_path import resource_path
from PIL import Image


class LoadingScreen(CTkToplevel):
    def __init__(self):
        super().__init__()
        screen_width = self.winfo_screenwidth()  # Width of the screen
        screen_height = self.winfo_screenheight()  # Height of the screen
        x = (screen_width / 2) - (self.winfo_width() / 2)
        y = (screen_height / 2) - (self.winfo_height() / 2)

        self.geometry('+%d+%d' % (x, y))

        self.overrideredirect(True)
        img = CTkImage(dark_image=Image.open(resource_path("Assets/main_icon.png")), size=(100, 100))
        CTkLabel(self, text="Loading...", image=img, font=("Arial", 25, "bold")).pack(padx=10, pady=10)
