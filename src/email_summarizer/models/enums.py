from enum import Enum


class EmailAccounts(Enum):
    PRIMARY = "PRIMARY"
    NOREPLY = "NOREPLY"
    ALTERNATE = "ALTERNATE"


class SupportedModel(Enum):
    CLAUDE_HAIKU = "CLAUDE_HAIKU"
    CLAUDE_SONNET = "CLAUDE_SONNET"
    NOVA_MICRO = "NOVA_MICRO"
    DEEPSEEK = "DEEPSEEK"
