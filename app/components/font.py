from functools import cache

import mpl_fontkit as fk


class FontFamily:
    fonts = ["Source Sans Pro", "Roboto", "Open Sans", "Noto Sans", "Raleway",
             "Lato", "Montserrat", "Inter", "Oswald"]

    def __init__(self):
        self.register()
        self.font_list = fk.list_fonts()

    @cache
    def register(self):
        for f in self.fonts:
            fk.install(f, as_global=False)
