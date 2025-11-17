"""
PyTTI Web UI - Module entry point

Allows running the web UI as a module:
    python -m pytti.webui
    python -m pytti.webui --share

Includes environment compatibility checks to detect common dependency issues.
"""

import sys


def run_with_checks():
    """Run web UI with environment checks"""
    # Run environment checks BEFORE importing the main app
    # This prevents cryptic import errors from pandas/gradio
    from pytti.webui.check_environment import check_environment

    if not check_environment():
        print("\n❌ Environment setup incomplete. Please fix the issues above.\n")
        sys.exit(1)

    # Environment is OK - import and run the main app
    from pytti.webui.app import main
    main()


if __name__ == "__main__":
    run_with_checks()
