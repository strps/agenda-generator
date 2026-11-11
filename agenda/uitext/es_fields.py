# ruff: noqa: ISC004
"""Spanish text for Config fields, sections and groups (data only).

English lives on ``Config`` (fields) and in ``templates.py`` (sections, groups); see
``agenda.fields`` and ``agenda.templates`` for the accessors. Field names, option values and
placeholders such as ``{n}`` are never translated.
"""

_HEX = "Color hexadecimal como #c85028 (también #abc o sin el #). Vacío = usa el color del tema."

# field name -> (label, short, detail)
FIELDS: dict[str, tuple[str, str, str]] = {
    "page_size": (
        "tamaño de página",
        "Tamaño de página: un nombre o WxH personalizado en mm.",
        "Tamaño de la página terminada. Use un nombre conocido (half_letter, a5, letter, a4, b6) "
        "o un tamaño personalizado escrito como WxH en milímetros. La orientación se aplica "
        "sobre él.",
    ),
    "orientation": (
        "orientación",
        "Orientación de la página.",
        "Si la página es más alta que ancha (portrait) o más ancha que alta (landscape). "
        "Intercambia el ancho y el alto del tamaño de página en todas las páginas.",
    ),
    "inner_margin": (
        "margen interior",
        "Margen del lado del encuadernado, en mm.",
        "Espacio libre, en mm, del lado de la página donde se encuaderna el cuadernillo. Un valor "
        "mayor aleja el contenido del pliegue y reduce el ancho del contenido.",
    ),
    "outer_margin": (
        "margen exterior",
        "Margen de los bordes exteriores, en mm.",
        "Espacio libre, en mm, en los bordes exteriores de la página, lejos del encuadernado. Un "
        "valor mayor reduce el área disponible para el contenido.",
    ),
    "bleed": (
        "sangrado",
        "Separación antes de cada marca de corte, en mm.",
        "Separación, en mm, entre la página y cada marca de corte. Solo tiene efecto cuando "
        "crop_marks está activado, lo que a su vez requiere imposition o spreads.",
    ),
    "booklet_size": (
        "tamaño del cuadernillo",
        "Tamaño de un cuadernillo, en hojas o páginas.",
        "Qué tan grande es un cuadernillo. Se cuenta en hojas o en páginas según booklet_unit "
        "(sheets o pages). Con páginas debe ser múltiplo de 4 en cuadernillos plegados y de 2 en "
        "los planos.",
    ),
    "booklet_unit": (
        "unidad del cuadernillo",
        "Unidad del tamaño del cuadernillo.",
        "Si booklet_size cuenta hojas o páginas. Una hoja plegada contiene 4 páginas y una hoja "
        "plana a doble cara contiene 2, así que 5 hojas son 20 páginas plegadas.",
    ),
    "booklet_folded": (
        "cuadernillo plegado",
        "Cuadernillos plegados (4 páginas por hoja) o planos.",
        "Activado: cuadernillos grapados al lomo con 4 páginas por hoja. Desactivado: hojas "
        "planas a doble cara con 2 páginas por hoja. La imposición requiere cuadernillos "
        "plegados.",
    ),
    "num_booklets": (
        "número de cuadernillos",
        "Número de cuadernillos, o auto.",
        "En cuántos cuadernillos se divide la agenda. Use auto para calcular el número según el "
        "contenido, o un número entero de al menos 1. El último cuadernillo se completa con "
        "pad_with.",
    ),
    "pad_with": (
        "relleno con",
        "Página usada para completar el último cuadernillo.",
        "Página del catálogo que se repite para completar el último cuadernillo y que termine en "
        "una hoja completa. Estas páginas de relleno aparecen como relleno en la barra de "
        "secciones. Por defecto es notes. La página se configura en su propia sección (p. ej. el "
        "patrón de Notas), que lleva la insignia de relleno.",
    ),
    "separate_covers": (
        "portadas aparte",
        "Mantener las portadas separadas de los cuadernillos.",
        "Activado: la portada y la contraportada se excluyen del conteo de cuadernillos, el "
        "relleno va antes de la contraportada y las portadas pueden imprimirse aparte en "
        "cartulina.",
    ),
    "creep_mm": (
        "deslizamiento (mm)",
        "Compensación de deslizamiento en hojas plegadas, en mm.",
        "Desplazamiento, en mm, aplicado a las páginas interiores de las hojas plegadas en la "
        "salida con imposición para compensar el grosor del papel. Es insignificante en "
        "cuadernillos pequeños y 0 lo desactiva.",
    ),
    "planners": (
        "planificadores",
        "Qué páginas de planificador incluir.",
        "Qué tipos de página de planificador se generan: weekly, daily o ambos. Las páginas "
        "diarias se limitan a los meses de daily_months, lo que también limita el número de "
        "páginas.",
    ),
    "daily_months": (
        "meses diarios",
        "Meses que tienen páginas diarias.",
        "Meses (1-12) que tienen páginas diarias, por ejemplo 1-6,9. Menos meses dan menos "
        "páginas y una agenda más delgada. Solo importa cuando se selecciona el planificador "
        "diario.",
    ),
    "pages": (
        "páginas",
        "Páginas del catálogo a incluir.",
        "Lista explícita de ids de páginas del catálogo a incluir. Si se define, siempre anula el "
        "preset. Si está vacía y no hay preset, se usan todas las páginas básicas.",
    ),
    "preset": (
        "preset",
        "Selección de páginas por puntaje de valor.",
        "Selecciona páginas por puntaje de valor: essential, complete o premium. Solo se usa "
        "cuando pages está vacío, porque las páginas explícitas siempre ganan sobre el preset.",
    ),
    "notes_pattern": (
        "patrón de notas",
        "Patrón de las páginas de notas.",
        "Rayado impreso en las páginas de notas: lined, dotted, grid o blank. También se aplica "
        "a las páginas de notas añadidas como relleno del cuadernillo.",
    ),
    "page_numbers": (
        "números de página",
        "Imprimir números de página.",
        "Activado: se imprime un número en cada página. Desactivado: las páginas no llevan "
        "número. El inicio, la primera página, la posición, la ubicación y el formato lo "
        "ajustan (page_number_start, page_number_first, page_number_position, "
        "page_number_placement, page_number_format).",
    ),
    "page_number_start": (
        "número inicial",
        "Número impreso en la primera página numerada.",
        "Número impreso en la primera página numerada (0-9999, por defecto 1). Solo se usa "
        "cuando page_numbers está activado.",
    ),
    "page_number_first": (
        "primera página numerada",
        "Página del plan que recibe el primer número.",
        "Página del plan (desde 1) que recibe el primer número (por defecto 1). Las páginas "
        "anteriores no se numeran, p. ej. 3 omite la portada y la guarda. Solo se usa cuando "
        "page_numbers está activado.",
    ),
    "page_number_position": (
        "posición del número",
        "Dónde va el número: outer, center o inner.",
        "Posición horizontal: outer (lejos del encuadernado, por defecto), center o inner (junto "
        "al encuadernado). Solo se usa cuando page_numbers está activado.",
    ),
    "page_number_placement": (
        "ubicación del número",
        "Número en el margen inferior o en el pie de página.",
        "margin (por defecto) imprime el número en el margen inferior bajo el contenido de la "
        "página; footer lo imprime dentro de la banda del pie de página. Solo se usa cuando "
        "page_numbers está activado.",
    ),
    "page_number_format": (
        "formato del número",
        "Texto de la etiqueta; {n} es el número y {total} el último.",
        "Texto de la etiqueta, de 1 a 24 caracteres. {n} es el número de página (obligatorio) y "
        "{total} el último número, p. ej. '{n} / {total}'. Solo se usa cuando page_numbers está "
        "activado.",
    ),
    "qr_urls": (
        "textos o URL de QR",
        "Textos o URL para la página QR, uno por línea.",
        "Textos o URL para la página qr, un código QR por cada uno, escritos uno por línea. "
        "Máximo 24 entradas de hasta 200 caracteres, y no se permiten líneas vacías.",
    ),
    "daily_hour_start": (
        "hora inicial diaria",
        "Primera hora impresa en las páginas diarias (0-23).",
        "Primera hora del horario por horas en las páginas diarias, 0-23 (por defecto 6, se "
        "muestra como 06:00). Debe ser menor que daily_hour_end. La página muestra menos horas "
        "si no caben.",
    ),
    "daily_hour_end": (
        "hora final diaria",
        "Última hora impresa en las páginas diarias (0-23).",
        "Última hora del horario por horas en las páginas diarias, 0-23 (por defecto 21, se "
        "muestra como 21:00). Debe ser mayor que daily_hour_start. La página muestra menos horas "
        "si no caben.",
    ),
    "weekly_filler": (
        "relleno semanal",
        "Qué llena la página antes de una semana abierta: blank, none o una página.",
        "Las dobles páginas de semana empiezan en una página izquierda, así que se añade una "
        "página de relleno antes de una doble que empezaría en una página derecha. blank (por "
        "defecto) la deja vacía; none no añade relleno, por lo que esa doble empieza en una "
        "página derecha y se reparte en dos hojas; el id de una página del catálogo de una sola "
        "página (p. ej. notes o todo) imprime esa página en el hueco. Se usa cuando el hueco no "
        "sigue a una página diaria.",
    ),
    "daily_filler": (
        "relleno diario",
        "Qué llena la página tras las páginas diarias de una semana: blank, none o una página.",
        "Igual que weekly_filler, para el hueco que sigue a la última página diaria de una "
        "semana (antes de la siguiente doble de semana). blank (por defecto), none o el id de "
        "una página del catálogo de una sola página como notes. Con ambos planificadores "
        "activados, la mayoría de los rellenos van en este hueco.",
    ),
    "month_start_pages": (
        "páginas de inicio de mes",
        "Páginas por mes impresas justo después de cada página mensual.",
        "Páginas por mes (budget, habits, monthly_review, health, quotes) impresas justo después "
        "de cada página mensual, con la fecha de ese mes. Una página listada aquí no se imprime "
        "de nuevo tras el planificador y no puede estar también en month_end_pages.",
    ),
    "month_end_pages": (
        "páginas de fin de mes",
        "Páginas por mes impresas tras la última semana de cada mes.",
        "Páginas por mes impresas tras la última semana de cada mes, con la fecha de ese mes. "
        "Una semana pertenece al mes en que empieza, así que la página puede seguir a uno o dos "
        "días del mes siguiente. Una página listada aquí no se imprime de nuevo tras el "
        "planificador.",
    ),
    "schedule_first_hour": (
        "primera hora del horario",
        "Primera hora del horario semanal (0-23).",
        "Hora de la primera fila de la página de horario semanal, 0-23 (por defecto 7). Debe ser "
        "menor que schedule_last_hour. La página muestra menos filas si no caben.",
    ),
    "schedule_last_hour": (
        "última hora del horario",
        "Última hora del horario semanal (0-23).",
        "Hora de la última fila de la página de horario semanal, 0-23 (por defecto 21), lo que "
        "limita el número de horas. Debe ser mayor que schedule_first_hour. La página muestra "
        "menos filas si no caben.",
    ),
    "habits_max": (
        "máximo de hábitos",
        "Máximo de filas de hábitos por mes (1-40).",
        "Número máximo de filas de hábitos en cada página mensual de seguimiento de hábitos, "
        "1-40 (por defecto 20). La página muestra menos filas si no caben.",
    ),
    "niche_entrepreneur_pages": (
        "páginas del pack Emprendedor",
        "Número de páginas del pack Emprendedor (1-20).",
        "Cuántas copias de la página del pack Emprendedor se imprimen, 1-20 (por defecto 1). "
        "Solo se aplica cuando niche_entrepreneur está en pages.",
    ),
    "niche_student_pages": (
        "páginas del pack Estudiante",
        "Número de páginas del pack Estudiante (1-20).",
        "Cuántas copias de la página del pack Estudiante se imprimen, 1-20 (por defecto 1). "
        "Solo se aplica cuando niche_student está en pages.",
    ),
    "niche_fitness_pages": (
        "páginas del pack Fitness",
        "Número de páginas del pack Fitness (1-20).",
        "Cuántas copias de la página del pack Fitness se imprimen, 1-20 (por defecto 1). Solo "
        "se aplica cuando niche_fitness está en pages.",
    ),
    "notes_pages": (
        "páginas de notas",
        "Número de páginas de Notas al final (0-50).",
        "Cuántas páginas de Notas se imprimen al final del libro, 0-50 (por defecto 1). 0 las "
        "elimina. El relleno hecho con pad_with=notes es aparte y se define con extra_padding.",
    ),
    "contacts_pages": (
        "páginas de contactos",
        "Número de páginas de Contactos al final (0-50).",
        "Cuántas páginas de Contactos se imprimen al final del libro, 0-50 (por defecto 1). 0 "
        "las elimina y la sección Contactos queda desactivada.",
    ),
    "extra_padding": (
        "relleno extra",
        "Número mínimo de páginas de relleno a añadir (0-200).",
        "Número mínimo de unidades de relleno (copias de la página pad_with, o páginas en "
        "blanco) puestas antes de la contraportada, 0-200 (por defecto 0). La agenda puede "
        "recibir más relleno del pedido, para completar el último cuadernillo y que los "
        "cuadernillos queden enteros.",
    ),
    "daily_holidays": (
        "feriados diarios",
        "Imprimir el nombre del feriado en las páginas diarias.",
        "Activado (por defecto): las páginas diarias imprimen el nombre del feriado del día en "
        "el encabezado, antes del número de semana. Usa los mismos feriados que las páginas de "
        "calendario, incluidos los de holidays_file.",
    ),
    "daily_quotes": (
        "frases diarias",
        "Imprimir una frase rotativa en las páginas diarias.",
        "Activado: el pie de cada página diaria muestra una frase inspiradora. Las frases rotan: "
        "una por día del año, recorriendo la lista. Desactivado por defecto.",
    ),
    "daily_quotes_file": (
        "archivo de frases",
        "Archivo de texto con una frase por línea.",
        "Archivo de texto opcional con una frase por línea (UTF-8; se ignoran las líneas en "
        "blanco y las que empiezan con #). Las frases rotan, una por día del año, de forma "
        "cíclica. Vacío significa las frases incluidas del idioma elegido. Solo se usa con "
        "daily_quotes.",
    ),
    "daily_extra_file": (
        "archivo de notas con fecha",
        "Archivo de notas con fecha mostradas en las páginas diarias.",
        "Archivo de texto opcional con una entrada con fecha por línea, como 'MM-DD texto' (cada "
        "año) o 'YYYY-MM-DD texto' (solo ese año); las líneas que empiezan con # son "
        "comentarios. El texto se muestra en el pie de la página diaria correspondiente. Varias "
        "entradas en una misma fecha se unen.",
    ),
    "year": (
        "año",
        "Año del calendario de la agenda.",
        "Año del calendario (1900-2200). Define todas las fechas, días de la semana y feriados "
        "en las páginas mensuales, semanales y diarias.",
    ),
    "week_start": (
        "inicio de semana",
        "Primer día de la semana.",
        "Primer día de la semana, monday o sunday. Cambia el orden de las columnas de las "
        "cuadrículas mensuales y dónde empieza cada página semanal.",
    ),
    "language": (
        "idioma",
        "Idioma de los textos impresos.",
        "Idioma de los nombres de meses, días de la semana y demás textos impresos: es (español) "
        "o en (inglés).",
    ),
    "holiday_country": (
        "país de feriados",
        "Código de país usado para los feriados, p. ej. CR.",
        "Código de país ISO, por ejemplo CR, cuyos feriados oficiales se marcan en las páginas "
        "de calendario. Se convierte a mayúsculas.",
    ),
    "holidays_file": (
        "archivo de feriados",
        "Archivo de feriados extra, combinado con la biblioteca.",
        "Archivo de texto opcional con sus propios feriados, uno por línea como 'MM-DD nombre' "
        "(cada año) o 'YYYY-MM-DD nombre' (solo ese año); las líneas que empiezan con # son "
        "comentarios. Se combinan con los feriados del país y se muestran igual en todas las "
        "páginas.",
    ),
    "theme": (
        "tema",
        "Paleta de colores del PDF.",
        "Nombre de la paleta de colores del PDF: minimal (por defecto), mono, ocean, forest, "
        "blush, lavender o peony. "
        "Un nombre desconocido se muestra como minimal (la línea de comandos avisa).",
    ),
    "color_ink": (
        "color de tinta",
        "Color del texto principal del PDF (vacío = tema).",
        "Color del texto principal del PDF, usado en títulos, números de día y texto del cuerpo. "
        + _HEX,
    ),
    "color_muted": (
        "color atenuado",
        "Color del texto secundario del PDF (vacío = tema).",
        "Color del texto secundario del PDF, usado en etiquetas, leyendas, números de semana y "
        "números de página. " + _HEX,
    ),
    "color_line": (
        "color de línea",
        "Color de las líneas del PDF (vacío = tema).",
        "Color de las líneas del PDF, usado en reglas, líneas de cuadrícula y puntos. " + _HEX,
    ),
    "color_accent": (
        "color de acento",
        "Color de acento del PDF (vacío = tema).",
        "Color de acento del PDF, usado en títulos de mes, marcas de feriados y resaltados. "
        + _HEX,
    ),
    "color_tint": (
        "color de tinte",
        "Color de tinte claro del PDF (vacío = tema).",
        "Color de tinte claro del PDF, usado en bandas de encabezado y fondos suaves. " + _HEX,
    ),
    "color_weekend_fill": (
        "relleno de fin de semana",
        "Relleno de las celdas de fin de semana del PDF (vacío = tema).",
        "Relleno de las celdas de fin de semana del PDF, usado como fondo de los días de fin de "
        "semana en los calendarios. " + _HEX,
    ),
    "color_holiday_fill": (
        "relleno de feriado",
        "Relleno de las celdas de feriado del PDF (vacío = tema).",
        "Relleno de las celdas de feriado del PDF, usado como fondo de los días feriados en los "
        "calendarios. " + _HEX,
    ),
    "font_primary": (
        "fuente principal",
        "Fuente de encabezados, títulos y texto en negrita.",
        'Fuente para encabezados, títulos y todo texto en negrita: la incluida "inter" o la '
        "ruta de un archivo .ttf/.otf. Las variantes negrita/cursiva se buscan junto al archivo "
        "(MyFont-Regular.ttf -> MyFont-Bold.ttf); los estilos que falten usan el archivo "
        "regular. La fuente debe contener los caracteres del idioma de la agenda.",
    ),
    "font_secondary": (
        "fuente secundaria",
        "Fuente del texto del cuerpo, etiquetas y números.",
        "Fuente para el texto del cuerpo, etiquetas, números y texto en cursiva: la incluida "
        '"inter" o la ruta de un archivo .ttf/.otf. Las variantes negrita/cursiva se buscan '
        "junto al archivo (MyFont-Regular.ttf -> MyFont-Italic.ttf); los estilos que falten "
        "usan el archivo regular. La fuente debe contener los caracteres del idioma de la "
        "agenda.",
    ),
    "title_padding": (
        "margen lateral de títulos",
        "Margen lateral de los fondos de título, en mm.",
        "Ancho extra, en mm, añadido a ambos lados de un fondo de título (el relleno de fin de "
        "semana o feriado detrás del encabezado de una página de día o de la fila de un día en "
        "la página semanal). El texto sigue alineado con el resto de la página; solo el relleno "
        "crece hacia afuera. 0 deja el relleno al ras del texto.",
    ),
    "imposition": (
        "imposición",
        "Exportar en orden de impresión de cuadernillo.",
        "Exporta las páginas en orden de impresión de cuadernillo, para poder plegar las hojas "
        "impresas en un cuadernillo. Requiere booklet_folded activado y no se puede combinar "
        "con spreads.",
    ),
    "crop_marks": (
        "marcas de corte",
        "Dibujar marcas de corte en las hojas con imposición o dobles páginas.",
        "Dibuja marcas de corte en las hojas para indicar dónde cortar. Requiere imposition o "
        "spreads activados, y el ajuste bleed controla la separación antes de cada marca.",
    ),
    "spreads": (
        "dobles páginas",
        "Exportar como dobles páginas de lectura (2 por hoja).",
        "Exporta las páginas de dos en dos por hoja horizontal en orden de lectura (la página 1 "
        "sola a la derecha, luego las páginas izquierda y derecha juntas), para leer o imprimir "
        "como dobles páginas. No se puede combinar con imposition. Las marcas de corte y "
        "sheet_size se aplican.",
    ),
    "sheet_size": (
        "tamaño de hoja",
        "Tamaño de hoja para dobles páginas e imposición.",
        "Hoja horizontal usada por spreads e imposition: auto elige letter o A4, la que escale "
        "más grandes las páginas; letter o a4 la fuerzan. Se ignora en páginas sueltas.",
    ),
    "output": (
        "salida",
        "Ruta del PDF exportado.",
        "Ruta del archivo PDF exportado. El archivo se escribe ahí al usar Exportar y se "
        "sobrescribe si existe.",
    ),
    "debug_grid": (
        "cuadrícula de depuración",
        "Superponer márgenes, columnas y línea base.",
        "Superpone los márgenes, las columnas y la cuadrícula de línea base en cada página. "
        "Úselo para revisar el diseño y desactívelo para la impresión final.",
    ),
}

SECTIONS: dict[str, str] = {
    "global": "Global",
    "padding": "Relleno",
    "month_start": "Inicio de cada mes",
    "daily": "Páginas diarias",
    "weekly": "Páginas semanales",
    "month_end": "Fin de cada mes",
    "notes": "Notas",
    "contacts": "Contactos",
    "budget": "Presupuesto mensual",
    "goals": "Metas del año",
    "habits": "Seguimiento de hábitos",
    "holidays": "Feriados",
    "important_dates": "Fechas importantes",
    "monthly_review": "Revisión mensual",
    "passwords": "Contraseñas",
    "projects": "Planificador de proyectos",
    "schedule": "Horario semanal",
    "todo": "Lista de tareas",
    "niche_entrepreneur": "Pack Emprendedor",
    "niche_fitness": "Pack Fitness",
    "niche_student": "Pack Estudiante",
    "physical_extras": "Guía de extras físicos",
    "qr": "Códigos QR",
    "challenges30": "Retos de 30 días",
    "gratitude": "Diario de gratitud",
    "health": "Seguimiento de salud",
    "meals": "Planificador de comidas y compras",
    "travel": "Planificador de viajes",
    "vision_board": "Tablero de visión",
    "ideas": "Mapa de ideas",
    "media_log": "Libros, películas y series",
    "quotes": "Frases mensuales",
    "styling": "Colores y fuentes del PDF",
}

GROUPS: dict[str, str] = {
    "general": "General",
    "planner": "Páginas de planificador",
    "optional": "Páginas opcionales",
    "value_added": "Páginas de valor añadido",
}

MESSAGES: dict[str, str] = {}
for _name, (_label, _short, _detail) in FIELDS.items():
    MESSAGES[f"field.{_name}.label"] = _label
    MESSAGES[f"field.{_name}.short"] = _short
    MESSAGES[f"field.{_name}.detail"] = _detail
MESSAGES.update({f"section.{k}": v for k, v in SECTIONS.items()})
MESSAGES.update({f"group.{k}": v for k, v in GROUPS.items()})
