"""Онтологическая валидация сущностей и отношений + проверка цитат.

Сущность валидна, если её тип активен в профиле, есть name и source_quote,
а цитата реально содержится в тексте главы. Отношение валидно, если тип
существует, тройка domain→range допустима, confidence ≥ порога и цитата
присутствует в тексте. Источник правил — knowledge_graph_analytics.md §4.2.
"""
from app.config import settings
from app.ontology import Profile


def quote_in_text(quote: str | None, text: str) -> bool:
    """Нормализованная проверка вхождения цитаты в тексте.

    Сначала точное совпадение (нормализованные пробелы+регистр).
    Если не совпало — проверяем, что хотя бы 3 последовательных слова
    из цитаты встречаются подряд в тексте (LLM иногда слегка перефразирует).
    Для коротких цитат (< 4 слов) достаточно любого одного слова длиной ≥ 5.
    """
    if not quote:
        return False
    norm = lambda s: " ".join(s.lower().split())
    nq = norm(quote)[:200]
    nt = norm(text)
    if nq in nt:
        return True
    words = nq.split()
    if len(words) >= 3:
        for i in range(len(words) - 2):
            trigram = " ".join(words[i : i + 3])
            if trigram in nt:
                return True
    elif words:
        return any(w in nt for w in words if len(w) >= 5)
    return False


def validate_entities(
    raw: list[dict], profile: Profile, chapter_text: str
) -> list[dict]:
    active_types = {et.type_name: et for et in profile.active_entity_types()}
    valid: list[dict] = []
    for e in raw:
        etype = e.get("entity_type")
        name = (e.get("name") or "").strip()
        et = active_types.get(etype)
        if et is None:
            continue  # тип не активен в профиле
        if len(name) < 2 or len(name) > 100:
            continue
        if not quote_in_text(e.get("source_quote"), chapter_text):
            continue  # цитата-фантом
        # оставляем только атрибуты, предусмотренные схемой класса
        attrs = {
            k: v for k, v in (e.get("attrs") or {}).items() if k in et.attrs
        }
        valid.append(
            {
                "entity_type": etype,
                "name": name,
                "attrs": attrs,
                "source_quote": e["source_quote"],
            }
        )
    return valid


def validate_relations(
    entities: list[dict],
    relations: list[dict],
    profile: Profile,
    chapter_text: str,
) -> list[dict]:
    ontology = profile.active_relation_types()
    rel_by_name = {rt.type_name: rt for rt in ontology}
    # имя(lower) -> entity_type извлечённой сущности
    type_by_name = {e["name"].lower(): e["entity_type"] for e in entities}

    valid: list[dict] = []
    for r in relations:
        rt = rel_by_name.get(r.get("relation_type"))
        if rt is None:
            continue
        frm = (r.get("from") or "").lower()
        to = (r.get("to") or "").lower()
        src_type = type_by_name.get(frm)
        dst_type = type_by_name.get(to)
        if src_type is None or dst_type is None or frm == to:
            continue
        if src_type not in rt.domain_types or dst_type not in rt.range_types:
            continue
        if r.get("confidence", 0) < settings.confidence_threshold:
            continue
        if not quote_in_text(r.get("source_quote"), chapter_text):
            continue
        valid.append(r)
    return valid
