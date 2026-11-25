# Selectable cm-pixel animations — ODD feature
Status: named animation selector implemented and installed; the user playlist is unchanged and has no named effect selected. Physical appearance of a selected effect has not been assessed.
Repository root: `/home/gmusa/cm-pixel`; branch: `feat/animation-selector`.

## Specs

- S1 — “cuando pongo que el widget es animation ,  como le digo que animacion ?
name = "animation"”
- S2 — “las opciones que soporta cm-pixel son ,

animations: plasma, rainbow, swirl, ripple, breathe, sparkle, fire, starfield, tunnel, metaballs, matrix, fireworks, aurora, comet, pinwheel, bounce, interference, twinkle, rubik”
- S3 — “Sí, agregá selector”

## Tasks

- T1 [S1–S3] — Add a validated per-animation-widget TOML selector backed by cm-pixel's named animations, preserving existing entries that omit it; cover the changed public preview/live path and document configuration; route: scoped worker under context backstop with parent correction; commit: `ccf855a`.
- T2 [S1–S3] — Verify the packaged selector and update only the user service's package while preserving the current user TOML, generated palette and sole HID ownership; route: parent; deployed source commit: `ccf855a`.

## Log

- L1 — Original user question (verbatim):

> cuando pongo que el widget es animation ,  como le digo que animacion ?
> name = "animation"

- L2 — User-supplied cm-pixel choices (verbatim):

> las opciones que soporta cm-pixel son ,
>
> animations: plasma, rainbow, swirl, ripple, breathe, sparkle, fire, starfield, tunnel, metaballs, matrix, fireworks, aurora, comet, pinwheel, bounce, interference, twinkle, rubik

- L3 — User selected the offered implementation action (verbatim):

> Sí, agregá selector

  This selects `name = "animation"` plus an animation selector backed by cm-pixel's named animations. Do not change the active user playlist to a particular animation: none was chosen. The prior dashboard's one moving-dot animation is existing behavior to preserve when the new selector is absent. The separate Noctalia accent correction is committed as `0cfb713` on the parent feature branch, generated output is active, and human color assessment remains open. Engram's Pi runtime contract is unavailable (`Expected engram.pi-http-runtime/v1`), so this local feature document is the confirmed continuity record; do not claim a persisted mirror.
- L4 — Read-only API map: installed `cm-pixel==0.1.0` exports `cmpixel.animations.ANIMATIONS` with the 19 user-named generator functions; each produces 32×32 RGB uint8 arrays. Generators are stateful and some use randomness. Preserve a generator instance for each active playlist entry across frames, reset on entry/playlist wrap/config reload, and run its RGB frames through the unchanged rotation, brightness and LED mask. The existing `name = "animation"` dot remains the default and uses Noctalia secondary; explicitly selected library effects keep their intrinsic colors (not all can be recolored consistently, notably rainbow). No global RNG seeding and no new animation names, speed knob or user TOML mutation are required. Reader-to-writer scope: config, animation plugin, preview/live dispatch, tests and README.
- L5 — The worker added strict validation for 19 selectors, stateful selected-effect playback and README syntax, with 51 tests passing after first trying the wrong runner (system Python lacked `cmpixel` on its path); those import errors were not valid RED evidence. The parent reproduced meaningful RED on pre-change source and new public behavior tests in a disposable base copy (3 selector/playback failures, exit 1), then GREEN with system Python plus the installed venv cm-pixel package on PYTHONPATH (52 passed, exit 0) after adding a public equal-config-hot-reload test and holding config/entry objects by identity to avoid recycled `id()` keys. A single exact differential against pre-change HEAD initially found `animation = "plasma"` on clock/date/cpu/gpu changed their previous CLI error from `unknown option`; this was corrected and pinned. Rerun matched exit/stdout/stderr for all four and pixels/stdout/stderr/exit of four-frame normal/locked previews. USB-free public preview produced two GIF frames for each of all 19 names at user-like rotation 90, brightness 50 and enabled mask; `/dev/hidraw5` owner was unchanged. `git diff --check` exit 0. `.venv` lacks pytest and an offline attempt to install it failed because the wheel was not cached; tests ran successfully via the host pytest with the venv dependency path. Pi-lens now reports no diagnostics on changed test files. Source not committed or deployed; independent verifier in flight.
- L6 — Independent read-only verifier inspected the full feature diff through Log, the installed cm-pixel generator contract, strict parser behavior, absent-selector fallback and preview/live lifecycle, with no output from its bundled `git diff --check` invocation and no concrete source blocker for S1–S3; the parent separately captured diff-check exit 0. It did not rerun tests and did not touch service/device; its verdict does not authorize declaring T2 deployed. Physical display animation remains unselected by the user.
- L7 — T1 committed locally as `ccf855a` (`feat(animation): select cm-pixel effects per widget`) after staged whitespace verification. The initial staged `git diff --check` exited 2 because the feature document had four quoted lines ending in literal spaces; the parent removed only those trailing whitespace bytes, reran the staged check with exit 0, and committed 252 additions/17 deletions across code, tests, README and this document. No push. T2 service package still uses old code until a separately verified offline upgrade.
- L8 — T2 deployed source `ccf855a` offline into `.venv` after validating a temporary package backup, stopping only `pixel-dashboard.service`, and checking `/dev/hidraw5` free. Installed CLI/config/live/animation source bytes match `ccf855a`, and the installed CLI rendered two named `plasma` preview frames without USB. The `cm-pixel` device patch hash, user TOML, generated Noctalia palette, and user service unit hashes were identical before/after. The service restarted enabled/active with `NRestarts=0`, new PID 2515287 and sole `/dev/hidraw5` ownership. Build artifacts and temporary backup removed after success. No animation name was selected in the user's existing TOML, so the physical appearance of a newly selected effect remains unverified and the previous moving-dot fallback remains the active behavior wherever such an entry is configured. No push.
