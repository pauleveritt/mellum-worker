"""Documentation helpers."""
import annotationlib


def return_text(func):
    return annotationlib.get_annotations(func, format=annotationlib.Format.STRING).get("return")
