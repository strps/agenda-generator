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
        "schedule.title": "Horario semanal",
        "passwords.title": "Contraseñas",
        "passwords.warning": "No escribas contraseñas reales. Usa solo pistas o guarda esta agenda en un lugar seguro.",
        "passwords.site": "Sitio / servicio",
        "passwords.user": "Usuario",
        "passwords.password": "Contraseña o pista",
        "todo.title": "Lista de tareas",
        "todo.task": "Tarea",
        "todo.due": "Fecha",
        "budget.title": "Presupuesto {month} {year}",
        "budget.income": "Ingresos",
        "budget.fixed": "Gastos fijos",
        "budget.variable": "Gastos variables",
        "budget.savings": "Ahorro",
        "budget.amount": "Importe",
        "budget.total_income": "Total ingresos",
        "budget.total_expenses": "Total gastos",
        "budget.balance": "Balance",
        "habits.title": "Hábitos {month} {year}",
        "habits.habit": "Hábito",
        "review.title": "Revisión {month} {year}",
        "review.wins": "Logros",
        "review.challenges": "Desafíos",
        "review.lessons": "Lecciones aprendidas",
        "review.goals": "Metas del próximo mes",
        "review.rating": "Satisfacción general (1-5)",
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
        "quotes.title": "Frase de {month} {year}",
        "quotes.reflection": "Mi propia reflexión",
        "vision.title": "Tablero de visión",
        "vision.subtitle": "Mi visión para {year}",
        "vision.word": "Palabra del año",
        "health.title": "Salud {month} {year}",
        "health.mood": "Ánimo",
        "health.water": "Agua",
        "health.sleep": "Sueño (h)",
        "health.exercise": "Ejercicio",
        "health.other": "Otro",
        "gratitude.title": "Diario de gratitud",
        "gratitude.date": "Fecha",
        "gratitude.grateful": "Estoy agradecido por…",
        "gratitude.best": "Mejor momento del día",
        "gratitude.intention": "Intención para mañana",
        "media.title": "Libros, películas y series",
        "media.type": "Tipo",
        "media.book": "Libro",
        "media.movie": "Película",
        "media.series": "Serie",
        "media.name": "Título",
        "media.date": "Terminado",
        "media.rating": "Nota",
        "travel.title": "Planificador de viaje",
        "travel.destination": "Destino",
        "travel.from": "Desde",
        "travel.to": "Hasta",
        "travel.budget": "Presupuesto",
        "travel.itinerary": "Itinerario",
        "travel.day": "Día",
        "travel.packing": "Equipaje",
        "challenge.title": "Reto de 30 días",
        "challenge.mine": "Mi reto",
        "challenge.why": "Por qué",
        "challenge.reflection": "Reflexión",
        "meals.title": "Comidas y compras",
        "meals.breakfast": "Desayuno",
        "meals.lunch": "Almuerzo",
        "meals.dinner": "Cena",
        "meals.groceries": "Lista de compras",
        "quotes.1": "Empieza donde estás, con lo que tienes, y deja que el primer paso te enseñe el segundo.",
        "quotes.2": "Pequeños pasos constantes pesan más que grandes impulsos que se apagan.",
        "quotes.3": "Hoy es un buen día para terminar lo que ayer dejaste a medias.",
        "quotes.4": "Lo que cuidas con paciencia termina por dar fruto.",
        "quotes.5": "No esperes el momento perfecto: crea el momento y hazlo suficiente.",
        "quotes.6": "Descansar también es avanzar; el campo que reposa da mejor cosecha.",
        "quotes.7": "Cada día es una página en blanco y la tinta es tuya.",
        "quotes.8": "La constancia convierte lo difícil en costumbre y la costumbre en carácter.",
        "quotes.9": "Mira cuánto has recorrido antes de medir cuánto falta.",
        "quotes.10": "Elige con calma y actúa con firmeza: así se construyen los buenos días.",
        "quotes.11": "Agradecer lo pequeño hace más grande lo que ya tienes.",
        "quotes.12": "Cierra el año con gratitud y abre el siguiente con ganas.",
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
        "schedule.title": "Weekly schedule",
        "passwords.title": "Passwords",
        "passwords.warning": "Do not write real passwords. Use hints only, or keep this booklet in a safe place.",
        "passwords.site": "Site / service",
        "passwords.user": "User",
        "passwords.password": "Password or hint",
        "todo.title": "To-do list",
        "todo.task": "Task",
        "todo.due": "Due",
        "budget.title": "Budget {month} {year}",
        "budget.income": "Income",
        "budget.fixed": "Fixed expenses",
        "budget.variable": "Variable expenses",
        "budget.savings": "Savings",
        "budget.amount": "Amount",
        "budget.total_income": "Total income",
        "budget.total_expenses": "Total expenses",
        "budget.balance": "Balance",
        "habits.title": "Habits {month} {year}",
        "habits.habit": "Habit",
        "review.title": "Review {month} {year}",
        "review.wins": "Wins / achievements",
        "review.challenges": "Challenges",
        "review.lessons": "Lessons learned",
        "review.goals": "Goals for next month",
        "review.rating": "Overall satisfaction (1-5)",
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
        "quotes.title": "Quote for {month} {year}",
        "quotes.reflection": "My own reflection",
        "vision.title": "Vision board",
        "vision.subtitle": "My vision for {year}",
        "vision.word": "Word of the year",
        "health.title": "Health {month} {year}",
        "health.mood": "Mood",
        "health.water": "Water",
        "health.sleep": "Sleep (h)",
        "health.exercise": "Exercise",
        "health.other": "Other",
        "gratitude.title": "Gratitude journal",
        "gratitude.date": "Date",
        "gratitude.grateful": "I am grateful for…",
        "gratitude.best": "Best moment of the day",
        "gratitude.intention": "Intention for tomorrow",
        "media.title": "Books, movies and series",
        "media.type": "Type",
        "media.book": "Book",
        "media.movie": "Movie",
        "media.series": "Series",
        "media.name": "Title",
        "media.date": "Finished",
        "media.rating": "Rating",
        "travel.title": "Travel planner",
        "travel.destination": "Destination",
        "travel.from": "From",
        "travel.to": "To",
        "travel.budget": "Budget",
        "travel.itinerary": "Itinerary",
        "travel.day": "Day",
        "travel.packing": "Packing list",
        "challenge.title": "30-day challenge",
        "challenge.mine": "My challenge",
        "challenge.why": "Why",
        "challenge.reflection": "Reflection",
        "meals.title": "Meals and groceries",
        "meals.breakfast": "Breakfast",
        "meals.lunch": "Lunch",
        "meals.dinner": "Dinner",
        "meals.groceries": "Grocery list",
        "quotes.1": "Begin where you are, with what you have, and let the first step teach you the second.",
        "quotes.2": "Small steady steps outweigh big bursts that fade away.",
        "quotes.3": "Today is a good day to finish what you left half done yesterday.",
        "quotes.4": "What you tend with patience eventually bears fruit.",
        "quotes.5": "Do not wait for the perfect moment: make this one good enough.",
        "quotes.6": "Rest is progress too; the field that lies fallow yields the better harvest.",
        "quotes.7": "Every day is a blank page, and the ink is yours.",
        "quotes.8": "Consistency turns the hard into habit and habit into character.",
        "quotes.9": "Look at how far you have come before measuring how far is left.",
        "quotes.10": "Choose calmly and act firmly: that is how good days are built.",
        "quotes.11": "Giving thanks for small things makes what you have feel larger.",
        "quotes.12": "Close the year with gratitude and open the next with appetite.",
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
