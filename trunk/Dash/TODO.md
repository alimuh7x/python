
## Critical Fixes (Next)

- [ ] **Comparison “Full Scale” semantics**: define + implement the final meaning
  - Option A (current main-tab meaning): per-file dynamic scaling (each heatmap uses its own data min/max) → requires per-heatmap colorbars or no shared colorbar
  - Option B (your requested meaning): group-global min/max across selected heatmaps → keep shared colorbar + slider snaps to group min/max when enabled
- [ ] Fix comparison colorbar behavior to match the chosen Full Scale semantics (don’t hide it unexpectedly)
- [ ] Fix comparison “Full Scale” toggle wiring so slider/min/max reliably update when switch is toggled (no stale min/max)
- [ ] Confirm comparison range defaults are computed over **all selected files** and not “first file wins” (already patched, re-verify)

## UX / Layout

- [ ] Make comparison header row height compact (single-line) and never consume heatmap height
- [ ] Ensure titles sit above heatmaps (not beside), aligned with dynamic heatmap widths
- [ ] Ensure dropdowns never clip (done via CSS), then narrow the CSS to avoid unwanted side-effects elsewhere if needed
- [ ] Decide & implement how selected files are represented:
  - Current: no chips in dropdown + file name above each heatmap with “×”
  - Alternative: show chips in dropdown + also show above heatmaps
- [ ] Add “Clear group selection” button per comparison group (remove all selected files for that group)

## Data / Comparison Model

- [ ] Validate grouping rule for real datasets (prefix-before-underscore) for all file naming patterns used in the project
- [ ] Ensure comparison blocks only show for the active module (Phase Field / Composition / Mechanics / Plasticity)
- [ ] Add an explicit “Group” dropdown (optional) to compare non-matching prefixes on demand

## Performance (Dash/Plotly)

- [ ] Keep tab content mounted to avoid re-registering callbacks and losing state (already done; re-verify no remounts)
- [ ] Reduce callback churn:
  - Debounce numeric inputs (min/max) so typing doesn’t trigger heavy renders
  - Avoid updating heatmaps when only layout/style changes
- [ ] Improve caching:
  - Cap `comparison_grid_cache_data` size (LRU) to avoid memory growth
  - Cache per-file stats (min/max) to avoid repeated reads for range defaults
- [ ] Consider fast rendering paths:
  - Downsample/interpolate grids for display while preserving values for hover
  - Optional WebGL heatmap (`go.Heatmapgl`) if it improves performance for large grids

## Robustness / Debugging

- [ ] Add a “Diagnostics” toggle: show callback timing, cache hits/misses, current selection stores (for debugging)
- [ ] Reduce console errors/warnings (currently many): identify top offenders and fix the root causes
- [ ] Add guardrails for missing files / deleted files / invalid VTK files (better messages, no crashes)

## Code Health

- [x] Break `OPView.py` into modules (no behavior changes):
  - `comparison.py` (comparison builders + callbacks)
  - `tabs.py` (TAB_CONFIGS + tab rendering)
  - `ui_components.py` (small reusable layout blocks)
- [ ] Add type hints for the comparison store payloads and helper functions
- [ ] Add a small “How comparison works” section in `README.md`
