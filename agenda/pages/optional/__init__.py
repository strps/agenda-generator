"""Optional pages, one module per page.

Registration happens at import (``@register``), so the import order below is the catalog order.
"""

from agenda.pages.optional.goals import Goals  # noqa: I001 (import order = catalog registration order)
from agenda.pages.optional.important_dates import ImportantDates
from agenda.pages.optional.todo import Todo
from agenda.pages.optional.projects import Projects
from agenda.pages.optional.budget import Budget
from agenda.pages.optional.habits import Habits
from agenda.pages.optional.monthly_review import MonthlyReview
from agenda.pages.optional.schedule import Schedule
from agenda.pages.optional.holidays import Holidays
from agenda.pages.optional.passwords import Passwords

__all__ = [
    "Budget",
    "Goals",
    "Habits",
    "Holidays",
    "ImportantDates",
    "MonthlyReview",
    "Passwords",
    "Projects",
    "Schedule",
    "Todo",
]
