"""Pins catalog registration order and preset page lists (guards page-module splits)."""

from agenda.catalog import all_pages, preset_pages

CATALOG_IDS = [
    "cover", "back_cover", "personal_info", "yearly", "monthly", "weekly", "daily", "notes",
    "contacts", "goals", "important_dates", "todo", "projects", "budget", "habits",
    "monthly_review", "schedule", "holidays", "passwords", "quotes", "vision_board", "health",
    "meals", "gratitude", "media_log", "travel", "challenges30", "ideas", "qr",
    "physical_extras", "niche_entrepreneur", "niche_student", "niche_fitness",
]  # fmt: skip

PRESETS = {
    "essential": ["qr", "physical_extras", "niche_entrepreneur", "niche_student", "niche_fitness"],
    "complete": [
        "vision_board", "health", "meals", "gratitude", "travel", "challenges30", "qr",
        "physical_extras", "niche_entrepreneur", "niche_student", "niche_fitness",
    ],
    "premium": [
        "goals", "important_dates", "todo", "projects", "budget", "habits", "monthly_review",
        "schedule", "holidays", "passwords", "quotes", "vision_board", "health", "meals",
        "gratitude", "media_log", "travel", "challenges30", "ideas", "qr", "physical_extras",
        "niche_entrepreneur", "niche_student", "niche_fitness",
    ],
}  # fmt: skip


def test_catalog_order():
    assert [p.id for p in all_pages()] == CATALOG_IDS


def test_preset_pages():
    assert {n: preset_pages(n) for n in PRESETS} == PRESETS
