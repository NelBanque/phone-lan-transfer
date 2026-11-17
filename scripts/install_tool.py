"""Install this checkout as a user tool using its locked runtime dependencies."""

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    uv_path = shutil.which("uv")
    if uv_path:
        uv = [uv_path]
    elif importlib.util.find_spec("uv") is not None:
        uv = [sys.executable, "-m", "uv"]
    else:
        parser.error("Install uv first, then run this script again. See README.md.")

    try:
        with TemporaryDirectory(prefix="phonelt-install-") as temporary:
            constraints = Path(temporary) / "runtime-constraints.txt"
            subprocess.run(
                [
                    *uv,
                    "export",
                    "--locked",
                    "--no-dev",
                    "--no-emit-project",
                    "--no-hashes",
                    "--format",
                    "requirements.txt",
                    "--output-file",
                    str(constraints),
                    "--quiet",
                ],
                cwd=project,
                check=True,
            )
            subprocess.run(
                [
                    *uv,
                    "tool",
                    "install",
                    "--force",
                    "--editable",
                    str(project),
                    "--python",
                    sys.executable,
                    "--constraints",
                    str(constraints),
                ],
                cwd=project,
                check=True,
            )
    except subprocess.CalledProcessError as error:
        print(
            "Installation failed; resolve the uv error above and retry.",
            file=sys.stderr,
        )
        return error.returncode
    print("Installed phonelt using uv.lock. Start with: phonelt")
    print("If it is not found, run uv tool update-shell and reopen your terminal.")
    print("Keep this checkout in place; reinstall after moving it or updating uv.lock.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
