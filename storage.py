"""
Main loader
"""

from sources.classes.class_engine import DwgbEngine
from sources.commands import DwgbCmdConsts

print("Connecting...")
tmp_engine = DwgbEngine("token",
                        "postgres://",
                        0,
                        "bagapi",
                        {
                            2000000001: None
                        })
print("Listening...")
tmp_engine.listen()
