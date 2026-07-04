"""Schema + validator for designs/<slug>/spec/design_spec.json (WORKFLOW Stage 0).

Every leaf setting is a "field" object:
    {"value": <x>, "source": "user" | "default" | "image", "assumed": <bool>}
so the human can see at the gate exactly which choices came from the brief and
which were filled in. Image-derived classifications additionally carry
"confidence" (0-1), per WORKFLOW Stage 0.2.

Usage:
    .venv/bin/python tools/spec_schema.py designs/<slug>/spec/design_spec.json
Exit code 0 = valid.
"""

import json
import sys

import jsonschema


def field(value_schema: dict, allow_image: bool = False) -> dict:
    sources = ["user", "default"] + (["image"] if allow_image else [])
    return {
        "type": "object",
        "properties": {
            "value": value_schema,
            "source": {"enum": sources},
            "assumed": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["value", "source", "assumed"],
        "additionalProperties": False,
    }


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "design": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
                "name": {"type": "string"},
                "created": {"type": "string", "format": "date"},
                "revision": {"type": "integer", "minimum": 1},
                "brief": {"type": "string"},
            },
            "required": ["slug", "name", "created", "revision", "brief"],
            "additionalProperties": False,
        },
        "size": {
            "type": "object",
            "properties": {
                "system": {"const": "uk_men"},
                "uk_size": field({"type": "number", "minimum": 5, "maximum": 13,
                                  "multipleOf": 0.5}),
                "width_fitting": field({"enum": ["E", "F", "FX", "G", "H"]}),
            },
            "required": ["system", "uk_size", "width_fitting"],
            "additionalProperties": False,
        },
        "shoe": {
            "type": "object",
            "properties": {
                "type": field({"enum": ["derby", "cap_toe_oxford",
                                        "brogued_derby", "brogued_oxford",
                                        "penny_loafer"]}),
                "style_template": field({"type": "string"}),
                "construction": field({"enum": ["gyw"]}),
                "toe_character": field({"enum": ["round", "almond",
                                                 "soft_chisel", "chisel",
                                                 "square"]}, allow_image=True),
                "toe_elongation": field({"enum": ["standard", "elongated"]},
                                        allow_image=True),
                "detailing": {
                    "type": "object",
                    "properties": {
                        "cap": field({"type": "boolean"}),
                        "brogue_scheme": field({"type": ["string", "null"]}),
                        "apron": field({"type": "boolean"}),
                    },
                    "required": ["cap", "brogue_scheme", "apron"],
                    "additionalProperties": False,
                },
            },
            "required": ["type", "style_template", "construction",
                         "toe_character", "toe_elongation", "detailing"],
            "additionalProperties": False,
        },
        "materials": {
            "type": "object",
            "properties": {
                "upper": field({"type": "string"}),
                "upper_thickness_mm": field({"type": "number", "minimum": 0.8,
                                             "maximum": 3.0}),
                "color": field({"type": "string"}),
                "lining": field({"type": "string"}),
                "edge_treatment": field({"type": "string"}),
            },
            "required": ["upper", "upper_thickness_mm", "color", "lining",
                         "edge_treatment"],
            "additionalProperties": False,
        },
        "heel": {
            "type": "object",
            "properties": {
                "height_mm": field({"type": "number", "minimum": 20,
                                    "maximum": 30}),
                "kind": field({"enum": ["stacked_leather"]}),
            },
            "required": ["height_mm", "kind"],
            "additionalProperties": False,
        },
        "sole": {
            "type": "object",
            "properties": {
                "spec": field({"enum": ["single_leather", "double_leather"]}),
                "thickness_mm": field({"type": "number", "minimum": 3,
                                       "maximum": 12}),
            },
            "required": ["spec", "thickness_mm"],
            "additionalProperties": False,
        },
        "inspiration_images": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "classification": {"type": "object"},
                },
                "required": ["path", "classification"],
            },
        },
    },
    "required": ["design", "size", "shoe", "materials", "heel", "sole",
                 "inspiration_images"],
    "additionalProperties": False,
}


def validate_spec(path: str) -> list[str]:
    """Return a list of human-readable problems; empty list = valid."""
    with open(path) as f:
        spec = json.load(f)
    validator = jsonschema.Draft202012Validator(SCHEMA)
    problems = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in validator.iter_errors(spec)
    ]
    # Semantic checks the schema can't express
    if not problems:
        if spec["shoe"]["type"]["value"] == "derby" and \
                spec["shoe"]["detailing"]["cap"]["value"]:
            problems.append("plain derby must not have a toe cap")
        for img in spec["inspiration_images"]:
            for k, v in img["classification"].items():
                if isinstance(v, dict) and v.get("source") == "image" \
                        and "confidence" not in v:
                    problems.append(f"image field {img['path']}:{k} lacks confidence")
    return problems


if __name__ == "__main__":
    errs = validate_spec(sys.argv[1])
    for e in errs:
        print(f"INVALID  {e}")
    print("OK" if not errs else f"{len(errs)} problem(s)")
    sys.exit(1 if errs else 0)
