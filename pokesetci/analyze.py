"""
Module for parsing and analyzing all pokeset files within a repository directory.
"""
import logging
import os
import warnings
from collections import defaultdict
from enum import Enum

import pokecat
import yaml
import yaml.scanner

logger = logging.getLogger(__name__)

ILLEGAL_CHARS = r"[\]^`|"


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    NOTE = "NOTE"


class Note:
    def __init__(self, severity: Severity, message, pokeset_identifier=None, filepath=None, position=None):
        self.severity = severity
        self.message = message
        self.pokeset_identifier = pokeset_identifier
        self.filepath = filepath
        self.position = position  # line offset in file, if known

    @property
    def ident(self):
        return "{}, {}".format(*self.pokeset_identifier) if self.pokeset_identifier else "unknown pokeset"

    def __str__(self):
        if self.filepath:
            return "[{}] [{} @ {}]: {}".format(self.severity.name, self.ident, self.filepath, self.message)
        else:
            return "[{}] [{}]: {}".format(self.severity.name, self.ident, self.message)

    def __repr__(self):
        return ("Note({!r}, {!r}, {!r}, {!r}, {!r})"
                .format(self.severity, self.message, self.pokeset_identifier, self.filepath, self.position))


def analyze_dir(root_dir):
    pokesets = []
    notes = []
    for dirname, _, filenames in os.walk(root_dir):
        for filename in filenames:
            filepath = os.path.join(root_dir, dirname, filename)
            relpath = os.path.relpath(filepath, root_dir)
            if not filename.endswith((".yaml", ".yml")) or filename.startswith("_"):
                continue
            with open(filepath, encoding="utf-8") as file_obj:
                its_notes, its_pokesets = analyze_file(file_obj)
                for note in its_notes:
                    note.filepath = relpath
                notes += its_notes
                pokesets += its_pokesets
    its_notes, pokesets = analyze_all_pokesets_integrity(pokesets)
    notes += its_notes
    return notes, pokesets


def analyze_file(file_obj):
    pokesets = []
    notes = []
    try:
        raw_pokesets = list(yaml.load_all(file_obj))
    except yaml.MarkedYAMLError as e:
        notes.append(Note(
            Severity.ERROR,
            str(e),
            position=e.problem_mark.line,
        ))
    except yaml.YAMLError as e:
        notes.append(Note(
            Severity.ERROR,
            str(e),
        ))
    else:
        for raw_pokeset in raw_pokesets:
            if not raw_pokeset:
                logger.info("Skipping empty pokeset in {}".format(file_obj.name))
                continue
            its_notes, pokeset = analyze_pokeset(raw_pokeset)
            notes += its_notes
            if pokeset:
                pokesets.append(pokeset)
    return notes, pokesets


def analyze_pokeset(pokeset):
    notes = []
    identifier = (pokeset.get("species"), pokeset.get("setname"))
    if "ingamename" in pokeset:
        fixed_ingamename = pokeset["ingamename"].encode("ascii", "replace").decode()
        for char in ILLEGAL_CHARS:
            fixed_ingamename = fixed_ingamename.replace(char, "?")
        if pokeset["ingamename"] != fixed_ingamename:
            notes.append(Note(
                Severity.NOTE,
                "Changed ingamename to {} as a temporary fix to avoid encoding issues".format(fixed_ingamename),
                identifier
            ))
            pokeset["ingamename"] = fixed_ingamename
    with warnings.catch_warnings(record=True) as w:
        try:
            pokeset = pokecat.populate_pokeset(pokeset, skip_ev_check=True)
        except ValueError as ex:
            notes.append(Note(
                Severity.ERROR,
                str(ex),  # TODO
                identifier
            ))
        else:
            for warning in w:
                warning_message = str(warning.message)
                if ("(wasted points)" in warning_message
                    or "Sum of EV must not be larger than 510" in warning_message
                    or "didn't recognize ball poke" in warning_message.lower()):  # TODO
                    severity = Severity.NOTE
                else:
                    severity = Severity.WARNING
                notes.append(Note(
                    severity,
                    warning_message,
                    identifier
                ))
            return notes, pokeset
    return notes, None


def analyze_all_pokesets_integrity(original_pokesets):
    notes = []
    pokesets = []
    genders_per_species = defaultdict(set)
    existing_ids = {}
    for pokeset in original_pokesets:
        identifier = (pokeset["species"]["id"], pokeset["setname"])
        genders_this_species = genders_per_species[pokeset["species"]["id"]]
        genders_this_species |= set(pokeset["gender"])
        if None in genders_this_species and len(genders_this_species) > 1:
            notes.append(Note(
                Severity.ERROR,
                ("Starting with this set, that species now has both genderless and gendered sets! "
                 "Stick to either genderless or gendered per species or PBR might crash!"),
                identifier
            ))
        if identifier in existing_ids:
            prev_identifier = existing_ids[id]
            notes.append(Note(
                Severity.ERROR,
                ("combination of species {} ({}) and setname {} already exists ({}), but must be unique!"
                 .format(identifier[0], pokeset["species"]["name"], identifier[1], prev_identifier)),
                identifier
            ))
        else:
            existing_ids[id] = identifier
            pokesets.append(pokeset)
    return notes, pokesets
