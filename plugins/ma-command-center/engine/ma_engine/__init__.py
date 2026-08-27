"""ma_engine -- the shared engine behind both M&A skills.

  config    portable deal-path resolution for CFOforIT and client installs
  validate  the financial tie-out gate (mirrors mhr_engine.validate)
  render    the tabbed command-center artifact
"""


# ONE version number for this engine, and the code owns it: pyproject.toml reads
# it via `dynamic = ["version"]`, so it must stay a plain string literal that
# setuptools can parse statically. Never restate the number in pyproject.
#
# 1.0.0 is a baseline, not a reconstruction. This engine shipped with no version
# of any kind, in code or in packaging, which is why nothing could tell a current
# install from a three-week-old one. Prior history was not reconstructed; bump
# MAJOR/MINOR/PATCH from here per Rule 17.
#
# Distinct from config.CONFIG_VERSION, which versions the deal-config schema and
# is not this.
__version__ = "1.0.0"


class MAError(Exception):
    """Raised when the engine refuses to proceed.

    Mirrors mhr_engine.MHRError deliberately. The gate's job is to stop, not to
    return a degraded result that reads like a good one, so a blocking tie-out
    failure raises rather than returning a report the caller might ignore.
    """

    def __init__(self, message: str, *, stage: str = "", schedule: str = "",
                 detail: str = ""):
        self.stage = stage
        self.schedule = schedule
        self.detail = detail
        parts = [message]
        if stage:
            parts.append(f"stage={stage}")
        if schedule:
            parts.append(f"schedule={schedule}")
        if detail:
            parts.append(f"detail={detail}")
        super().__init__("; ".join(parts))
