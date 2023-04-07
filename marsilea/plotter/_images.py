import numpy as np
from matplotlib.image import imread, BboxImage
from matplotlib.transforms import Bbox, TransformedBbox
from pathlib import Path

from urllib.request import urlretrieve

from .base import RenderPlan

from platformdirs import user_cache_dir

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
        self.data = codes
        self.emoji_caches = {}
        for c in codes:
            cache_image = _cache_remote(f"{TWEMOJI_CDN}{c}.png")
            self.emoji_caches[c] = imread(cache_image)

        self.scale = scale
        self.mode = mode

    def render_ax(self, ax, data):

        locs = np.linspace(0, 1, len(data)+2)[1:-1]
        print(locs)
        for loc, d in zip(locs, data):
            img = self.emoji_caches[d]
            width, height = img.shape[:2]

            def get_emoji_bbox(renderer):
                x0, y0 = ax.transData.transform((loc, 0))
                print(x0, y0)
                return Bbox.from_bounds(x0, y0, width, height)

            i1 = BboxImage(get_emoji_bbox,
                           data=img)
            ax.add_artist(i1)
