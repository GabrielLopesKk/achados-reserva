"""Descrição de objetos a partir da foto.

Usa a API da Anthropic quando ANTHROPIC_API_KEY existe; senão cai num analisador
local simples (cor dominante). O resultado é sempre uma SUGESTÃO para revisão humana.
"""
import base64
import io
import json
import re

import requests
from PIL import Image

from .catalog import COLORS, ITEM_TYPES, SENSITIVE_TYPES

PALETTE = {
    "preto": (20, 20, 20), "branco": (240, 240, 240), "cinza": (128, 128, 128),
    "azul": (30, 70, 190), "vermelho": (200, 30, 40), "verde": (40, 150, 70),
    "amarelo": (240, 210, 40), "laranja": (240, 140, 30), "roxo": (120, 50, 160),
    "rosa": (240, 130, 180), "marrom": (110, 70, 40), "bege": (215, 195, 160),
}

PROMPT = (
    "Você ajuda um sistema de achados e perdidos de uma escola. Analise a foto e responda "
    "SOMENTE com um JSON: {\"type\": um de %s, \"color\": uma de %s, "
    "\"marks\": lista curta de marcas/adesivos/riscos visíveis, "
    "\"description\": uma frase simples em português, \"sensitive\": true se a foto mostrar "
    "documento, crachá, cartão, rosto ou dado pessoal}. Não identifique pessoas e não "
    "transcreva números ou nomes de documentos."
) % (ITEM_TYPES, COLORS)


def _nearest_color(rgb):
    return min(PALETTE, key=lambda n: sum((a - b) ** 2 for a, b in zip(PALETTE[n], rgb)))


def local_describe(data: bytes) -> dict:
    img = Image.open(io.BytesIO(data)).convert("RGB").resize((16, 16))
    px = [img.getpixel((x, y)) for x in range(4, 12) for y in range(4, 12)]
    avg = tuple(sum(p[i] for p in px) // len(px) for i in range(3))
    color = _nearest_color(avg)
    return {
        "type": "outro", "color": color, "marks": [],
        "description": f"Objeto de cor predominante {color}. Complete o tipo e os detalhes.",
        "sensitive": False,
    }


def _normalize(raw: dict) -> dict:
    kind = raw.get("type") if raw.get("type") in ITEM_TYPES else "outro"
    color = raw.get("color") if raw.get("color") in COLORS else "outra"
    marks = raw.get("marks") or []
    if isinstance(marks, str):
        marks = [marks]
    marks = [str(m).strip()[:60] for m in marks if str(m).strip()][:6]
    return {
        "type": kind, "color": color, "marks": marks,
        "description": str(raw.get("description", ""))[:500],
        "sensitive": bool(raw.get("sensitive")) or kind in SENSITIVE_TYPES,
    }


def _anthropic_describe(data: bytes, media_type: str, api_key: str, model: str) -> dict:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model, "max_tokens": 400, "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                         "data": base64.b64encode(data).decode()}},
            {"type": "text", "text": PROMPT}]}]},
        timeout=30,
    )
    resp.raise_for_status()
    text = "".join(b.get("text", "") for b in resp.json().get("content", []))
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group(0))


def describe(data: bytes, media_type: str, config) -> dict:
    """Retorna sugestão normalizada + origem ('anthropic' ou 'local')."""
    key = config.get("ANTHROPIC_API_KEY")
    if key:
        try:
            raw = _anthropic_describe(data, media_type, key, config["ANTHROPIC_MODEL"])
            return {**_normalize(raw), "source": "anthropic", "needs_review": True}
        except (requests.RequestException, ValueError, KeyError):
            pass  # cai no analisador local; o usuário continua podendo preencher
    return {**_normalize(local_describe(data)), "source": "local", "needs_review": True}
