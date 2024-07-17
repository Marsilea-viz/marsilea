# The implementation of Image in matplotlib may suffer from compatibility
# issues across different rendering backend at different DPI. Currently
# not a public API.
from functools import partial
from hashlib import sha256
from numbers import Number
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from matplotlib.image import imread, BboxImage
from matplotlib.transforms import Bbox
from platformdirs import user_cache_dir

from .base import RenderPlan


def _cache_remote(url, cache=True):
    try:
        import requests
    except ImportError:
        raise ImportError("Required requests, try `pip install requests`.")
    data_dir = Path(user_cache_dir(appname="Marsilea"))
    data_dir.mkdir(exist_ok=True, parents=True)

    hasher = sha256()
    hasher.update(url.encode("utf-8"))
    fname = hasher.hexdigest()

    dest = data_dir / fname
    if not (cache and dest.exists()):
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)

    return dest


class Image(RenderPlan):
    """Plot static images

    Parameters
    ----------
    images : array of image
        You can input either path to the image, URL, or numpy array.
    align : {"center", "top", "bottom", "left", "right"}, default: "center"
        The alignment of the images.
    scale : float, default: 1
        The scale of the images.
    spacing : float, default: 0.1
        The spacing between images, a value between 0 and 1,
        relative to the image container size.
    resize : int or tuple, default: None
        The size to resize the images.

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import numpy as np
        >>> import marsilea as ma
        >>> c = ma.ZeroWidth(height=2)
        >>> c.add_right(
        ...     ma.plotter.Image(
        ...         [
        ...             "https://www.iconfinder.com/icons/4375050/download/png/512",
        ...             "https://www.iconfinder.com/icons/8666426/download/png/512",
        ...             "https://www.iconfinder.com/icons/652581/download/png/512",
        ...         ],
        ...         align="right",
        ...     ),
        ...     pad=0.1,
        ... )
        >>> c.add_right(
        ...     ma.plotter.Labels(["Python", "Rust", "JavaScript"], fontsize=20), pad=0.1
        ... )
        >>> c.render()

    """

    def __init__(
        self,
        images,
        align="center",
        scale=1,
        spacing=0.1,
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
        if not 0 <= spacing <= 1:
            raise ValueError("spacing should be between 0 and 1")
        self.spacing = spacing
        if resize is not None:
            if isinstance(resize, Number):
                resize = (int(resize), int(resize))
            for i, img in self.images_mapper.items():
                self.images_mapper[i] = img.resize(resize, PILImage.Resampling.LANCZOS)
        for i, img in self.images_mapper.items():
            self.images_mapper[i] = np.asarray(img)
        self.set_data(self.images_codes)

    def _get_bbox_imges(
        self, ax, imgs, scale=1, align="center", ax_height=None, ax_width=None
    ):
        locs = np.linspace(0, 1, len(imgs) + 1)
        slot_size = locs[1] - locs[0]
        locs = locs[:-1] + slot_size * self.spacing / 2

        xmin, ymin = ax.transAxes.transform((0, 0))
        xmax, ymax = ax.transAxes.transform((1, 1))

        if ax_width is None or ax_width == 0:
            ax_width = xmax - xmin
        if ax_height is None or ax_height == 0:
            ax_height = ymax - ymin

        base_dpi = ax.get_figure().get_dpi()

        bbox_images = []
        imgaes_sizes = []

        if self.is_body:
            fit_width = ax_width / len(imgs) * (1 - self.spacing)
            for loc, img in zip(locs, imgs):
                height, width = img.shape[:2]
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
            fit_height = ax_height / len(imgs) * (1 - self.spacing)
            for loc, img in zip(locs, imgs[::-1]):
                height, width = img.shape[:2]
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

    def get_canvas_size(
        self, figure, main_height=None, main_width=None, **kwargs
    ) -> float:
        ax = figure.add_subplot(111)
        imgs = [self.images_mapper[i] for i in self.images_codes]
        _, size = self._get_bbox_imges(
            ax, imgs, ax_width=main_width, ax_height=main_height
        )
        ax.remove()
        return size


# ======== EMOJI Plotter ========

TWEMOJI_CDN = "https://cdn.jsdelivr.net/gh/twitter/twemoji/assets/72x72/"


class Emoji(Image):
    """Have fun with emoji images

    The emoji images are from `twemoji <https://twemoji.twitter.com/>`_.

    You can will all twemoji from `here <https://twemoji-cheatsheet.vercel.app/>`_

    Parameters
    ----------
    codes : array of str
        The emoji codes. You can input either unicode or short code.
    lang : str, default: "en"
        The language of the emoji.
    scale : float, default: 1
        The scale of the emoji.
    spacing : float, default: 0.1
        The spacing between emoji, a value between 0 and 1,
        relative to the emoji container size.

    Examples
    --------

    .. plot::

        >>> import marsilea as ma
        >>> c = ma.ZeroHeight(width=2)
        >>> c.add_top(ma.plotter.Emoji("😆😆🤣😂😉😇🐍🦀🦄"))
        >>> c.render()

    """

    def __init__(self, codes, lang="en", scale=1, spacing=0.1, **kwargs):
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

        super().__init__(urls, scale=scale, spacing=spacing, **kwargs)
