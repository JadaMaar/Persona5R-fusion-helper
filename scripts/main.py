import locale
import os
import time
from threading import Thread

import customtkinter
from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
from PIL import Image

from CTkScrollableDropdown import CTkScrollableDropdown
from scripts.compendium import Compendium
from fusion_helper import FusionHelper
from scripts.data_path import resource_path
from scripts.image_button import ImageButton
from scripts.loading_screen import LoadingScreen
from slink import SLink
from tutorial import HelpWindow
import pygetwindow as gw


def function_timer(func):
    def wrapper():
        start = time.time()
        func()
        print(time.time() - start)

    return wrapper


def center_popup(popup):
    popup.grab_set()
    # popup.attributes('-topmost', 'true')
    popup.attributes('-alpha', 0)
    popup.update()
    x = app.winfo_x()
    y = app.winfo_y()
    w = app.winfo_width()
    h = app.winfo_height()
    popup.geometry("+%d+%d" % (x + w / 2 - popup.winfo_width() / 2, y + h / 2 - popup.winfo_height() / 2))
    popup.attributes('-alpha', 100)


def fill_text(text):
    text_field.delete(0, 'end')
    text_field.insert(0, text)


@function_timer
def open_compendium():
    center_popup(compendium_popup)
    compendium_popup.show()
    # compendium_popup.grab_set()


@function_timer
def open_slink():
    center_popup(slink_popup)
    slink_popup.show()


@function_timer
def open_help():
    help_popup = HelpWindow()
    center_popup(help_popup)


def scan_compendium():
    Thread(thread_scan_compendium()).start()


def thread_scan_compendium():
    helper.scan_compendium()
    windows = gw.getWindowsWithTitle("Persona 5 Royal")
    windows[0].activate()
    compendium_popup.update_checkboxes()
    app.attributes('-topmost', True)
    app.attributes('-topmost', False)


def check_fusion(name, index={}):
    global result_index, max_index, index_dict
    result_index = 0
    index_dict = index
    max_index = helper.can_fuse(target_persona=name, indices=index_dict)
    print(max_index)
    left.configure(state="disabled", image=arrow_l_disabled)
    right.configure(state="disabled", image=arrow_r_disabled)
    if name != "" and max_index > 0:
        # cost_label.configure(text=f"Cost: {locale.currency(helper.calculate_fusion_cost(), grouping=True)}")
        show_cost()
        add_to_compendium.configure(state='normal')
    print(f"price {helper.calculate_fusion_cost()}")
    # print(f"cheapest price {helper.calculate_cheapest_fusion(name)}")


def show_cheapest_fusion():
    thread = Thread(target=show_cheapest_fusion_thread)
    thread.start()


def show_cheapest_fusion_thread():
    global index_dict
    current_persona = helper.get_current_result()
    if current_persona == "":
        return
    result = helper.calculate_cheapest_fusion(current_persona)
    check_fusion(current_persona, result[1])


@function_timer
def next_recipe():
    global result_index
    left.configure(state="normal", image=arrow_l)
    if result_index + 1 < max_index:
        result_index += 1
        index_dict[current_node] = result_index
        helper.can_fuse(target_persona=text_field.get(), indices=index_dict, new_fusion=True)
    if result_index + 1 >= max_index:
        right.configure(state="disabled", image=arrow_r_disabled)
    # cost_label.configure(text=f"Cost: {locale.currency(helper.calculate_fusion_cost(), grouping=True)}")
    show_cost()


@function_timer
def previous_recipe():
    global result_index
    right.configure(state="normal", image=arrow_r)
    if result_index - 1 >= 0:
        result_index -= 1
        index_dict[current_node] = result_index
        helper.can_fuse(target_persona=text_field.get(), indices=index_dict, new_fusion=True)
    if result_index - 1 < 0:
        left.configure(state="disabled", image=arrow_l_disabled)
    # cost_label.configure(text=f"Cost: {locale.currency(helper.calculate_fusion_cost(), grouping=True)}")
    show_cost()


def show_cost():
    cost_label.configure(text=f"Cost: {locale.currency(helper.calculate_fusion_cost(), grouping=True)}")
    leafs = helper.get_leaf_nodes()
    zero_cost = False
    for leaf in leafs:
        if helper.persona_map[leaf].cost == 0:
            cost_info.pack(padx=5, side='left')
            zero_cost = True
            break
    if not zero_cost:
        cost_info.pack_forget()


def add_personas():
    graph = helper.get_current_graph()
    personas = graph.nodes()
    message = ''
    print(f'P: {personas}')
    for p in personas:
        if not helper.persona_map[p].owned:
            helper.persona_map[p].set_owned(True)
            message += f'{p}, '
    message = message[:len(message) - 2]
    if len(personas) > 1:
        message += ' have been added to your Compendium.'
    else:
        message += ' had been added to your Compendium.'
    helper.update_my_personas()
    helper.save_compendium()
    compendium_popup.update_checkboxes()
    dropdown.configure(values=helper.persona_map.values())
    center_popup(CTkMessagebox(title='info', message=message))
    add_to_compendium.configure(state='disabled')


def set_current_node(value):
    global current_node, result_index, max_index
    current_node = value
    if current_node not in index_dict.keys():
        result_index = 0
        index_dict[current_node] = 0
    else:
        result_index = index_dict[current_node]
    # disable right arrow if there is only one recipe or the last one is already selected
    max_index = len(helper.persona_map[current_node].fusion_material_list)
    if max_index <= 1 or result_index == max_index - 1:
        right.configure(state="disabled", image=arrow_r_disabled)
    else:
        right.configure(state="normal", image=arrow_r)
    # disable left arrow if the first recipe is selected
    if result_index == 0:
        left.configure(state="disabled", image=arrow_l_disabled)
    else:
        left.configure(state="normal", image=arrow_l)


def on_closing():
    os._exit(1)


index_dict = {}
current_node = ""
result_index = 0
max_index = 0
BORDER_COLOR = "#1F6AA5"
# japanese local for the correct currency
locale.setlocale(locale.LC_ALL, 'ja_JP.utf8')

# setup UI
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
loading_screen = LoadingScreen()
app.geometry("643x667")
# 643x627
app.title("Persona 5 Royal Fusion Helper")

app.resizable(False, False)
app.iconbitmap(resource_path("Assets/main_icon.ico"))
app.protocol("WM_DELETE_WINDOW", on_closing)

# option_menu = customtkinter.CTkOptionMenu(app, values=['Name', 'Level'], command=optionmenu_callback)
# option_menu.grid(row=0, column=0, padx=10, pady=10)
compendium_button = customtkinter.CTkButton(app, text="Compendium", command=lambda: open_compendium())
compendium_button.place(x=490, y=10)

slink_button = customtkinter.CTkButton(app, text="Social Links", command=lambda: open_slink())
slink_button.place(x=490, y=60)

help_button = ImageButton(master=app, image_path="Assets/help-2.png", command=open_help, size=(30, 30))
help_button.place(x=10, y=10)

text_field = customtkinter.CTkEntry(app, width=200)
text_field.grid(row=0, column=0, padx=10, pady=10)

scan = customtkinter.CTkButton(app, text="Scan Compendium", command=lambda: scan_compendium())
scan.grid(row=1, column=0, padx=10, pady=10)

check = customtkinter.CTkButton(app, text="Check", command=lambda: check_fusion(text_field.get()))
check.grid(row=2, column=0, padx=10, pady=10)

arrow_l = customtkinter.CTkImage(dark_image=Image.open(resource_path("Assets/arrow_l.png")))
arrow_l_disabled = customtkinter.CTkImage(dark_image=Image.open(resource_path("Assets/arrow_l_disabled.png")))
left = customtkinter.CTkButton(app, text="", width=10, command=lambda: previous_recipe(), image=arrow_l_disabled,
                               state="disabled")
left.place(x=210, y=106)

arrow_r = customtkinter.CTkImage(dark_image=Image.open(resource_path("Assets/arrow_r.png")))
arrow_r_disabled = customtkinter.CTkImage(dark_image=Image.open(resource_path("Assets/arrow_r_disabled.png")))
right = customtkinter.CTkButton(app, text="", width=10, command=lambda: next_recipe(), image=arrow_r_disabled,
                                state="disabled")
right.place(x=394, y=106)

cost_frame = customtkinter.CTkFrame(master=app, fg_color='gray14')
cost_frame.place(x=10, y=110)
cost_label = customtkinter.CTkLabel(master=cost_frame, text="Cost: N/A", text_color="white", font=('Helvetica', 15))
cost_label.pack(side='left')
img = customtkinter.CTkImage(dark_image=Image.open(resource_path('Assets/info.png')), size=(15, 15))
cost_info = customtkinter.CTkLabel(master=cost_frame, text='', image=img)
CTkToolTip(cost_info, message='This calculation uses Persona(s)\n with a cost of ¥0')

cheapest_fusion = customtkinter.CTkButton(master=app, text="min cost", width=50, command=lambda: show_cheapest_fusion())
cheapest_fusion.place(x=10, y=80)

plotframe = customtkinter.CTkFrame(master=app, fg_color="gray14", width=640, height=480, border_color=BORDER_COLOR,
                                   border_width=0)
plotframe.grid(row=3, column=0)

border = customtkinter.CTkFrame(master=app, fg_color=BORDER_COLOR, width=643, height=2)
border.place(x=0, y=150)

helper = FusionHelper(center_popup, plotframe, set_current_node)
compendium_popup = Compendium(helper.persona_map, helper)
center_popup(compendium_popup)
compendium_popup.hide()

slink_popup = SLink(helper)
center_popup(slink_popup)
slink_popup.hide()

helper.can_fuse_all()
c = 0
for p in helper.persona_map.values():
    if p.can_be_fused:
        # print(p)
        c += 1
print(f'{c} personas can be fused')

dropdown = CTkScrollableDropdown(text_field, values=helper.persona_map.values(),
                                 command=lambda e: fill_text(e), autocomplete=True)  # Using autocomplete
helper.set_dropdown(dropdown)

add_to_compendium = customtkinter.CTkButton(app, text='Add Persona(s)', state='disabled',
                                            command=lambda: add_personas())
add_to_compendium.grid(row=5, column=0, pady=5)
loading_screen.destroy()
app.mainloop()
