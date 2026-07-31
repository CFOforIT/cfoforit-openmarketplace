"""config.py -- portable deal-path resolution for both install shapes.

This plugin ships to two kinds of machine (see shared/ma-config.md):

  cfoforit    CFOforIT staff running deals across many clients, against the
              firm's SharePoint convention.
  single_org  a client who installed the plugin to run their OWN deals on
              their own drive, where a `Clients/{Client}/` layer would be
              meaningless because they are the only client.

One code path serves both via `path_template`. Nothing here hardcodes a
user-profile path -- the firm's portability check greps for exactly that, and
it exists because a hardcoded path once shipped and broke every other
machine.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_FILENAME = "ma-config.json"
CONFIG_ENV_VAR = "CFOFORIT_MA_CONFIG"
CONFIG_VERSION = "1.0.0"

DEPLOYMENTS = ("cfoforit", "single_org")

DEFAULT_TEMPLATES = {
    # Keeps the per-client layer: one install serves many clients. The
    # {ma_folder} layer is DISCOVERED, not named -- see find_ma_folder().
    "cfoforit": "{deal_root}/{client}/{ma_folder}/{target}/M&A Package",
    # No client layer: there is only one, so a folder for it is noise. No
    # {ma_folder} layer either -- deal_root is theirs to point wherever they
    # like, so an imposed intermediate folder would just be our convention on
    # someone else's drive.
    "single_org": "{deal_root}/{target}/M&A Package",
}

# Every CFOforIT client folder carries a folder for M&A material, and its name
# varies: the numeric prefix and index differ by client and by when the client
# was provisioned ("08.2 - M&A Related" in the wild). The one stable thing is
# that the name contains "M&A", so it is matched by name and never by position.
MA_FOLDER_MARKER = "m&a"

# A client install defaults to emitting client-audience builds. Without this a
# client running the plugin on their own machine would produce builds stamped
# INTERNAL containing CFOforIT's own deal-team workplan.
DEFAULT_AUDIENCE = {"cfoforit": "firm", "single_org": "client"}


class ConfigError(Exception):
    """Raised instead of guessing. A wrong deal path either fails loudly or
    quietly writes confidential deal data somewhere unintended; there is no
    acceptable silent fallback."""


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(p))))


def find_config(start: Path | None = None) -> Path | None:
    """Discovery order, stopping at the first hit. Deliberately does NOT fall
    back to the CFOforIT convention: this may not be a CFOforIT machine."""
    env = os.environ.get(CONFIG_ENV_VAR)
    if env:
        cand = _expand(env)
        if cand.is_file():
            return cand
        raise ConfigError(
            f"{CONFIG_ENV_VAR} points at {cand}, which is not a readable file. "
            f"Fix or unset it -- refusing to fall back to a default path.")

    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        cand = d / CONFIG_FILENAME
        if cand.is_file():
            return cand
        if d == here.parents[3] if len(here.parents) > 3 else False:
            break
    return None


def load_config(path: Path | None = None, *, start: Path | None = None) -> dict:
    path = path or find_config(start)
    if path is None:
        raise ConfigError(
            f"no {CONFIG_FILENAME} found and {CONFIG_ENV_VAR} is unset. Run "
            f"first-run setup (see shared/ma-config.md) to record where deal "
            f"folders live on this machine. Not assuming the CFOforIT layout, "
            f"because this may not be a CFOforIT machine.")
    try:
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"{path} could not be read as JSON: {e}") from e
    return validate_config(cfg, source=str(path))


def validate_config(cfg: dict, *, source: str = "<in-memory>") -> dict:
    dep = cfg.get("deployment")
    if dep not in DEPLOYMENTS:
        raise ConfigError(
            f"{source}: deployment must be one of {DEPLOYMENTS}, got {dep!r}")
    if not cfg.get("deal_root"):
        raise ConfigError(f"{source}: deal_root is required")
    if not cfg.get("organization_name"):
        raise ConfigError(
            f"{source}: organization_name is required -- it names the party in "
            f"the artifact masthead and 'Prepared for' footer")

    cfg.setdefault("config_version", CONFIG_VERSION)
    cfg.setdefault("path_template", DEFAULT_TEMPLATES[dep])
    cfg.setdefault("render_subfolder", "renders")
    cfg.setdefault("default_audience", DEFAULT_AUDIENCE[dep])

    if cfg["default_audience"] == "target":
        raise ConfigError(
            f"{source}: default_audience cannot be 'target'. A target-facing "
            f"build omits the buyer's own pricing and addback analysis and "
            f"needs explicit per-render sign-off; it is never a default.")

    if dep == "single_org" and "{client}" in cfg["path_template"]:
        raise ConfigError(
            f"{source}: path_template uses {{client}} but deployment is "
            f"single_org, which has no client layer. Remove the token or "
            f"switch deployment to 'cfoforit'.")

    if dep == "single_org" and "{ma_folder}" in cfg["path_template"]:
        raise ConfigError(
            f"{source}: path_template uses {{ma_folder}} but deployment is "
            f"single_org. That layer is CFOforIT's own filing convention, "
            f"discovered inside a client folder we did not create. On a "
            f"client's own drive deal_root already points where they want "
            f"deals, and this would impose our folder scheme on them -- and "
            f"then fail, because their drive has no folder named \"M&A\".")

    if "{ma_folder}" in cfg["path_template"] and "{client}" not in cfg["path_template"]:
        raise ConfigError(
            f"{source}: path_template uses {{ma_folder}} without {{client}}. "
            f"The M&A folder is found inside a specific client's folder, so "
            f"there is nowhere to look for it without one.")
    return cfg


def find_ma_folder(client_dir: Path) -> str:
    """The name of the client's M&A folder, found by NAME among that folder's
    direct children.

    By name and not by position, because the numeric prefix varies by client
    ("08.2 - M&A Related"), and by direct child only, because a deeper match is
    something else entirely -- every target folder contains an "M&A Package",
    and a recursive search would happily return one of those and file the next
    deal inside the last one.

    Ambiguity raises. Two candidate folders means the client's drive was
    reorganised or a stray folder was created, and picking one silently files
    confidential deal material somewhere nobody will look for it.
    """
    client_dir = Path(client_dir)
    if not client_dir.is_dir():
        raise ConfigError(
            f"client folder {client_dir} does not exist. This skill never "
            f"creates a client root -- those are provisioned elsewhere.")

    hits = sorted(p.name for p in client_dir.iterdir()
                  if p.is_dir() and MA_FOLDER_MARKER in p.name.casefold())
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise ConfigError(
            f"no M&A folder directly under {client_dir}. Expected one folder "
            f"whose name contains \"M&A\" (e.g. \"08.2 - M&A Related\"). "
            f"Create it in SharePoint first, or say which existing folder to "
            f"use -- guessing would scatter this deal outside the convention.")
    raise ConfigError(
        f"{len(hits)} folders under {client_dir} contain \"M&A\": "
        f"{', '.join(hits)}. Say which one -- refusing to guess.")


def resolve_deal_path(cfg: dict, *, target: str, client: str | None = None,
                      ma_folder: str | None = None) -> Path:
    """Resolve one deal's folder, refusing any result that escapes deal_root.

    The escape check is not paranoia: a `..` in a target name, or an absolute
    path arriving where a name was expected, is exactly how one client's deal
    data ends up written into another client's folder.

    When the template carries {ma_folder} and none is passed, the folder is
    discovered on disk via find_ma_folder(). Pass one explicitly to skip the
    lookup -- which the caller must do when the drive is not mounted, rather
    than have this quietly resolve to a path that does not exist.
    """
    cfg = validate_config(dict(cfg))
    root = _expand(cfg["deal_root"]).resolve()
    tpl = cfg["path_template"]

    if "{client}" in tpl and not client:
        raise ConfigError(
            "path_template needs {client} but no client was supplied")

    # Validate the caller-supplied names BEFORE touching the disk, so a
    # traversal attempt is refused rather than used to go looking for folders.
    for label, val in (("target", target), ("client", client)):
        if val is None:
            continue
        if not str(val).strip():
            raise ConfigError(f"{label} is empty")
        if os.path.isabs(str(val)) or ".." in Path(str(val)).parts:
            raise ConfigError(
                f"{label}={val!r} is not a plain folder name. Absolute paths "
                f"and '..' are refused -- that is how deal data lands in the "
                f"wrong folder.")

    if "{ma_folder}" in tpl:
        if ma_folder is None:
            ma_folder = find_ma_folder(root / str(client))
        # A discovered name is still untrusted: it came off a drive that may be
        # shared, and it is about to become part of a path.
        if not str(ma_folder).strip():
            raise ConfigError("ma_folder is empty")
        if os.path.isabs(str(ma_folder)) or ".." in Path(str(ma_folder)).parts:
            raise ConfigError(
                f"ma_folder={ma_folder!r} is not a plain folder name; refusing")
    elif ma_folder is not None:
        raise ConfigError(
            f"ma_folder={ma_folder!r} was supplied but path_template has no "
            f"{{ma_folder}} token, so it would be silently ignored")

    rendered = tpl.format(deal_root=str(root), client=client or "",
                          target=target, ma_folder=ma_folder or "")
    resolved = Path(rendered).resolve()

    if root != resolved and root not in resolved.parents:
        raise ConfigError(
            f"resolved deal path {resolved} escapes deal_root {root}; refusing")
    return resolved


def resolve_render_path(cfg: dict, *, target: str, client: str | None = None,
                        audience: str, ma_folder: str | None = None) -> Path:
    deal = resolve_deal_path(cfg, target=target, client=client,
                             ma_folder=ma_folder)
    return deal / cfg.get("render_subfolder", "renders") / audience


def default_config(*, deployment: str, organization_name: str,
                   deal_root: str) -> dict:
    """The object first-run setup writes, after confirming with the user."""
    if deployment not in DEPLOYMENTS:
        raise ConfigError(f"deployment must be one of {DEPLOYMENTS}")
    return validate_config({
        "config_version": CONFIG_VERSION,
        "deployment": deployment,
        "organization_name": organization_name,
        "deal_root": deal_root,
        "render_subfolder": "renders",
        "default_audience": DEFAULT_AUDIENCE[deployment],
        "path_template": DEFAULT_TEMPLATES[deployment],
    })
