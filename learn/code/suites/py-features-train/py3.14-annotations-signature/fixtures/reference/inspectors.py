"""Introspection helpers."""
import annotationlib


def param_types(func) -> dict[str, str]:
    return annotationlib.get_annotations(func, format=annotationlib.Format.STRING)
