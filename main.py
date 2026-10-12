"""Canonical source checkout entry point for Aiko Desktop Pet.

Run with `python main.py` from the repository root. Existing Windows launchers
and `python -m aiko_pet` continue to use the same application entry point.
"""

from aiko_pet.gui import main


if __name__ == "__main__":
    main()
