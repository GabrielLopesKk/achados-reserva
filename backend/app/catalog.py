"""Listas controladas usadas pelo formulário, pela IA e pela busca."""

ITEM_TYPES = [
    "garrafa", "carregador", "caderno", "jaqueta", "documento", "cartão", "chave",
    "fone de ouvido", "mochila", "guarda-chuva", "calculadora", "óculos", "outro",
]
COLORS = [
    "preto", "branco", "cinza", "azul", "vermelho", "verde", "amarelo", "laranja",
    "roxo", "rosa", "marrom", "bege", "outra",
]
LOCATIONS = [
    "Laboratório", "Sala de aula", "Pátio", "Recepção", "Biblioteca", "Cantina",
    "Estacionamento", "Entorno do campus",
]
STATUSES = ["found", "awaiting_pickup", "returned"]
SENSITIVE_TYPES = {"documento", "cartão"}
