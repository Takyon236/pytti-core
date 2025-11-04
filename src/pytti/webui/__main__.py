"""
PyTTI Web UI - Module entry point

Allows running the web UI as a module:
    python -m pytti.webui
    python -m pytti.webui --share
"""

from pytti.webui.app import main

if __name__ == "__main__":
    main()
