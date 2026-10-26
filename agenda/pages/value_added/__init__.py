"""Value-added pages, one module per page.

Registration happens at import (``@register``), so the import order below is the catalog order.
"""

from agenda.pages.value_added.monthly_quotes import MonthlyQuotes  # noqa: I001 (import order = catalog registration order)
from agenda.pages.value_added.vision_board import VisionBoard, VisionLayout
from agenda.pages.value_added.health import HealthTracker
from agenda.pages.value_added.meals import Meals, MealsLayout
from agenda.pages.value_added.gratitude import Gratitude, GratitudeLayout
from agenda.pages.value_added.media import Media, MediaLayout
from agenda.pages.value_added.travel import Travel, TravelLayout
from agenda.pages.value_added.challenge30 import Challenge30, ChallengeLayout
from agenda.pages.value_added.idea_map import IdeaLayout, IdeaMap
from agenda.pages.value_added.qr_codes import QRCodes, QRLayout
from agenda.pages.value_added.extras_guide import ExtrasGuide, ExtrasLayout
from agenda.pages.value_added.pack_entrepreneur import EntrepreneurLayout, PackEntrepreneur
from agenda.pages.value_added.pack_student import PackStudent, StudentLayout
from agenda.pages.value_added.pack_fitness import FitnessLayout, PackFitness

__all__ = [
    "Challenge30",
    "ChallengeLayout",
    "EntrepreneurLayout",
    "ExtrasGuide",
    "ExtrasLayout",
    "FitnessLayout",
    "Gratitude",
    "GratitudeLayout",
    "HealthTracker",
    "IdeaLayout",
    "IdeaMap",
    "Meals",
    "MealsLayout",
    "Media",
    "MediaLayout",
    "MonthlyQuotes",
    "PackEntrepreneur",
    "PackFitness",
    "PackStudent",
    "QRCodes",
    "QRLayout",
    "StudentLayout",
    "Travel",
    "TravelLayout",
    "VisionBoard",
    "VisionLayout",
]
