# The implementation of Image in matplotlib may suffer from compatibility
# issues across different rendering backend at different DPI. Currently
# not a public API.
from functools import partial

import numpy as np
from matplotlib.image import imread, BboxImage
from matplotlib.transforms import Bbox
from pathlib import Path
from platformdirs import user_cache_dir
from urllib.request import urlretrieve

from .base import RenderPlan

TWEMOJI_CDN = "https://cdn.jsdelivr.net/gh/twitter/twemoji/assets/72x72/"


def _cache_remote(url, cache=True):
    data_dir = Path(user_cache_dir(appname="Marsilea"))
    data_dir.mkdir(exist_ok=True, parents=True)

    fname = url.split("/")[-1]
    dest = data_dir / fname
    if not (cache and dest.exists()):
        urlretrieve(url, dest)

    return dest


class Emoji(RenderPlan):
    def __init__(self, images, lang="en", scale=1, mode="filled"):
        try:
            import emoji
        except ImportError:
            raise ImportError("Required emoji, try `pip install emoji`.")

        codes = []
        for i in images:
            i = emoji.emojize(i, language=lang)
            if not emoji.is_emoji(i):
                raise ValueError(f"{i} is not a valid emoji")
            codes.append(f"{ord(i):X}".lower())

        self.set_data(np.asarray(codes))
        self.emoji_caches = {}
        for c in codes:
            cache_image = _cache_remote(f"{TWEMOJI_CDN}{c}.png")
            self.emoji_caches[c] = imread(cache_image)

        self.scale = scale
        self.mode = mode

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        # TODO: Does not work for orient = "v"
        locs = np.linspace(0, 1, len(data) + 1)
        for loc, d in zip(locs, data):
            img = self.emoji_caches[d]
            width, height = img.shape[:2]

            xmin, ymin = ax.transAxes.transform((0, 0))
            xmax, ymax = ax.transAxes.transform((1, 1))

            ax_width = xmax - xmin
            ax_height = ymax - ymin

            fit_width = ax_width / len(data)
            fit_height = height / width * fit_width

            fit_scale_width = fit_width * self.scale
            fit_scale_height = fit_height * self.scale

            offset = (fit_width - fit_scale_width) / 2 / ax_width
            loc += offset

            loc_y = 0.5 - fit_scale_height / 2 / ax_height

            def get_emoji_bbox(renderer, loc, loc_y, width, height):
                x0, y0 = ax.transData.transform((loc, loc_y))
                return Bbox.from_bounds(x0, y0, width, height)

            partial_get_emoji_bbox = partial(get_emoji_bbox, loc=loc, loc_y=loc_y,
                                             width=fit_scale_width,
                                             height=fit_scale_height)

            i1 = BboxImage(partial_get_emoji_bbox, data=img)
            ax.add_artist(i1)
