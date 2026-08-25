from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScriptTests(unittest.TestCase):
    def test_wechat_stitch_dimensions(self) -> None:
        module = load_module(
            "build_wechat_cover_stitch",
            ROOT / "scripts" / "build-wechat-cover-stitch.py",
        )
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            square = work / "square.png"
            wide = work / "wide.png"
            output = work / "stitch.png"
            Image.new("RGB", (400, 400), "#dd5522").save(square)
            Image.new("RGB", (940, 400), "#101820").save(wide)

            module.build_stitch(square, wide, output)

            with Image.open(output) as result:
                self.assertEqual(result.size, (1340, 400))
                self.assertIsNotNone(result.info.get("icc_profile"))

    def test_ratio_renderer_self_test(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render-ratio-pack.py"), "--self-test"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_public_audit(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_public.py")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
