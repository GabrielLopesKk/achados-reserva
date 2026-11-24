"""Cruzamento entre relatos de perda e itens encontrados (sugestões, nunca decisão final)."""
import re
import unicodedata

STOPWORDS = {
    "de", "da", "do", "das", "dos", "com", "uma", "um", "para", "que", "por", "na", "no",
    "em", "e", "a", "o", "as", "os", "meu", "minha", "perdi", "acho", "ela", "ele",
}

MIN_SCORE = 0.35


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", normalize(text)) if len(t) > 2 and t not in STOPWORDS}


def score(report: dict, item: dict):
    """Retorna (pontuação 0-1, motivos legíveis)."""
    total, reasons = 0.0, []
    if report["item_type"] == item["item_type"] and item["item_type"] != "outro":
        total += 0.35
        reasons.append("mesmo tipo")
    if report["color"] == item["color"] and item["color"] != "outra":
        total += 0.20
        reasons.append("mesma cor")
    if report["location"] == item["location"]:
        total += 0.15
        reasons.append("mesmo local")
    a = tokens(report["description"])
    b = tokens(f"{item['description']} {item['marks']}")
    if a and b:
        overlap = len(a & b) / len(a | b)
        if overlap:
            total += min(0.30, overlap * 0.6)
            reasons.append("palavras em comum")
    if item["found_date"] < report["lost_date"]:
        total *= 0.5  # item achado antes da perda é pouco provável
    return round(min(total, 1.0), 2), reasons


def rank(report: dict, items: list, limit: int = 5) -> list:
    ranked = []
    for item in items:
        s, reasons = score(report, item)
        if s >= MIN_SCORE:
            ranked.append({"item": item, "score": s, "reasons": reasons})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:limit]
