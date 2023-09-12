import time

from PIL import Image
from customtkinter import *
from data_path import resource_path


class ImageButton(CTkLabel):
    def __init__(self, master, image_path,  command, disabled_image_path="", state="normal", size=None):
        self.pil_image = Image.open(resource_path(image_path))
        self.pil_disabled_image = self.pil_image if disabled_image_path == "" else Image.open(resource_path(disabled_image_path))
        self.size = self.pil_image.size if size is None else size
        self.image = CTkImage(light_image=self.pil_image, dark_image=self.pil_image, size=self.size)
        self.disabled_image = CTkImage(light_image=self.pil_disabled_image, dark_image=self.pil_disabled_image,
                                       size=self.size)
        super().__init__(master=master, image=self.image, text="")
        self._master = master
        self._command = command
        self._state = state
        self._cursor = "hand2"
        self.bind('<Enter>', self.enter)
        self.bind('<Leave>', self.leave)
        self.bind('<Button-1>', self._on_click)

    def enter(self, event):
        self._master.config(cursor=self._cursor)
        # self.configure(size=(self.size[0] * 1.1, self.size[1] * 1.1))
        # self._spin_animation()
        # print(event)

    def leave(self, event):
        self._master.config(cursor="arrow")
        # self.configure(size=(self.size[0] / 1.1, self.size[1] / 1.1))
        # print(event)

    def _on_click(self, event):
        if self._state == "normal":
            self._command()

    def _update_state(self):
        if self._state == "normal":
            self._cursor = "hand2"
            self.configure(image=self.image)
        elif self._state == "disabled":
            self._cursor = "arrow"
            self.configure(image=self.disabled_image)

    def rotate(self, degree):
        self.pil_image.rotate(degree, resample=Image.BICUBIC)
        self.pil_disabled_image.rotate(degree, resample=Image.BICUBIC)
        self.image.configure(dark_image=self.pil_image, light_image=self.pil_image)
        self.disabled_image.configure(dark_image=self.pil_disabled_image, light_image=self.pil_disabled_image)
        self._update_state()
        self.update()

    def _spin_animation(self):
        for i in range(361):
            self.rotate(i)
            self.update()
            time.sleep(1/360)

    def configure(self, require_redraw=False, **kwargs):
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._update_state()
        if "size" in kwargs:
            size = kwargs.pop("size")
            self.image.configure(size=size)
            self.disabled_image.configure(size=size)
        super().configure(require_redraw=False, **kwargs)
