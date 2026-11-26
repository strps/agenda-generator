from agenda.gui import preview_model as M


def test_cut_warning_by_plan_index():
    from agenda.textfit import CutLog

    log = CutLog()
    log.add(5, "footer", "Long phrase")
    log.add(5, "header", "Long title")
    log.add(9, "footer", "Other")
    text = M.cut_warning(log, [4])
    assert "Header text" in text and "Footer text" in text and "Long phrase" in text
    assert "Other" not in text
    assert M.cut_warning(log, [0, 1]) == ""
    assert "Other" in M.cut_warning(log, [3, 8])
    assert M.cuts_tooltip(CutLog()) == ""
    assert "5, 9" in M.cuts_tooltip(log)
