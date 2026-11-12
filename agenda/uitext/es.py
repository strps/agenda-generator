"""Spanish UI text."""

MESSAGES: dict[str, str] = {
    "common.ok": "Aceptar",
    "common.cancel": "Cancelar",
    "prefs.restart_note": "El cambio de idioma se aplica la próxima vez que se inicie la aplicación.",
    "tooltip.open_config": "Abre un archivo de configuración YAML. Sus valores se cargan en el panel "
    "de ajustes y reemplazan todos los ajustes actuales, y se reconstruye la "
    "vista previa.",
    "tooltip.save_config": "Guarda los ajustes actuales como archivo de configuración YAML. El "
    "archivo guardado se puede volver a cargar más tarde con Abrir.",
    "tooltip.export_pdf": "Abre el diálogo de exportación para elegir numeración de páginas, "
    "disposición, cuadernillos e intervalo de páginas, y luego escribe el PDF. "
    "Las páginas se generan en un hilo en segundo plano mientras se muestra una "
    "barra de progreso, así la ventana sigue respondiendo.",
    "tooltip.prev": "Va a la página, el pliego doble o la hoja anterior. El tamaño del paso depende "
    "del modo actual: una página en Individual, un pliego doble en Doble, una hoja de "
    "impresora en Hoja.",
    "tooltip.next": "Va a la página, el pliego doble o la hoja siguiente. El tamaño del paso depende "
    "del modo actual: una página en Individual, un pliego doble en Doble, una hoja de "
    "impresora en Hoja.",
    "tooltip.mode_single": "Modo individual: muestra una página a la vez. Útil para revisar el diseño "
    "de una página concreta.",
    "tooltip.mode_spread": "Modo doble: muestra las páginas izquierda y derecha tal como se enfrentan "
    "al encuadernar. Es el modo predeterminado y el mejor para revisar los "
    "márgenes alternos.",
    "tooltip.mode_sheet": "Modo hoja: muestra la hoja de impresora impuesta, con las páginas "
    "colocadas tal como se imprimen. Solo se aplica a cuadernillos plegados; de "
    "lo contrario no hay hojas.",
    "tooltip.appearance": "Aspecto de la aplicación: oscuro, claro o del sistema (sigue el tema del "
    "escritorio). La elección se guarda entre sesiones.",
    "tooltip.color_swatch": "Haz clic para elegir este color en un diálogo de color. Muestra el color "
    "vigente.",
    "tooltip.color_clear": "Quita el color personalizado y vuelve a usar el color del tema.",
    "tooltip.font_browse": "Elige un archivo de fuente .ttf u .otf. También se usan los archivos en "
    "negrita y cursiva que estén junto a él.",
    "tooltip.global_section": "Ajustes de toda la agenda: tamaño de página, márgenes, cuadernillos, "
    "año, idioma, planificadores y numeración de páginas.",
    "tooltip.padding_section": "Qué página rellena el último cuadernillo para que termine en una hoja "
    "completa, y el número mínimo de páginas de relleno. La página de "
    "relleno se configura en su propia sección, que muestra una insignia "
    "de relleno y un recuadro con aro.",
    "tooltip.month_start_section": "Páginas impresas justo después de cada página mensual, una por "
    "mes (p. ej., el presupuesto o el seguimiento de hábitos de ese "
    "mes). Una página marcada lleva aro en su propia sección y ya no "
    "se imprime después del planificador.",
    "tooltip.month_end_section": "Páginas impresas después de la última semana de cada mes, una por "
    "mes (p. ej., la revisión de ese mes). Una página marcada lleva aro "
    "en su propia sección y ya no se imprime después del planificador. "
    "Una página puede estar al inicio o al final, no en ambos.",
    "tooltip.styling_section": "Estilo del PDF generado: tema, colores y fuentes. El aspecto de esta "
    "aplicación está en Ajustes > Preferencias y nunca cambia el PDF.",
    "tooltip.preferences": "Aspecto de la interfaz; no cambia el PDF.",
    "tooltip.zoom": "Zoom de la vista previa. Elige ajustar para escalar las páginas al espacio "
    "disponible, o un porcentaje fijo como 100%.",
    "export.help.page_range": "Exporta solo algunas páginas, p. ej. 1-4,9. Déjalo vacío o escribe all "
    "para todas las páginas.",
    "export.help.page_range_detail": "Las páginas se numeran por su posición en la agenda, empezando "
    "en 1. Un intervalo de páginas solo funciona con la disposición "
    "de páginas individuales (no con pliegos dobles ni "
    "cuadernillos). Los números impresos en las páginas conservan "
    "sus valores de la agenda completa. No se guarda en el archivo "
    "de ajustes. CLI: --page-range.",
    "export.help.layout_pages": "Una página de la agenda por página del PDF, en orden.",
    "export.help.layout_pages_detail": "La disposición predeterminada. Necesaria para un intervalo de "
    "páginas. Los cuadernillos planos conservan su orden de "
    "páginas.",
    "export.help.layout_spreads": "Dos páginas lado a lado por hoja, en orden de lectura (sin "
    "plegar).",
    "export.help.layout_spreads_detail": "Activa los pliegos dobles y desactiva la imposición. La "
    "página 1 es una página derecha. Se aplican el tamaño de "
    "hoja y las marcas de corte. CLI: --spreads.",
    "export.help.layout_booklets": "Cuadernillos plegados impuestos para imprimir y grapar.",
    "export.help.layout_booklets_detail": "Activa la imposición y los cuadernillos plegados y "
    "desactiva los pliegos dobles. Las páginas se reordenan "
    "para que las hojas impresas se plieguen en cuadernillos. "
    "CLI: --imposition --folded.",
    "export.help.open_after": "Abre el PDF con el visor predeterminado una vez escrito.",
    "export.help.open_after_detail": "Solo se recuerda en la interfaz gráfica; la línea de comandos "
    "nunca abre el archivo.",
    "export.help.cli_preview": "El comando agenda-gen que produce el mismo PDF que estas opciones.",
    "export.help.cli_preview_detail": "Solo se listan las opciones que difieren de los valores "
    "predeterminados. Los ajustes fuera de este diálogo vienen del "
    "archivo de configuración (--config).",
    "export.help.browse_output": "Elige dónde se escribe el PDF.",
    "export.help.browse_output_detail": "Abre un diálogo de guardado; se añade la extensión .pdf si "
    "falta.",
    "export.disabled_reason": "La exportación está desactivada porque los ajustes actuales no son "
    "válidos. Corrige los ajustes resaltados para activarla.",
    "section_desc.front_back": "portada y contraportada y páginas preliminares: portada, datos "
    "personales, metas, resumen anual, notas, contactos y contraportada.",
    "section_desc.monthly": "páginas de resumen mensual, una por mes.",
    "section_desc.weekly": "páginas del planificador semanal.",
    "section_desc.daily": "páginas del planificador diario, una por día.",
    "section_desc.optional": "páginas de las categorías opcionales que activaste.",
    "section_desc.value_added": "páginas de las categorías de valor añadido que activaste.",
    "section_desc.padding": "páginas de relleno en blanco insertadas automáticamente para que los "
    "cuadernillos llenen hojas completas. Se muestran rayadas.",
    "bar.section.front_back": "Inicio/final",
    "bar.section.monthly": "Mensual",
    "bar.section.weekly": "Semanal",
    "bar.section.daily": "Diario",
    "bar.section.optional": "Opcional",
    "bar.section.value_added": "Valor añadido",
    "bar.section.padding": "Relleno",
    "app.title": "Generador de agendas",
    "legend.no_plan": "Sin agenda: corrige los ajustes",
    "summary.page.one": "{n} página",
    "summary.page.other": "{n} páginas",
    "summary.sheet.one": "{n} hoja",
    "summary.sheet.other": "{n} hojas",
    "summary.booklet.one": "{n} cuadernillo",
    "summary.booklet.other": "{n} cuadernillos",
    "summary.padding.one": "{n} página de relleno",
    "summary.padding.other": "{n} páginas de relleno",
    "summary.warning.one": "{n} advertencia",
    "summary.warning.other": "{n} advertencias",
    "preview.mode.single": "Página",
    "preview.mode.spread": "Doble",
    "preview.mode.sheet": "Hoja",
    "preview.label": "{mode} {span} de {total}",
    "export.group.page_numbers": "Numeración de páginas",
    "export.group.layout": "Disposición",
    "export.group.booklets": "Cuadernillos",
    "export.group.output": "Salida",
    "export.err.single_pages": "intervalo de páginas: un intervalo de páginas solo se puede exportar "
    "como páginas individuales",
    "export.err.page_range": "intervalo de páginas: {message}",
    "bar.page": "Página {n}",
    "bar.booklet_sheet": "Cuadernillo {booklet}, hoja {sheet}",
    "bar.blank": "En blanco",
    "bar.filler": "{name} (relleno)",
    "bar.week": "Semana {number} ({start}–{end})",
    "date.short": "{day} {month}",
    "date.weekday": "{weekday} {date}",
    "pad.short.pad_with": "relleno",
    "pad.short.weekly_filler": "relleno semanal",
    "pad.short.daily_filler": "relleno diario",
    "pad.short.month_start_pages": "inicio de mes",
    "pad.short.month_end_pages": "fin de mes",
    "pad.use.pad_with": "rellena el último cuadernillo",
    "pad.use.weekly_filler": "llena el hueco antes de un pliego semanal",
    "pad.use.daily_filler": "llena el hueco después de las páginas diarias de una semana",
    "pad.use.month_start_pages": "se imprime después de cada página mensual",
    "pad.use.month_end_pages": "se imprime después de la última semana de cada mes",
    "pad.text": "{short}: {use} (configurado en {section}).",
    "filler.blank": "En blanco: deja el hueco vacío.",
    "filler.none": "Ninguno: sin relleno; un pliego semanal puede empezar en una página derecha.",
    "page.text": "{name}: página {category}, {size}{repeat}{where}.",
    "page.category.core": "básica",
    "page.category.optional": "opcional",
    "page.category.value_added": "de valor añadido",
    "page.size.spread": "pliego doble de 2 páginas",
    "page.size.one": "{n} página",
    "page.size.many": "{n} páginas",
    "page.per_month": ", una por mes",
    "page.where": ", se configura en su sección {section}",
    "header.count": "La casilla fija {field} en 0 (desactivado) o en al menos 1 (activado).",
    "header.enable": "La casilla la incluye en la agenda.",
    "header.month_hint": "Elige Inicio o Fin de cada mes para imprimirla dentro de cada mes.",
    "header.ringed": "Una casilla con aro significa que la página se imprime ahí aunque la casilla "
    "esté desactivada.",
    "header.month_note": "Mientras esté colocada en cada mes, no se repite después del planificador.",
    "date.month_abbr.1": "ene",
    "date.month_abbr.2": "feb",
    "date.month_abbr.3": "mar",
    "date.month_abbr.4": "abr",
    "date.month_abbr.5": "may",
    "date.month_abbr.6": "jun",
    "date.month_abbr.7": "jul",
    "date.month_abbr.8": "ago",
    "date.month_abbr.9": "sep",
    "date.month_abbr.10": "oct",
    "date.month_abbr.11": "nov",
    "date.month_abbr.12": "dic",
    "date.month.1": "enero",
    "date.month.2": "febrero",
    "date.month.3": "marzo",
    "date.month.4": "abril",
    "date.month.5": "mayo",
    "date.month.6": "junio",
    "date.month.7": "julio",
    "date.month.8": "agosto",
    "date.month.9": "septiembre",
    "date.month.10": "octubre",
    "date.month.11": "noviembre",
    "date.month.12": "diciembre",
    "date.day_abbr.0": "lun",
    "date.day_abbr.1": "mar",
    "date.day_abbr.2": "mié",
    "date.day_abbr.3": "jue",
    "date.day_abbr.4": "vie",
    "date.day_abbr.5": "sáb",
    "date.day_abbr.6": "dom",
    "tooltip.ui_language": "Idioma del texto de la aplicación: sistema (sigue el escritorio), inglés o español. La elección se guarda entre sesiones y se aplica la próxima vez que se inicie la aplicación. No cambia el idioma del PDF impreso.",
    "prefs.language": "Idioma",
    "prefs.language.system": "sistema",
    "prefs.language.en": "English",
    "prefs.language.es": "Español",
    "prefs.title": "Preferencias",
    "prefs.appearance": "Apariencia",
    "prefs.appearance.dark": "oscuro",
    "prefs.appearance.light": "claro",
    "prefs.appearance.system": "sistema",
    "export.title": "Exportar PDF",
    "export.group.range_output": "Rango y salida",
    "export.all_pages": "todas ({total} páginas)",
    "export.all": "todas",
    "export.page_range_label": "rango de páginas",
    "export.browse": "Examinar...",
    "export.open_after": "abrir tras exportar",
    "export.cli_label": "comando equivalente",
    "export.export_button": "Exportar",
    "export.layout.pages": "Páginas sueltas",
    "export.layout.spreads": "Pliegos",
    "export.layout.booklets": "Cuadernillos",
    "app.open_config": "Abrir configuración",
    "app.save_config": "Guardar configuración",
    "app.export_pdf": "Exportar PDF",
    "app.menu_settings": "&Ajustes",
    "app.preferences": "Preferencias...",
    "app.template_disabled": "{label} está desactivada y no se incluye en la agenda.",
    "tabs.whole": "Agenda completa",
    "tabs.whole_tip": "Ajustes de toda la agenda, con su vista previa completa, barra de secciones "
    "y leyenda.",
    "settings.no_options": "Esta página no tiene ajustes propios. Marca la casilla de arriba para "
    "incluirla en la agenda.",
    "app.exporting": "Exportando...",
    "app.exported": "Exportado {path}",
    "app.export_failed": "Error al exportar: {message}",
    "app.yaml_open_filter": "YAML (*.yaml *.yml)",
    "app.yaml_save_filter": "YAML (*.yaml)",
    "section.include_tip": "Incluye esta plantilla en la agenda.",
    "legend.title": "Leyenda:",
    "legend.tip": "Los colores marcan las secciones de la agenda en la barra de arriba. El rayado marca el relleno (páginas en blanco de relleno).",
    "legend.chip_tip": "Haz clic para ir a la primera página de {label}; haz clic de nuevo para la siguiente.",
    "settings.none": "(ninguno)",
    "settings.one_per_line": "uno por línea",
    "settings.pages_title": "páginas (ninguna marcada = páginas básicas por defecto)",
    "settings.category": "<b>{category}</b>",
    "style.theme_default": "predeterminado del tema",
    "style.clear_glyph": "x",
    "style.browse": "Examinar...",
    "preview.button.single": "Individual",
    "preview.button.spread": "Doble",
    "preview.button.sheet": "Hoja",
    "preview.zoom_fit": "ajustar",
    "cli.help": "Genera un PDF de agenda imprimible.",
    "cli.version": "Muestra la versión.",
    "cli.list": "Lista el catálogo de páginas.",
    "cli.config": "Archivo de ajustes YAML; las opciones de la línea de comandos lo reemplazan.",
    "cli.category": "Lista de categorías separadas por comas: core,optional,value_added.",
    "cli.page_range": 'Exporta solo estas páginas, p. ej. "1-4,9" (solo páginas sueltas).',
    "cli.blank_pages": "Escribe N páginas en blanco en lugar de la agenda (temporal).",
    "cli.dry_run": "Imprime el resumen del plan; no genera nada.",
    "cli.error": "agenda-gen: {message}",
    "cli.unknown_theme": "aviso: tema desconocido {theme}; se usa minimal (conocidos: {known})",
    "cli.range_singles_only": "un rango de páginas solo se puede exportar como páginas sueltas",
    "cli.page_range_error": "rango de páginas: {message}",
    "cli.wrote": "escrito {path}",
}
