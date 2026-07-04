# LSQ Style-Zone Fit Report

- free parameters: 16 style-zone control points (outlines, crown, swing; x ≥ 0.7 of stick — fit zone frozen)
- residual samples: 194 (top-view both directions + masked side view)
- loss: soft_l1, f_scale 2 mm; side-view weight 0.4, fitted datum offset 19.9 mm (bounds (4.0, 20.0)), mask (0.62, 0.9) of shoe length; tip beyond 0.965 of stick excluded

| Metric | Before | After |
|---|---|---|
| RMS gap (mm) | 9.89 | 3.05 |
| Worst gap (mm) | 14.07 | 10.07 |
| Cost | 9479.2 | 1070.4 |

Post-fit girth/floor validation: see TEMPLATE_REPORT.md (rebuild).

Changed control points:
- outline_y_medial[x=0.72]: -46.3 → -38.8
- outline_y_medial[x=0.8]: -44.5 → -37.2
- outline_y_medial[x=0.86]: -41.0 → -32.2
- outline_y_medial[x=0.9]: -37.5 → -28.9
- outline_y_medial[x=0.95]: -30.0 → -21.3
- outline_y_medial[x=0.98]: -19.0 → -28.5
- outline_y_lateral[x=0.74]: 49.0 → 39.6
- outline_y_lateral[x=0.82]: 45.0 → 35.0
- outline_y_lateral[x=0.88]: 40.0 → 29.5
- outline_y_lateral[x=0.93]: 33.0 → 23.2
- outline_y_lateral[x=0.97]: 22.0 → 14.2
- top_profile_z[x=0.72]: 33.0 → 44.6
- top_profile_z[x=0.8]: 27.5 → 39.1
- top_profile_z[x=0.88]: 24.0 → 35.5
- centerline_shift_y[x=0.75]: -2.5 → -0.6
- centerline_shift_y[x=0.9]: -4.0 → -1.1
