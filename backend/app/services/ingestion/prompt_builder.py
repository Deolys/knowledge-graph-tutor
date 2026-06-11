"""Динамическая сборка промптов извлечения из активной онтологии.

В промпт попадают ТОЛЬКО классы и отношения активного профиля книги — так
промпт остаётся компактным, а поведение меняется правкой YAML без правок кода.
"""
from app.ontology import Profile


def build_entity_extraction_prompt(profile: Profile) -> str:
    """Системный промпт извлечения сущностей из активной онтологии."""
    type_blocks = []
    for et in profile.active_entity_types():
        attrs = ", ".join(et.attrs)
        type_blocks.append(
            f"- {et.type_name} ({et.label}): {et.description}. "
            f"Атрибуты: {attrs}"
        )
    types_section = "\n".join(type_blocks)

    return f"""Ты — система извлечения знаний из учебных текстов.
Разложи содержимое главы по следующим типам сущностей:

{types_section}

ПРАВИЛА:
1. Извлекай ТОЛЬКО то, что явно присутствует в тексте
2. name: минимальная каноническая форма
3. source_quote: точная цитата из текста, где сущность вводится — ОБЯЗАТЕЛЬНА
4. Формулы — в LaTeX, в атрибут latex
5. Заполняй только атрибуты, предусмотренные типом
6. Если фрагмент не подходит ни под один тип — не извлекай его

ФОРМАТ — только валидный JSON:
{{
  "entities": [
    {{"entity_type": "...", "name": "...", "attrs": {{...}}, "source_quote": "..."}}
  ]
}}"""


def build_relation_extraction_prompt(profile: Profile) -> str:
    """Промпт извлечения отношений: только активные тройки domain → range."""
    rel_blocks = []
    for rt in profile.active_relation_types():
        domain = "|".join(rt.active_domain(profile))
        range_ = "|".join(rt.active_range(profile))
        rel_blocks.append(
            f"- {rt.type_name} ({rt.label}): {domain} → {range_}"
        )
    rels_section = "\n".join(rel_blocks)

    return f"""Ты — система построения графа знаний.
Найди связи между сущностями СТРОГО по схеме:

{rels_section}

ПРАВИЛА:
1. Используй только сущности из предоставленного списка (по точным name)
2. Связь должна соответствовать схеме: тип слева → тип справа
3. source_quote: точная цитата, подтверждающая связь — ОБЯЗАТЕЛЬНА
4. confidence от 0.0 до 1.0; сохраняются только ≥ 0.7
5. Не выводи связи из общих знаний — только из текста

ФОРМАТ — только валидный JSON:
{{
  "relations": [
    {{"from": "...", "to": "...", "relation_type": "...",
      "confidence": 0.85, "source_quote": "..."}}
  ]
}}"""


def entity_extraction_user(chapter_title: str, chapter_text: str) -> str:
    return f'Текст главы "{chapter_title}":\n\n{chapter_text}'


def relation_extraction_user(entities_json: str, chapter_text: str) -> str:
    return (
        f"Список сущностей из главы (entity_type, name):\n{entities_json}\n\n"
        f"Текст главы:\n{chapter_text}"
    )
