# The implementation of Image in matplotlib may suffer from compatibility
# issues across different rendering backend at different DPI. Currently
# not a public API.
from functools import partial
from numbers import Number
from PIL import Image as PILImage

import numpy as np
from matplotlib.image import imread, BboxImage
from matplotlib.transforms import Bbox
from pathlib import Path
from platformdirs import user_cache_dir
from urllib.request import urlretrieve

from .base import RenderPlan


def _cache_remote(url, cache=True):
    data_dir = Path(user_cache_dir(appname="Marsilea"))
    data_dir.mkdir(exist_ok=True, parents=True)

    fname = url.split("/")[-1]
    dest = data_dir / fname
    if not (cache and dest.exists()):
        urlretrieve(url, dest)

    return dest


class Image(RenderPlan):
    def __init__(self,
                 images,
                 align="center",
                 scale=1,
                 resize=None,
                 ):
        self.images_mapper = {}

        for i, img in enumerate(images):
            if isinstance(img, str):
                # Read from URL
                if img.startswith("http") or img.startswith("https"):
                    img = imread(_cache_remote(img))
                else:
                    # Read from string path
                    img = imread(img)
            # Read from Path
            elif isinstance(img, Path):
                img = imread(img)
            else:
                # Read from array interface
                img = np.asarray(img)
            self.images_mapper[i] = img

        self.images_codes = np.asarray(list(self.images_mapper.keys()))

        self.images = images
        self.align = align
        self.scale = scale
        if resize is not None:
            if isinstance(resize, Number):
                resize = (resize, resize)
            for i, img in self.images_mapper.items():
                self.images_mapper[i] = (PILImage.fromarray(img)
                                         .resize(resize, PILImage.ANTIALIAS))
        self.set_data(self.images_codes)

    def _get_bbox_imges(self, ax, imgs, scale=1, align="center", ax_height=None, ax_width=None):

        locs = np.linspace(0, 1, len(imgs) + 1)

        xmin, ymin = ax.transAxes.transform((0, 0))
        xmax, ymax = ax.transAxes.transform((1, 1))

        if ax_width is None:
            ax_width = xmax - xmin
        if ax_height is None:
            ax_height = ymax - ymin

        base_dpi = ax.get_figure().get_dpi()

        bbox_images = []
        imgaes_sizes = []

        if self.is_body:

            for loc, img in zip(locs, imgs):
                width, height = img.shape[:2]

                fit_width = ax_width / len(imgs)
                fit_height = height / width * fit_width

                fit_scale_width = fit_width * scale
                fit_scale_height = fit_height * scale

                offset = (fit_width - fit_scale_width) / 2 / ax_width
                loc += offset

                if align == "top":
                    loc_y = 1 - fit_scale_height / ax_height
                elif align == "bottom":
                    loc_y = 0
                else:
                    loc_y = 0.5 - fit_scale_height / 2 / ax_height

                def img_bbox(renderer, loc, loc_y, width, height, base_dpi):
                    factor = renderer.dpi / base_dpi
                    x0, y0 = ax.transData.transform((loc, loc_y))
                    return Bbox.from_bounds(x0, y0, width * factor, height * factor)

                memorized_img_bbox = partial(
                    img_bbox,
                    loc=loc,
                    loc_y=loc_y,
                    width=fit_scale_width,
                    height=fit_scale_height,
                    base_dpi=base_dpi,
                )

                i1 = BboxImage(memorized_img_bbox, data=img)
                bbox_images.append(i1)
                imgaes_sizes.append(fit_scale_height)
        else:
            for loc, img in zip(locs, imgs[::-1]):
                width, height = img.shape[:2]

                fit_height = ax_height / len(imgs)
                fit_width = width / height * fit_height

                fit_scale_width = fit_width * scale
                fit_scale_height = fit_height * scale

                offset = (fit_height - fit_scale_height) / 2 / ax_height
                loc += offset

                if align == "right":
                    loc_x = 1 - fit_scale_width / ax_width
                elif align == "left":
                    loc_x = 0
                else:
                    loc_x = 0.5 - fit_scale_width / 2 / ax_width

                def img_bbox(renderer, loc_x, loc, width, height, base_dpi):
                    factor = renderer.dpi / base_dpi
                    x0, y0 = ax.transData.transform((loc_x, loc))
                    return Bbox.from_bounds(x0, y0, width * factor, height * factor)

                memorized_img_bbox = partial(
                    img_bbox,
                    loc_x=loc_x,
                    loc=loc,
                    width=fit_scale_width,
                    height=fit_scale_height,
                    base_dpi=base_dpi,
                )

                i1 = BboxImage(memorized_img_bbox, data=img)
                bbox_images.append(i1)
                imgaes_sizes.append(fit_scale_width)

        return bbox_images, max(imgaes_sizes)

    def render_ax(self, spec):
        ax = spec.ax
        imgs = [self.images_mapper[i] for i in spec.data]
        bbox_images, _ = self._get_bbox_imges(ax, imgs)
        for i in bbox_images:
            ax.add_artist(i)
        ax.set_axis_off()

    def get_canvas_size(self, figure, main_height=None, main_width=None, **kwargs) -> float:
        ax = figure.add_subplot(111)
        imgs = [self.images_mapper[i] for i in self.images_codes]
        _, size = self._get_bbox_imges(ax, imgs, ax_width=main_width, ax_height=main_height)
        ax.remove()
        return size


# ======== EMOJI Plotter ========

TWEMOJI_CDN = "https://cdn.jsdelivr.net/gh/twitter/twemoji/assets/72x72/"


class Emoji(Image):
    def __init__(self, codes, lang="en", scale=1):
        try:
            import emoji
        except ImportError:
            raise ImportError("Required emoji, try `pip install emoji`.")

        urls = []
        for i in codes:
            i = emoji.emojize(i, language=lang)
            if not emoji.is_emoji(i):
                raise ValueError(f"{i} is not a valid emoji")
            c = f"{ord(i):X}".lower()
            urls.append(f"{TWEMOJI_CDN}{c}.png")

        super().__init__(urls, scale=scale)
