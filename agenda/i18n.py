"""String tables for supported languages (es, en).

Conventions:
- Month and weekday names are stored in the form used in titles and headers
  (capitalized: "Enero", "Lunes"). Use ``.lower()`` for running text, which is
  the usual Spanish convention (``month_name(m, lang).lower()``).
- Short forms: months are 3 letters (Spanish "Set" is not used; "Sep"), weekdays
  3 letters (es "Lun", en "Mon"). Letter forms are one capital letter
  (es: L M X J V S D; en: M T W T F S S).
- Labels are keyed by dotted message id; formats use ``str.format`` fields.
- Only user-facing text is localized. Never use ``locale``.
"""

from __future__ import annotations

from typing import Final

LANGUAGES: Final = ("es", "en")
DEFAULT_LANGUAGE: Final = "es"

_MONTHS: Final[dict[str, tuple[str, ...]]] = {
    "es": (
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Setiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ),
    "en": (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
}
_MONTHS_SHORT: Final[dict[str, tuple[str, ...]]] = {
    "es": ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"),
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
}
# Monday-first.
_WEEKDAYS: Final[dict[str, tuple[str, ...]]] = {
    "es": ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"),
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
}
_WEEKDAYS_SHORT: Final[dict[str, tuple[str, ...]]] = {
    "es": ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"),
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
}
_WEEKDAYS_LETTER: Final[dict[str, tuple[str, ...]]] = {
    "es": ("L", "M", "X", "J", "V", "S", "D"),
    "en": ("M", "T", "W", "T", "F", "S", "S"),
}
_WEEKDAY_FORMS: Final = {
    "full": _WEEKDAYS,
    "short": _WEEKDAYS_SHORT,
    "letter": _WEEKDAYS_LETTER,
}

STRINGS: Final[dict[str, dict[str, str]]] = {
    "es": {
        "cover.year": "Agenda {year}",
        "cover.title": "Agenda",
        "personal.title": "Información personal",
        "personal.name": "Nombre",
        "personal.address": "Dirección",
        "personal.phone": "Teléfono",
        "personal.email": "Correo electrónico",
        "personal.emergency": "Contacto de emergencia",
        "personal.blood_type": "Tipo de sangre",
        "year.title": "Calendario {year}",
        "month.title": "{month} {year}",
        "month.label": "Mes",
        "week.label": "Semana",
        "week.number": "Semana {n}",
        "week.range": "{start} – {end}",
        "week.short": "S{n}",
        "day.label": "Día",
        "day.title": "{weekday} {day} de {month}",
        "notes.title": "Notas",
        "goals.title": "Metas del año",
        "goals.goal": "Meta {n}",
        "goals.step": "Paso",
        "goals.deadline": "Fecha límite",
        "dates.title": "Fechas importantes",
        "todo.title": "Lista de tareas",
        "todo.task": "Tarea",
        "todo.due": "Fecha",
        "projects.title": "Planificador de proyecto",
        "projects.name": "Proyecto",
        "projects.objective": "Objetivo",
        "projects.start": "Inicio",
        "projects.deadline": "Fecha límite",
        "projects.task": "Tarea",
        "projects.due": "Fecha",
        "projects.notes": "Notas",
        "contacts.title": "Contactos",
        "contacts.name": "Nombre",
        "contacts.phone": "Teléfono",
        "contacts.email": "Correo",
        "holidays.title": "Feriados",
        "holidays.label": "Feriado",
        "priorities": "Prioridades",
        "tasks": "Tareas",
        "schedule": "Horario",
        "back_cover.title": "Contraportada",
        "back_cover.line": "Que cada día cuente",
        "page.number": "Página {n}",
    },
    "en": {
        "cover.year": "Planner {year}",
        "cover.title": "Planner",
        "personal.title": "Personal information",
        "personal.name": "Name",
        "personal.address": "Address",
        "personal.phone": "Phone",
        "personal.email": "Email",
        "personal.emergency": "Emergency contact",
        "personal.blood_type": "Blood type",
        "year.title": "{year} Calendar",
        "month.title": "{month} {year}",
        "month.label": "Month",
        "week.label": "Week",
        "week.number": "Week {n}",
        "week.range": "{start} – {end}",
        "week.short": "W{n}",
        "day.label": "Day",
        "day.title": "{weekday}, {month} {day}",
        "notes.title": "Notes",
        "goals.title": "Yearly goals",
        "goals.goal": "Goal {n}",
        "goals.step": "Step",
        "goals.deadline": "Deadline",
        "dates.title": "Important dates",
        "todo.title": "To-do list",
        "todo.task": "Task",
        "todo.due": "Due",
        "projects.title": "Project planner",
        "projects.name": "Project",
        "projects.objective": "Objective",
        "projects.start": "Start",
        "projects.deadline": "Deadline",
        "projects.task": "Task",
        "projects.due": "Due",
        "projects.notes": "Notes",
        "contacts.title": "Contacts",
        "contacts.name": "Name",
        "contacts.phone": "Phone",
        "contacts.email": "Email",
        "holidays.title": "Holidays",
        "holidays.label": "Holiday",
        "priorities": "Priorities",
        "tasks": "Tasks",
        "schedule": "Schedule",
        "back_cover.title": "Back cover",
        "back_cover.line": "Make every day count",
        "page.number": "Page {n}",
    },
}


def check_language(lang: str) -> str:
    if lang not in STRINGS:
        raise ValueError(f"Unsupported language {lang!r}; expected one of {LANGUAGES}")
    return lang


def t(key: str, lang: str = DEFAULT_LANGUAGE, **fmt: object) -> str:
    """Look up ``key`` in ``lang`` and apply ``str.format(**fmt)``."""
    table = STRINGS[check_language(lang)]
    try:
        text = table[key]
    except KeyError:
        raise KeyError(f"Missing i18n key {key!r} for language {lang!r}") from None
    return text.format(**fmt) if fmt else text


class Strings:
    """Language-bound accessor: ``Strings(cfg.language)("week.number", n=3)``."""

    def __init__(self, lang: str = DEFAULT_LANGUAGE) -> None:
        self.lang = check_language(lang)

    def __call__(self, key: str, **fmt: object) -> str:
        return t(key, self.lang, **fmt)

    def month_name(self, m: int, short: bool = False) -> str:
        return month_name(m, self.lang, short)

    def weekday_names(self, week_start: str = "monday", form: str = "full") -> list[str]:
        return weekday_names(self.lang, week_start, form)


def month_name(m: int, lang: str = DEFAULT_LANGUAGE, short: bool = False) -> str:
    """Name of month ``m`` (1-12)."""
    if not 1 <= m <= 12:
        raise ValueError(f"Month must be 1-12, got {m}")
    table = _MONTHS_SHORT if short else _MONTHS
    return table[check_language(lang)][m - 1]


def weekday_names(
    lang: str = DEFAULT_LANGUAGE, week_start: str = "monday", form: str = "full"
) -> list[str]:
    """Seven weekday names starting at ``week_start``; form: full | short | letter."""
    if form not in _WEEKDAY_FORMS:
        raise ValueError(f"Unknown weekday form {form!r}; expected {tuple(_WEEKDAY_FORMS)}")
    if week_start not in ("monday", "sunday"):
        raise ValueError(f"week_start must be 'monday' or 'sunday', got {week_start!r}")
    names = list(_WEEKDAY_FORMS[form][check_language(lang)])
    return names if week_start == "monday" else [names[-1], *names[:-1]]


def weekday_name(index: int, lang: str = DEFAULT_LANGUAGE, form: str = "full") -> str:
    """Name for a Monday-based weekday index (``date.weekday()``, 0=Monday)."""
    return _WEEKDAY_FORMS[form][check_language(lang)][index]
