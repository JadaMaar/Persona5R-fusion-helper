import time
from difflib import SequenceMatcher
from time import sleep

import PIL
import cv2
import mss
import numpy as np
import tesserocr
from CTkMessagebox import CTkMessagebox
from PIL import Image
import PIL.ImageOps
from keyboard import add_hotkey
from pynput.keyboard import Controller, Key

from scripts.data_path import resource_path


class CompendiumScanner:
    def __init__(self, persona_map, center_popup):
        self._center_popup = center_popup
        self.persona_map = persona_map
        self._keyboard = Controller()
        self._sct = mss.mss()
        self._api = tesserocr.PyTessBaseAPI(path=resource_path("data/"), lang='eng')
        self._api.SetPageSegMode(7)

        self._number_api = tesserocr.PyTessBaseAPI(path=resource_path("data/"), lang="eng")
        self._number_api.SetPageSegMode(tesserocr.PSM.SINGLE_WORD)
        self._num_detected = 0
        self._number_api.SetVariable("tessedit_char_whitelist", "0123456789")
        self._number_api.SetVariable("tessedit_char_blacklist", "¥")
        self._scan_in_progress = False
        add_hotkey("esc", self._abort_scan)

        # flag to differentiate Orpheus (Picaro) and Orpheus F (Picaro) the first instance or Orpheus is M
        # which will set the flag to indicate the next instance to be Orpheuse F
        self.orpheus_f = False
        self.orpheus_picaro_f = False

    def _abort_scan(self):
        self._scan_in_progress = False

    def check_conditions(self):
        compendium_screenshot = self.take_screenshot({"top": 780, "left": 1620, "width": 230, "height": 50})
        self._api.SetImage(compendium_screenshot)
        text = self._api.GetUTF8Text().replace("\n", "")
        print(text)
        if text != "Check Compendium" and "Check Registry" not in text:
            self._center_popup(CTkMessagebox(title="Info", message="Please go to the Compendium Screen."))
            return False
        registered_only_screenshot = self.take_screenshot({"top": 70, "left": 620, "width": 250, "height": 120})
        registered_only_screenshot = registered_only_screenshot.rotate(-21, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
        self._api.SetImage(registered_only_screenshot)
        text = self._api.GetUTF8Text().replace("\n", "")
        print(text)
        if text != "Registered":
            self._keyboard.press(Key.tab)
            time.sleep(0.5)
        first_selected_screenshot = self.take_screenshot({"top": 260, "left": 590, "width": 40, "height": 20}).convert('L')
        contains_black = False
        for pixel_value in first_selected_screenshot.getdata():
            if pixel_value == 0:
                contains_black = True
                break
        if contains_black:
            self._center_popup(CTkMessagebox(title="Info", message="Please hover over the first Compendium entry."))
            return False
        return True

    def scan_compendium(self):
        self._scan_in_progress = True
        personas = []
        x1 = 410
        y1 = 280  # 250
        x2 = 730
        y2 = 335
        height = 75

        lvl_x = 328  # 325
        lvl_y = 302  # 300

        price_x = 790
        price_y = 250

        check_box = self.take_screenshot({"top": 710, "left": 1000, "width": 1, "height": 1})
        started_scroll = False
        i = 0
        self._num_detected = 0
        while _contains_red(check_box) or not started_scroll:
            # abort scan if _scan_in_progress = False
            if not self._scan_in_progress:
                return

            # takes a screenshot to the right of the second bottom most persona to check it for red color
            # it will only not be red for the first 6 entries or once the end has been reached
            check_box = self.take_screenshot({"top": 687, "left": 1080, "width": 1, "height": 1})
            last_check_box = self.take_screenshot({"top": 760, "left": 1080, "width": 1, "height": 1})

            # check is last compendium entry has been reached
            if not _contains_red(check_box) and _contains_red(last_check_box):
                y1 += height
                y2 += height
                lvl_y += height
                x1 += 16
                x2 += 16
                lvl_x += 16

            # persona name label screenshot
            im = self.take_screenshot({"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1})
            im = im.convert('L')
            im = PIL.ImageOps.invert(im)
            i += 1

            # use ocr to access the text
            self._api.SetImage(im)
            text = self._api.GetUTF8Text()
            # debug
            # if text == "":
            #     im.show()
            #     break
            # print(f'before: {text}')
            if text not in self.persona_map.keys():
                text = self._find_closest_match(text)

            # persona level label screenshot
            lvl = self.take_screenshot({"top": lvl_y, "left": lvl_x, "width": 45, "height": 46})
            lvl = PIL.ImageOps.invert(lvl)
            lvl = _non_black_to_white(lvl).convert('RGBA').rotate(-6, resample=Image.BICUBIC,
                                                                  fillcolor=(255, 255, 255))

            # persona price label screenshot
            price = self.take_screenshot({"top": price_y, "left": price_x, "width": 200, "height": 60})
            price = PIL.ImageOps.invert(price)
            price = _non_black_to_white(price).convert('RGBA').rotate(-6, resample=Image.BICUBIC,
                                                                      fillcolor=(255, 255, 255))

            # move down 6 entries before the list starts to scroll
            if not _contains_red(check_box):
                y1 += height
                y2 += height
                lvl_y += height
                price_y += height
                x1 += 16
                x2 += 16
                lvl_x += 16
                price_x += 16
            else:
                started_scroll = True

            # Thread(target=self._thread_lvl_ocr(lvl, text)).start()
            self._thread_lvl_ocr(lvl, text)
            self._thread_price_ocr(price, text)

            # add persona name to the list of personas
            personas.append(self.persona_map[text])
            self.persona_map[text].owned = True

            # go down by one
            self._keyboard.press('s')
            sleep(0.1)
            self._keyboard.release('s')

            # print(f'after: {text}')

        print(f'{self._num_detected} out of {i} numbers identified correctly')
        return self.persona_map

    def _thread_lvl_ocr(self, lvl, name):
        self._number_api.SetPageSegMode(7)
        self._number_api.SetImage(lvl)
        self._number_api.Recognize(0)
        lvl_text = self._number_api.GetUTF8Text()
        lvl_text = lvl_text.replace('\n', '').replace(' ', '')

        if lvl_text.isnumeric():
            self.persona_map[name].current_level = int(lvl_text)
            self._num_detected += 1
        else:
            # find the best psm mode for every single screenshot
            psm = tesserocr.PSM
            for mode in range(14):
                self._number_api.SetPageSegMode(mode)
                self._number_api.SetImage(lvl)
                lvl_text = self._number_api.GetUTF8Text()
                lvl_text = lvl_text.replace('\n', '').replace(' ', '')

                if lvl_text.isnumeric():
                    # set current level to the one from the image
                    current_level = int(lvl_text)
                    if current_level >= self.persona_map[name].level:
                        self.persona_map[name].current_level = current_level
                        self._num_detected += 1
                        return
            print(f'{name} lvl: {lvl_text}')

    def _thread_price_ocr(self, price, name):
        self._number_api.SetPageSegMode(7)
        # remove yen symbol from the screenshot
        img_rgb = np.array(price.convert('RGB'))
        template = cv2.imread(resource_path('Assets/yen.png'))
        h, w = template.shape[:-1]

        res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
        threshold = .8
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):  # Switch columns and rows
            cv2.rectangle(img_rgb, pt, (pt[0] + int(w / 1), pt[1] + h), (255, 255, 255), -1)
        yen_removed_price = Image.fromarray(img_rgb)

        self._number_api.SetImage(yen_removed_price)
        price_text = self._number_api.GetUTF8Text()
        price_text = price_text.replace('\n', '').replace(' ', '')

        if price_text.isnumeric():
            p = self.persona_map[name]
            if int(price_text) > p.cost:
                p.cost = int(price_text)
        else:
            # self._number_api.SetImage(price)
            for mode in range(14):
                self._number_api.SetPageSegMode(mode)
                self._number_api.SetImage(yen_removed_price)
                price_text = self._number_api.GetUTF8Text()
                price_text = price_text.replace('\n', '').replace(' ', '')
                if price_text.isnumeric():
                    p = self.persona_map[name]
                    if int(price_text) > p.cost:
                        p.cost = int(price_text)
                    break
        # yen_removed_price.show()

    def take_screenshot(self, area):
        sct_img = self._sct.grab(area)
        # convert to PIL image
        img = Image.new("RGB", sct_img.size)
        pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
        img.putdata(list(pixels))
        return img

    def _find_closest_match(self, text):
        max_match_percentage = 0
        result = ""
        matches = list(self.persona_map.keys())
        matches.append('M. Izanagi Picaro')
        for p in matches:
            current_match_percentage = SequenceMatcher(None, text, p).ratio()
            if current_match_percentage > max_match_percentage:
                max_match_percentage = current_match_percentage
                result = p
        if result == 'M. Izanagi Picaro':
            result = 'Magatsu-Izanagi Picaro'
        if result == "Orpheus F" and not self.orpheus_f:
            result = "Orpheus"
            self.orpheus_f = True
        if result == "Orpheus Picaro" and not self.orpheus_picaro_f:
            self.orpheus_picaro_f = True
        elif result == "Orpheus Picaro" and self.orpheus_picaro_f:
            result = "Orpheus F Picaro"
        return result


def _contains_red(image):
    image = image.convert('RGBA')
    pixdata = image.load()
    # check all pixels for red color
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            if pixdata[x, y] == (255, 0, 0, 255):
                return True
    return False


def _non_black_to_white(img):
    image = img.convert('RGBA')
    pixdata = image.load()
    # check all pixels for not black color
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            if pixdata[x, y][0] > 2 or pixdata[x, y][1] > 2 or pixdata[x, y][2] > 2:
                pixdata[x, y] = (255, 255, 255, 255)
    return image

