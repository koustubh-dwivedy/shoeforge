# LSQ Style-Zone Fit Report

- free parameters: 14 style-zone control points (outlines, crown, swing; x ≥ 0.7 of stick — fit zone frozen)
- residual samples: 363 (top-view both directions + masked side view)
- loss: soft_l1, f_scale 2 mm; WHOLE-PROFILE side fit, per-region fitted datum offsets: toe/vamp 25.8 mm (mask (0.6, 0.9), w 0.5), cone/laces 43.6 mm (mask (0.3, 0.6), w 0.35); tip beyond 0.965 of stick excluded; instep/waist/ball crowns frozen (fit zone)
- cone height scale (single DOF over rear crown): 0.850 (bounds (0.85, 1.15)); smoothness λ 0.08

| Metric | Before | After |
|---|---|---|
| RMS gap (mm) | 7.10 | 3.22 |
| Worst gap (mm) | 16.80 | 11.85 |
| Cost | 9148.4 | 1819.1 |

Post-fit girth/floor validation: see TEMPLATE_REPORT.md (rebuild).

Changed control points:
- outline_y_medial[x=0.72]: -43.0 → -44.8
- outline_y_medial[x=0.8]: -37.2 → -39.9
- outline_y_medial[x=0.86]: -32.2 → -33.7
- outline_y_medial[x=0.9]: -28.9 → -27.1
- outline_y_medial[x=0.95]: -21.3 → -18.4
- outline_y_lateral[x=0.74]: 43.5 → 42.4
- outline_y_lateral[x=0.82]: 35.0 → 33.7
- outline_y_lateral[x=0.88]: 29.5 → 27.3
- outline_y_lateral[x=0.93]: 23.2 → 20.8
- top_profile_z[x=0.72]: 37.5 → 40.5
- top_profile_z[x=0.8]: 39.1 → 38.7
- top_profile_z[x=0.88]: 35.5 → 35.3
- centerline_shift_y[x=0.75]: -0.6 → 0.5
- centerline_shift_y[x=0.9]: -1.1 → -0.9
