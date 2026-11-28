"""Schema helpers."""
import annotationlib


def describe(cls) -> dict[str, str]:
    return annotationlib.get_annotations(cls, format=annotationlib.Format.STRING)
