import sys
from pathlib import Path

package_dir = str(Path(__file__).parent.resolve())
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

try:
    from .pipeline import discovery_pipeline
except ImportError:
    from pipeline import discovery_pipeline

root_agent = discovery_pipeline
