from typing import Any


def safe_dig(
    data: dict, keys: list[str], default: Any = None, error_on_missing: bool = False
) -> Any:
    """
    Safely dig into a dictionary.
    """
    keys_traversed = []
    for key in keys:
        keys_traversed.append(key)
        if key in data:
            data = data[key]
        elif error_on_missing:
            keys_traversed_str = ".".join(keys_traversed)
            raise ValueError(f"Key {keys_traversed_str} not found in data")
        else:
            return default
    return data
