"""Funções de privacidade: máscara de contato, hash de códigos."""
import hashlib
import hmac
import secrets


def mask_contact(contact: str) -> str:
    """Mostra o mínimo necessário para a recepção reconhecer o contato."""
    contact = contact.strip()
    if "@" in contact:
        user, _, domain = contact.partition("@")
        return f"{user[:1]}***@{domain}"
    digits = [c for c in contact if c.isdigit()]
    if len(digits) >= 4:
        return "••••-" + "".join(digits[-4:])
    return "•••"


def new_secret(nbytes: int = 3) -> str:
    """Código curto legível (retirada) ou token maior (relato)."""
    return secrets.token_hex(nbytes).upper()


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.strip().upper().encode("utf-8")).hexdigest()


def same_secret(value: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_secret(value), expected_hash)
