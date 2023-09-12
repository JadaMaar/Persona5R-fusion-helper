from sys import platform
from webbrowser import open_new_tab
from customtkinter import *

from scripts.data_path import resource_path


class HelpWindow(CTkToplevel):
    def __init__(self):
        super().__init__()
        # self.geometry("400x380")
        self.title("How to use")
        self.iconbitmap(resource_path("Assets/compendium_icon.ico"))
        if platform.startswith("win"):
            self.after(200, lambda: self.iconbitmap(resource_path("Assets/compendium_icon.ico")))

        tabview = CTkTabview(self)
        tabview.pack()

        tabview.add("About")
        tabview.add("Scan")
        tabview.add("Fusion calculation")
        tabview.add("Graph")
        b = "• "
        about = CTkLabel(tabview.tab("About"), text="This tool was created in order to figure out which Personas can "
                                                    "be fused with a given set of Personas and the exact recipes to "
                                                    "achieve that. It is mainly supposed to help completionists to 100%"
                                                    " their Compendium or to see if you can get a specific Persona with"
                                                    " your current Compendium.\nAny feedback is much appreciated!\n\n"
                                                    "GitHub:", wraplength=280, justify="left")
        link = CTkLabel(tabview.tab("About"), text="https://github.com/JadaMaar/Persona5R-fusion-helper", wraplength=280, justify='left', cursor="hand2")
        discord = CTkLabel(tabview.tab("About"), text="Discord:\njadamaar\nOriginally known as JadaMaar#0937",
                           wraplength=280, justify="left")
        about.pack(anchor='w')
        link.pack(anchor='w')
        link.bind("<Button-1>", lambda e: open_new_tab("https://github.com/JadaMaar/Persona5R-fusion-helper"))
        discord.pack(anchor='w')

        text = f'Scanning the own Compendium\n' \
               f'{b}Open the Game\n' \
               f'{b}Navigate to the Compendium\n' \
               f'{b}Toggle "Registered Only"\n' \
               f'{b}Hover over the first entry\n' \
               f'{b}Click on "Scan Compendium"\n' \
               f'Pressing ESC during the scan will abort it\n\n' \
               f'Manually change Compendium\n' \
               f'{b}Click on "Compendium"\n' \
               f'{b}Select all owned Personas\n' \
               f'{b}Click on "Apply"'
        scan = CTkLabel(tabview.tab("Scan"), text=text, wraplength=280, justify="left")
        scan.pack(anchor='w')

        text = f"{b}Type the name of a Persona in the entry field (not case sensitive)\n" \
               f'{b}Click on "Check"\n' \
               f'{b}All involved Personas will be displayed as a DiGraph and the cost for summoning all required base' \
               f' Persona will be shown in top left "Cost" label.\n' \
               f'{b}The "min cost"-Button will check all possible combinations to determine the cheapest fusion. This' \
               f' can take a while due to the amount of possible combinations.\n\n' \
               f'Note:\n' \
               f'While typing there will be three types of Autocomplete-Buttons that show up.\n' \
               f'Normal:\n' \
               f'Persona isnt owned and can be fused\n' \
               f'Red disabled:\n' \
               f'Persona isnt owned and can not be fused\n' \
               f'Green disabled:\n' \
               f'Persona is already owned'
        fusion = CTkLabel(tabview.tab("Fusion calculation"), text=text, wraplength=280, justify="left")
        fusion.pack(anchor="w")

        graph = CTkLabel(tabview.tab("Graph"), text=f'Graph interactions:\n\n'
                                                    f'{b}Left-Click:\nA popup with '
                                                    'information about the selected Persona will show up. \n'
                                                    f'{b}Right-Click:\nThe clicked node '
                                                    'will be highlighted red. For the highlighted Persona you can '
                                                    'change the '
                                                    'recipe by using the "◁" and "▷" button. The '
                                                    'price will be '
                                                    'updated accordingly.', wraplength=280, justify="left")
        graph.pack(anchor='w')
