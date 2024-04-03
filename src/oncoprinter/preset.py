from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List

import marsilea.layers as mlayers
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

# The preset follows the style of cBioPortal as much as possible
# https://github.com/cBioPortal/cbioportal-frontend/blob/master/src/shared/components/oncoprint/geneticrules.ts
MUT_COLOR_MISSENSE = "#008000"
MUT_COLOR_MISSENSE_PASSENGER = "#53D400"
MUT_COLOR_INFRAME = "#993404"
MUT_COLOR_INFRAME_PASSENGER = "#a68028"
MUT_COLOR_TRUNC = "#000000"
MUT_COLOR_TRUNC_PASSENGER = "#708090"
MUT_COLOR_SPLICE = "#e5802b"
MUT_COLOR_SPLICE_PASSENGER = "#f0b87b"
MUT_COLOR_PROMOTER = "#00B7CE"
MUT_COLOR_OTHER = "#cf58bc"

MUT_DRIVER = "#000000"
MUT_VUS = "#696969"
MUT_COLOR_GERMLINE = "#FFFFFF"

MRNA_COLOR_HIGH = "#ff9999"
MRNA_COLOR_LOW = "#6699cc"

PROT_COLOR_HIGH = "#ff3df8"
PROT_COLOR_LOW = "#00E1FF"

CNA_COLOR_AMP = "#ff0000"
CNA_COLOR_GAIN = "#ffb6c1"
CNA_COLOR_HETLOSS = "#8fd8d8"
CNA_COLOR_HOMDEL = "#0000ff"

MUT_COLOR_FUSION = "#C900A1"
STRUCTURAL_VARIANT_COLOR = "#8B00C9"
STRUCTURAL_VARIANT_PASSENGER_COLOR = "#ce92e8"

DEFAULT_GREY = "#BEBEBE"


class Alteration(Enum):
    BACKGROUND = auto()
    AMP = auto()
    GAIN = auto()
    HOMDEL = auto()
    HETLOSS = auto()
    MRNA_HIGH = auto()
    MRNA_LOW = auto()
    PROTEIN_HIGH = auto()
    PROTEIN_LOW = auto()
    FUSION = auto()
    GERMLINE = auto()
    SPLICE = auto()
    SPLICE_PASSENGER = auto()
    MISSENSE = auto()
    MISSENSE_PASSENGER = auto()
    PROMOTER = auto()
    TRUNC = auto()
    TRUNC_PASSENGER = auto()
    INFRAME = auto()
    INFRAME_PASSENGER = auto()
    STRUCTURAL_VARIANT = auto()
    STRUCTURAL_VARIANT_PASSENGER = auto()
    # STRUCTURE_VARIANT

    OTHER = 10000


# Overwrite the default legend
# So that the legend entry will add a background
class _AltPiece:
    background_color = None

    def legend(self, x, y, w, h):
        arts = []
        if self.background_color is not None:
            arts.append(Rectangle((x, y), w, h, facecolor=self.background_color))
        arts.append(self.draw(x, y, w, h, None))
        return PatchCollection(arts, match_original=True)


class Rect(_AltPiece, mlayers.Rect):
    pass


class FrameRect(_AltPiece, mlayers.FrameRect):
    pass


class FracRect(_AltPiece, mlayers.FracRect):
    pass


@dataclass(repr=False)
class MatchRule:
    startswith: str = None
    endswith: str = None
    contains: List[str] = field(default_factory=list)
    flexible: bool = False

    def is_match(self, text: str):
        text = text.lower()

        match_start = not self.flexible
        if self.startswith is not None:
            match_start = text.startswith(self.startswith)

        match_end = not self.flexible
        if self.endswith is not None:
            match_end = text.endswith(self.endswith)

        match_contains = True
        if len(self.contains) > 0:
            match_contains = np.sum([i in text for i in self.contains])

        if self.flexible:
            return match_start | match_end | match_contains
        else:
            return match_start & match_end & match_contains


MATCH_POOL = {
    Alteration.AMP: MatchRule(startswith="amp"),
    Alteration.GAIN: MatchRule(startswith="gain"),
    Alteration.HOMDEL: MatchRule(
        startswith="homdel", contains=["deep", "deletion"], flexible=True
    ),
    Alteration.HETLOSS: MatchRule(
        startswith="hetloss", contains=["shallow", "deletion"], flexible=True
    ),
    Alteration.MRNA_HIGH: MatchRule(contains=["mrna", "high"]),
    Alteration.MRNA_LOW: MatchRule(contains=["mrna", "low"]),
    Alteration.PROTEIN_HIGH: MatchRule(contains=["protein", "high"]),
    Alteration.PROTEIN_LOW: MatchRule(contains=["protein", "low"]),
    Alteration.FUSION: MatchRule(startswith="fusion"),
    Alteration.GERMLINE: MatchRule(startswith="germline"),
    Alteration.MISSENSE_PASSENGER: MatchRule(
        startswith="missense", contains=["passenger"]
    ),
    Alteration.MISSENSE: MatchRule(
        startswith="missense", contains=["driver"], flexible=True
    ),
    Alteration.PROMOTER: MatchRule(startswith="promoter"),
    Alteration.TRUNC_PASSENGER: MatchRule(startswith="trunc", contains=["passenger"]),
    Alteration.TRUNC: MatchRule(startswith="trunc"),
    Alteration.INFRAME_PASSENGER: MatchRule(
        startswith="inframe", contains=["passenger"]
    ),
    Alteration.INFRAME: MatchRule(startswith="inframe"),
    Alteration.STRUCTURAL_VARIANT_PASSENGER: MatchRule(
        startswith="sv", contains=["structural", "variant", "passenger"], flexible=True
    ),
    Alteration.STRUCTURAL_VARIANT: MatchRule(
        startswith="sv", contains=["structural", "variant"], flexible=True
    ),
    Alteration.SPLICE_PASSENGER: MatchRule(startswith="splice", contains=["passenger"]),
    Alteration.SPLICE: MatchRule(startswith="splice"),
}

SHAPE_BANK = {
    Alteration.BACKGROUND: Rect(
        color=DEFAULT_GREY, label="No alterations", zorder=-10000
    ),
    # CNA
    Alteration.AMP: Rect(color=CNA_COLOR_AMP, label="Amplification"),
    # ShapeId.ampRectangle
    Alteration.GAIN: Rect(color=CNA_COLOR_GAIN, label="Gain"),
    # ShapeId.gainRectangle
    Alteration.HOMDEL: Rect(color=CNA_COLOR_HOMDEL, label="Deep Deletion"),
    Alteration.HETLOSS: Rect(color=CNA_COLOR_HETLOSS, label="Shallow Deletion"),
    # mRNA Regulation
    Alteration.MRNA_HIGH: FrameRect(
        color=MRNA_COLOR_HIGH, width=1.5, label="mRNA High", zorder=1000
    ),
    Alteration.MRNA_LOW: FrameRect(
        color=MRNA_COLOR_LOW, width=1.5, label="mRNA Low", zorder=1000
    ),
    # Protein Expression Regulation
    Alteration.PROTEIN_HIGH: FracRect(
        color=PROT_COLOR_HIGH, frac=(1.0, 0.2), label="Protein High", zorder=100
    ),
    Alteration.PROTEIN_LOW: FracRect(
        color=PROT_COLOR_LOW, frac=(1.0, 0.2), label="Protein Low", zorder=100
    ),
    # Structural variant
    Alteration.STRUCTURAL_VARIANT: FracRect(
        color=STRUCTURAL_VARIANT_COLOR,
        frac=(1.0, 0.6),
        label="Structural variant",
        zorder=200,
    ),
    Alteration.STRUCTURAL_VARIANT_PASSENGER: FracRect(
        color=STRUCTURAL_VARIANT_PASSENGER_COLOR,
        frac=(1.0, 0.6),
        label="Structural variant (putative passenger)",
        zorder=200,
    ),
    Alteration.FUSION: FracRect(
        color=MUT_COLOR_FUSION, frac=(1.0, 0.6), label="Fusion", zorder=200
    ),
    # Splice
    Alteration.SPLICE: FracRect(
        color=MUT_COLOR_SPLICE, frac=(1.0, 0.3), label="Splice Mutation", zorder=400
    ),
    Alteration.SPLICE_PASSENGER: FracRect(
        color=MUT_COLOR_SPLICE_PASSENGER,
        frac=(1.0, 0.3),
        label="Splice Mutation (putative passenger)",
        zorder=400,
    ),
    Alteration.MISSENSE: FracRect(
        color=MUT_COLOR_MISSENSE,
        frac=(1.0, 0.3),
        label="Mutation (putative driver)",
        zorder=400,
    ),
    Alteration.MISSENSE_PASSENGER: FracRect(
        color=MUT_COLOR_MISSENSE_PASSENGER,
        frac=(1.0, 0.3),
        label="Missense Mutation (putative passenger)",
        zorder=400,
    ),
    Alteration.OTHER: FracRect(
        color=MUT_COLOR_OTHER, frac=(1.0, 0.3), label="Other Mutation", zorder=400
    ),
    Alteration.PROMOTER: FracRect(
        color=MUT_COLOR_PROMOTER, frac=(1.0, 0.3), label="Promoter Mutation", zorder=400
    ),
    Alteration.TRUNC: FracRect(
        color=MUT_COLOR_TRUNC, frac=(1.0, 0.3), label="Truncating Mutation", zorder=400
    ),
    Alteration.TRUNC_PASSENGER: FracRect(
        color=MUT_COLOR_TRUNC_PASSENGER,
        frac=(1.0, 0.3),
        label="Truncating Mutation (putative passenger)",
        zorder=400,
    ),
    Alteration.INFRAME: FracRect(
        color=MUT_COLOR_INFRAME,
        frac=(1.0, 0.3),
        label="Inframe Mutation (putative driver)",
        zorder=400,
    ),
    Alteration.INFRAME_PASSENGER: FracRect(
        color=MUT_COLOR_INFRAME_PASSENGER,
        frac=(1.0, 0.3),
        label="Inframe Mutation (putative passenger)",
        zorder=400,
    ),
    # Germline
    Alteration.GERMLINE: FracRect(
        color=MUT_COLOR_GERMLINE, frac=(1.0, 0.1), label="Germline Mutation", zorder=600
    ),
}
