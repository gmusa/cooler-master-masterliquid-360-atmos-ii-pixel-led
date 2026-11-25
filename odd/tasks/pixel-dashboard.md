# Pixel LED dashboard — ODD scope and design
Status: first local milestone verified in L8; v1 continuation authorized by L9. Clone-local RDD disabled by L7; remote publication remains separate.
Repository root: `/home/gmusa/cm-pixel`; branch: `feat/pixel-dashboard`.

## Specs

- S1 — “info de sensores ( cpu , gpu ) temperatura, velocidad , una animacion del uso , reloj digital / analogico , fecha”
- S2 — “si la maquina esta loqueada que reprodusca una animacion ( podemos usar las del mismo cm-pixel, o estas de reloj que dije antes.”
- S3 — “ver si los sensores podemos hacerle algun detalle visual para que no sea solo texto.”
- S4 — “Uso noctalia v5 , estaria bueno respetar la paleta de colores activa de noctalia”
- S5 — “ver que corra siempre y que se vuelva a iniciar si se cae el servicio.”
- S6 — “la configuracion que tenga hot-reload y validacion ( noctalia suele mostrar un error en pantalla cuando hay error de config ) [yaml / toml ]”
- S7 — “Estaria bueno poder armar la secuencia de widgets de info que ciclan en entorno normal. y los que cliclan en entorno locked”
- S8 — “por cada widget estaria bueno poder definer su tiempo de ejecucion o uno general a nivel entorno ( locked / unlocked )”
- S9 — “(v2) a futuro me gustaria tb tener un gui para configuirar todo esto de antes.”
- S10 — “ademas de duration, que se puede definir por widget o global , brillo, rotacion , fps , mask.”
- S11 — “Fijate que todo lo que armemos como widget sean modulos / plugins , para simplificar el mantenimiento si te parece.”
- S12 — “Antes de arrancar decime que paleta encontras activa de noctalia. Por ahi es mejor definir un template de noctalia, en vez de leer que noctalia nos mande la config de colores.”
- S13 — “hagamos un odd si queres para esto, pero si me gustaria que documentemos minimamente que vamos a hacer para que no perdamos contexto .”
- S14 — “fijate que lo clonaste en carpeta separada. por ahi es mejor omitar la carpeta del repo cm-pixel es el root”

## Tasks

- T1 [S1–S14] — Record requirements, current palette, architectural direction and uncertainties; route: inline, documentation only; commit: `500b02e`.
- T2 [S1, S3, S6–S8, S10–S11] — First local milestone: tested TOML validation and last-good reload, modular widgets, normal/locked playlists with inherited options, clock and CPU/GPU sensor samples, and a bounded demo; route: scoped worker under context backstop; commits: `500b02e`, `837ebe7`.
- T3 [S1, S3, S10] — Connect real CPU/GPU samples, CPU utilization and one live USB frame owner to the tested widget sequence; route: scoped worker under context backstop; commit: `74b481d`.
- T4 [S9] — Proposed v2 configuration GUI, separately scoped after v1; route: deferred; commit: none.
- T5 [S2, S4, S7, S12] — Integrate Noctalia v5 template palette and locked/unlocked transitions with startup state reconciliation; route: scoped worker under context backstop after T3; commit: `7bea6b0`.
- T6 [S5–S6] — Persistent validated hot reload, error feedback and restartable user service; route: scoped worker under context backstop after T3/T5; separately authorized installation outside repo by parent; commit: pending.

## Design notes

- Current Noctalia IPC reports palette `custom rose2`, resolved mode `dark`. This identifies the palette but not its hexadecimal values.
- Prefer a Noctalia v5 theme template that renders resolved color roles into an application-owned palette file. Noctalia's documented template processing can refresh that file as the theme changes. Do not parse Noctalia's internal settings as the palette API. Source: https://docs.noctalia.dev/noctalia/v5.6.0/theming/templates/ .
- Noctalia v5 documents `session_locked` and `session_unlocked` hooks after the compositor confirms lock transitions. Consider hooks for fast transitions plus a startup reconciliation of current lock state; validate the user's installed version before wiring anything. Source: https://docs.noctalia.dev/noctalia/v5.6.0/automation/hooks/ .
- Proposed v1 shape: a single USB frame owner; a widget interface (`render(frame, sampled_data, palette, time)`) with independently maintained clock, date, CPU/GPU sensor, and animation modules; a sequencer with separate normal/locked playlists; per-widget overrides inheriting environment/global defaults for duration, brightness, rotation, FPS and mask. This is an architectural proposal, not a new requirement.
- Configuration: propose TOML to match Noctalia's v5 ecosystem; parse and validate a complete candidate before swapping it in, retaining the last good configuration on failure. Define a usable diagnostic path before promising an on-screen error. Run as a user service with restart-on-failure only after lock, device ownership and lifecycle behavior are verified.
- GPU temperature/utilization is available via `nvidia-smi`; CPU Tctl temperature via `sensors -j`; CPU utilization requires two `/proc/stat` aggregate-counter samples (idle + iowait idle), treating an initial or invalid delta as unavailable. The latter path was authorized for local reads. Lock integration, physical legibility, palette template merge and service lifecycle still need proof. Keep v2 GUI out of v1.
- Local USB evidence: `2516:021c`, screen frame interface `/dev/hidraw5`; installed `cm-pixel 0.1.0` needed a local `hidraw` import instead of its default backend on this machine. That installed patch can be overwritten by reinstalling; design a reproducible dependency/backend arrangement before service deployment.
- Local v1 source implementation is authorized by L9. No SSH push, PR or external configuration writes are authorized by these notes alone. The user separately approved read-only `/proc/stat` and `/home/gmusa/.config/noctalia/` inspection for the next step.
- Local discovery: Noctalia v5.6.0 reports `locked: false` via `noctalia msg status`. `sensors -j` exposes `k10temp-pci-00c3` → `Tctl` for CPU temperature; `nvidia-smi` exposes NVIDIA GeForce RTX 5070 temperature, utilization, fan speed and power. `asusec-isa-000a` reports `CPU_Opt` fan RPM as zero in this sample; don't promise a working fan-speed display. A `sensors -j` invocation also emitted an unreadable `temp4_input` diagnostic; tolerate partial readings. No extra outside-tree files were read directly.
- For T2, keep hardware writes out of tests. Treat CPU utilization (`/proc/stat`) and the live installed hidraw backend as explicit later integration checks, rather than silently assuming they work. T2's preview samples are synthetic; no live sensor-to-display loop, autonomous watcher, on-screen error or physical legibility has been proven.

## Log

- L1 — Original request (verbatim):

> mira Lo que me gustaria es poder armar algo que haga ciclos de info
>
> - info de sensores ( cpu , gpu ) temperatura, velocidad , una animacion del uso , reloj digital / analogico , fecha
> - si la maquina esta loqueada que reprodusca una animacion ( podemos usar las del mismo cm-pixel, o estas de reloj que dije antes.
> - ver si los sensores podemos hacerle algun detalle visual para que no sea solo texto.
> - Uso noctalia v5 , estaria bueno respetar la paleta de colores activa de noctalia
> - ver que corra siempre y que se vuelva a iniciar si se cae el servicio.
> - la configuracion que tenga hot-reload y validacion ( noctalia suele mostrar un error en pantalla cuando hay error de config ) [yaml / toml ]
> - Estaria bueno poder armar la secuencia de widgets de info que ciclan en entorno normal. y los que cliclan en entorno locked
> - por cada widget estaria bueno poder definer su tiempo de ejecucion o uno general a nivel entorno ( locked / unlocked )
> - (v2) a futuro me gustaria tb tener un gui para configuirar todo esto de antes.
>
> el repo es git@github.com:gmusa/cooler-master-masterliquid-360-atmos-ii-pixel-led.git con host Host github.com-personal para usar mi cuenta personal ,

- L2 — Additional requirements (verbatim):

> ademas de duration, que se puede definir por widget o global , brillo, rotacion , fps , mask.
>
> Fijate que todo lo que armemos como widget sean modulos / plugins , para simplificar el mantenimiento si te parece.
>
> Antes de arrancar decime que paleta encontras activa de noctalia. Por ahi es mejor definir un template de noctalia, en vez de leer que noctalia nos mande la config de colores.
>
> hagamos un odd si queres para esto, pero si me gustaria que documentemos minimamente que vamos a hacer para que no perdamos contexto .

- L3 — Repository root correction (verbatim):

> fijate que lo clonaste en carpeta separada. por ahi es mejor omitar la carpeta del repo cm-pixel es el root

- L4 — Evidence: cloning with `Host github.com-personal` succeeded without an ambient SSH agent. The remote repository is empty; `.git` was moved to `/home/gmusa/cm-pixel` after L3. No push occurred.
- L5 — User accepted the proposed first local milestone (verbatim):

> si dale

- L6 — First reviewable unit committed locally as `500b02e` (`feat(config): establish validated dashboard playlists and sensor adapters`); isolated staged checkout passed 15 config/sensor cases. No push. The remaining preview/widgets work is a separate unit; packaging CLI belongs with that unit to avoid a broken entry point.
- L7 — User explicitly changed this clone's review mode and authorized continuing (verbatim):

> desactivemos el rdd para este clon y sigamos

  `gentle-ai review mode disable --scope clone` returned `off (decided by clone_local)`; global remained on. Prior lineage `review-a9147e557e8346c6` stopped at `escalated/targeted_validator_rejected` without approval. The change of mode is not a review approval.
- L8 — Local first milestone: `837ebe7` added a bounded USB-free GIF preview, independently reviewed package/dependency risk (item 5), and passed 28 tests. A clean offline temporary install ran its packaged CLI and generated 3 GIF frames. A public 20-frame static example encoded exactly 20 frames; FPS `0.0001` exited 2 with `invalid fps` and no artifact. Upstream 556-LED membership was independently matched. The second work unit exceeds the approximate 400-line review target (536 additions plus 6 deletions) to keep its behavior, tests and docs together. No native review approval, service install or push.
- L9 — User authorized continuing v1 (verbatim):

> ok segui pedal a fondo

  User subsequently approved read-only local inspection of `/proc/stat` for CPU use and `/home/gmusa/.config/noctalia/` for integration location. This did not authorize writes under those paths.
- L10 — Read-only discovery: Noctalia local config currently contains `settings.json`, `colors.json`, `palettes/rose2.json` and `user-templates.toml` (commented examples). Hooks in `settings.json` are disabled; active palette `custom rose2`/`dark` was independently reported by Noctalia IPC. Avoid writing generated or legacy JSON files; verify installed v5.6.0 template behavior before any config integration. CPU usage `/proc/stat` is cumulative and needs two readings, not a single absolute reading. No outside-root writes.
- L11 — T3 committed locally as `74b481d` (`feat(live): stream sampled dashboard frames through hidraw`). 34 tests passed. An offline temporary installation of this package with `cm-pixel==0.1.0` drove the actual `2516:021c` frame HID interface for five seconds at 15% software brightness with CPU/GPU widgets, exit 0. Physical visual legibility was not observed by the agent; pump/fans and firmware were not addressed. Independent verifier confirmed source/fake-test logic but could not run USB in its read-only scope. No push.
- L12 — User authorized new Noctalia fragment `/home/gmusa/.config/noctalia/pixel-dashboard.toml` and generated palette `/home/gmusa/.config/pixel-dashboard/palette.toml`, both confirmed absent first. A standalone v5.6 fragment passed `noctalia config validate` exit 0; creating it and invoking `noctalia msg config-reload` returned `ok` and generated the exact palette file without a broad `templates-apply`. IPC still reported `custom rose2`, `dark`; generated roles parsed as primary `#ff8cb3`, on_surface `#ffe0eb`, secondary `#ffb3cc`. No existing Noctalia JSON was intentionally edited. No service installed or push.
- L13 — T5 committed locally as `7bea6b0` (`feat(noctalia): follow generated palette and fail-closed lock state`). 41 tests passed plus 4-frame exact differential of default preview output against T3. Real generated rose2 palette rendered in a 3-frame preview and a 4-second low-brightness physical USB live run (exit 0); independent verifier confirmed fail-closed behavior on IPC outage. A real compositor lock transition and LED legibility remain unobserved. User selected "Sí, instalar y arrancar servicio de usuario" after explicit scope naming: create `/home/gmusa/.config/pixel-dashboard/config.toml` and `/home/gmusa/.config/systemd/user/pixel-dashboard.service`, enable a `default.target.wants` link, and start it, only after tests and validation; no sudo or push.
- L14 — T6 source passed 43 tests; `systemd-analyze verify` passed after an offline `.venv` installation whose CLI bytes match current source. The user separately authorized `fuser /dev/hidraw5` (reads `/proc/*/fd`) to check ownership before startup; the interface was free. A new validated config with normal brightness 15% and locked 10% and a new user unit were installed at the explicitly authorized paths. `systemctl --user enable --now pixel-dashboard.service` created the authorized link; after eight seconds the service was active, zero restarts and sole `/dev/hidraw5` owner. Temporarily invalidating the owned config produced `pixel-dashboard: invalid configuration: Invalid value (at end of document)` in user service status; the same service PID remained active, and the exact config bytes were restored. Current config/palette revalidated and service remains active, enabled, with zero restarts. Visual desktop notification and compositor lock transitions were not observed. Independent verifier confirmed source but required this environment/device proof. Engram runtime contract could not be confirmed (`engram.pi-http-runtime/v1` unavailable), so persistent memory save is unverified; this feature document remains the local continuity record. No push.
