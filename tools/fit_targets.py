"""Stage 1: derive last fit targets from the design spec + data tables.

Pure table math (WORKFLOW Stage 1) — no geometry. Reads:
    designs/<slug>/spec/design_spec.json
    data/sizing/uk_men.json
    data/allowances/fit.json
Writes:
    designs/<slug>/last/fit_targets.json
    designs/<slug>/last/FIT_TARGETS.md

Usage: .venv/bin/python tools/fit_targets.py designs/<slug>
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(p):
    with open(p) as f:
        return json.load(f)


def interp_size(table: dict, size: float) -> dict:
    """Linear interpolation between integer sizes for half sizes."""
    lo, hi = int(size), int(size) if size == int(size) else int(size) + 1
    a, b = table[str(lo)], table[str(hi)]
    t = size - lo
    return {k: a[k] + t * (b[k] - a[k]) for k in a}


def fitting_offset(sizing: dict, fitting: str) -> float:
    """Ball-girth offset (mm) of `fitting` relative to standard F."""
    seq = sizing["width_fittings"]["sequence"]          # E F FX G H
    step = sizing["width_fittings"]["ball_girth_step_mm"]["default"]
    # FX is a half step above F; E/G/H are full steps around F (FX excluded from full-step count)
    full = [s for s in seq if s != "FX"]
    if fitting == "FX":
        return 0.5 * step
    return (full.index(fitting) - full.index("F")) * step


def derive(design_dir: Path) -> dict:
    spec = load(design_dir / "spec" / "design_spec.json")
    sizing = load(REPO / "data" / "sizing" / "uk_men.json")
    allow = load(REPO / "data" / "allowances" / "fit.json")

    size = spec["size"]["uk_size"]["value"]
    fitting = spec["size"]["width_fitting"]["value"]
    toe = spec["shoe"]["toe_character"]["value"]
    elongated = spec["shoe"]["toe_elongation"]["value"] == "elongated"
    sole_key = f'{spec["sole"]["spec"]["value"]}_{round(spec["sole"]["thickness_mm"]["value"])}mm'
    heel_mm = spec["heel"]["height_mm"]["value"]

    # --- foot reference (F fitting table + fitting offset on girths/widths)
    foot = interp_size(sizing["reference_foot"]["foot_table_f_fitting"], size)
    sec = sizing["reference_foot"]["secondary_estimates"]
    w_off = fitting_offset(sizing, fitting)
    tread_step = sizing["width_fittings"]["tread_width_step_mm"]["default"]
    n_steps = w_off / sizing["width_fittings"]["ball_girth_step_mm"]["default"]

    foot_ball = foot["ball_girth_mm"] + w_off
    foot_instep = foot_ball + sec["instep_girth_offset_from_ball_mm"]["default"]
    foot_waist = foot_ball + sec["waist_girth_offset_from_ball_mm"]["default"]
    foot_short_heel = foot_ball * sec["short_heel_girth_ratio_of_ball"]["default"]
    foot_heel_w = sec["heel_width_mm_at_uk9"]["default"] + \
        (size - 9) * sec["heel_width_grade_per_size_mm"]
    foot_tread_w = sec["tread_width_mm_at_uk9_f"]["default"] + \
        (size - 9) * sizing["girth_grades"]["tread_width_per_full_size_mm"] + \
        n_steps * tread_step

    # --- stick length: table is authority (WORKFLOW §S1.1)
    stick = sizing["length"]["stick_length_mm"][
        str(int(size)) if size == int(size) else str(size)]
    toe_allow = allow["toe_allowance_mm"][toe]["default"] + \
        (allow["toe_allowance_mm"]["elongated_extra"]["default"] if elongated else 0.0)
    effective_toe_allow = round(stick - foot["foot_length_mm"], 1)

    # --- foot -> last
    ga, wa = allow["girth_allowances_mm"], allow["width_allowances_mm"]
    last_ball = foot_ball + ga["ball"]["default"]
    last_instep = foot_instep + ga["instep"]["default"]
    last_waist = last_ball * (foot_waist / foot_ball)          # proportional mode
    last_short_heel = foot_short_heel + ga["short_heel"]["default"]
    last_seat_w = foot_heel_w + wa["seat_width"]["default"]
    last_tread_w = foot_tread_w + wa["tread_width"]["default"]

    st = sizing["stations"]
    tol = allow["tolerances_mm"]
    ball_x = st["ball_fraction"]["default"] * stick
    fit_zone_x_max = round(ball_x + 0.03 * stick, 1)           # "just beyond the ball line"
    toes_end_x = round(foot["foot_length_mm"], 1)              # toe tips of the reference foot

    r = lambda v: round(v, 1)
    return {
        "meta": {
            "design": spec["design"]["slug"], "units": "mm",
            "derived_from": ["spec/design_spec.json", "data/sizing/uk_men.json",
                             "data/allowances/fit.json"],
            "created": "2026-07-04",
            "estimate_flag": "instep/waist/short-heel/width foot values are grade-derived ESTIMATES pending calibration (see data/sizing/uk_men.json secondary_estimates)"
        },
        "input": {"uk_size": size, "width_fitting": fitting, "toe_character": toe,
                  "heel_height_mm": heel_mm, "sole": sole_key},
        "reference_foot": {
            "foot_length_mm": r(foot["foot_length_mm"]), "ball_girth_mm": r(foot_ball),
            "instep_girth_mm": r(foot_instep), "waist_girth_mm": r(foot_waist),
            "short_heel_girth_mm": r(foot_short_heel), "heel_width_mm": r(foot_heel_w),
            "tread_width_mm": r(foot_tread_w)
        },
        "targets": {
            "stick_length_mm": {"target": r(stick), "tol": tol["lengths"]},
            "ball_girth_mm": {"target": r(last_ball), "tol": tol["girths"],
                               "station_fraction": st["ball_fraction"]["default"]},
            "instep_girth_mm": {"target": r(last_instep), "tol": tol["girths"],
                                 "station_fraction": st["instep_fraction"]["default"]},
            "waist_girth_mm": {"target": r(last_waist), "tol": tol["girths"],
                                "station_fraction": st["waist_fraction"]["default"]},
            "short_heel_girth_mm": {"target": r(last_short_heel), "tol": tol["girths"]},
            "seat_width_mm": {"target": r(last_seat_w), "tol": tol["widths"],
                               "station_fraction": st["heel_width_fraction"]["default"]},
            "tread_width_mm": {"target": r(last_tread_w), "tol": tol["widths"],
                                "station_fraction": st["ball_fraction"]["default"]},
            "toe_spring_mm": {"target": allow["toe_spring_mm"]["by_sole"][sole_key]["default"],
                               "min": allow["toe_spring_mm"]["by_sole"][sole_key]["min"],
                               "max": allow["toe_spring_mm"]["by_sole"][sole_key]["max"]},
            "heel_height_mm": {"target": heel_mm, "tol": tol["lengths"]},
            "toe_box_min_height_mm": allow["toe_box_min_height_mm"]["default"]
        },
        "toe_allowance": {
            "nominal_mm": toe_allow,
            "effective_mm": effective_toe_allow,
            "note": "effective = barleycorn stick - reference foot length; see FIT_TARGETS.md open note"
        },
        "zones": {
            "ball_line_x_mm": r(ball_x),
            "fit_zone": {"x_mm": [0.0, fit_zone_x_max],
                          "rule": "hard tolerances; untouched by style operations (assert <0.2 mm displacement in Stage 2 style step)"},
            "toe_region": {"x_mm": [fit_zone_x_max, toes_end_x],
                            "rule": f"style shaping allowed but toe-box height >= {allow['toe_box_min_height_mm']['default']} mm above insole plane over the toes"},
            "style_zone": {"x_mm": [fit_zone_x_max, r(stick)],
                            "rule": "free aesthetic shaping forward of fit zone, subject to toe_region rule"}
        },
        "feather_edge": {"spec": "sharp hard crease on the DESIGN last (print copy may take a 0.4 mm micro-flat in Stage 3 only)"}
    }


def write_md(t: dict, path: Path):
    tg, rf = t["targets"], t["reference_foot"]
    rows = [
        ("Stick length", tg["stick_length_mm"], f"foot {rf['foot_length_mm']}"),
        ("Ball girth", tg["ball_girth_mm"], f"foot {rf['ball_girth_mm']}"),
        ("Instep girth", tg["instep_girth_mm"], f"foot {rf['instep_girth_mm']} (est.)"),
        ("Waist girth", tg["waist_girth_mm"], f"foot {rf['waist_girth_mm']} (est., proportional)"),
        ("Short heel girth", tg["short_heel_girth_mm"], f"foot {rf['short_heel_girth_mm']} (est.)"),
        ("Seat width", tg["seat_width_mm"], f"foot {rf['heel_width_mm']} (est.)"),
        ("Tread width", tg["tread_width_mm"], f"foot {rf['tread_width_mm']} (est.)"),
    ]
    lines = [
        f"# Fit Targets — {t['meta']['design']} (UK {t['input']['uk_size']} {t['input']['width_fitting']})",
        "",
        "| Measurement | Last target (mm) | Tol (±mm) | Station (x/stick) | Reference foot (mm) |",
        "|---|---|---|---|---|",
    ]
    for name, v, foot in rows:
        lines.append(f"| {name} | {v['target']} | {v['tol']} | "
                     f"{v.get('station_fraction', '—')} | {foot} |")
    lines += [
        f"| Toe spring | {tg['toe_spring_mm']['target']} | "
        f"{tg['toe_spring_mm']['min']}–{tg['toe_spring_mm']['max']} | — | sole-linked |",
        f"| Heel height | {tg['heel_height_mm']['target']} | {tg['heel_height_mm']['tol']} | — | from spec |",
        f"| Toe-box min height | ≥ {tg['toe_box_min_height_mm']} | hard floor | toe line | — |",
        "",
        f"**Zones:** fit-critical x ∈ [0, {t['zones']['fit_zone']['x_mm'][1]}] "
        f"(ball line at {t['zones']['ball_line_x_mm']}); toes end ≈ {t['zones']['toe_region']['x_mm'][1]}; "
        "style zone forward of the fit zone, toe-box height floor over the toes.",
        "",
        "**Open note (toe allowance):** nominal round-toe allowance is "
        f"{t['toe_allowance']['nominal_mm']} mm, but the barleycorn stick length minus the "
        f"reference foot length gives an effective {t['toe_allowance']['effective_mm']} mm. "
        "This tension is inherent in WORKFLOW's own anchor numbers (279.2 stick vs 265 foot at UK 8 ⇒ ~14 mm). "
        "The stick-length table is the authority of record, so the effective value stands; "
        "flagged for the one-time physical calibration run. Fit-critical heel-to-ball is unaffected.",
        "",
        "**Estimate flag:** instep / waist / short-heel girths and widths derive from "
        "grade-based estimates (`data/sizing/uk_men.json → secondary_estimates`) — "
        "no free authoritative per-size table exists (last_creation.md caveat). "
        "Calibrate once against a physical sample and update `data/`.",
        "",
    ]
    path.write_text("\n".join(lines))


if __name__ == "__main__":
    design_dir = REPO / sys.argv[1] if not Path(sys.argv[1]).is_absolute() \
        else Path(sys.argv[1])
    targets = derive(design_dir)
    out = design_dir / "last"
    out.mkdir(exist_ok=True)
    with open(out / "fit_targets.json", "w") as f:
        json.dump(targets, f, indent=2)
    write_md(targets, out / "FIT_TARGETS.md")
    print(json.dumps(targets["targets"], indent=2))
