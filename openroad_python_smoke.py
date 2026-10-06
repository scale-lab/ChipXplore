"""Exercise installed OpenROAD Python bindings, including an OpenDB round trip."""
import sys
import tempfile
from pathlib import Path
import openroad
from openroad import odb

tech = openroad.Tech()
openroad.set_thread_count(1)
assert openroad.thread_count() == 1
design = openroad.Design(tech)
assert design.getDb() is not None

db = odb.dbDatabase.create()
db_tech = odb.dbTech.create(db, "smoke_tech")
chip = odb.dbChip.create(db, db_tech)
block = odb.dbBlock.create(chip, "chipxplore_smoke")
net = odb.dbNet.create(block, "smoke_net")
assert net.getName() == "smoke_net"
with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "smoke.odb")
    odb.write_db(db, path)
    restored = odb.dbDatabase.create()
    odb.read_db(restored, path)
    restored_block = restored.getChip().getBlock()
    assert restored_block.getName() == "chipxplore_smoke"
    assert restored_block.findNet("smoke_net").getName() == "smoke_net"
    odb.dbDatabase.destroy(restored)
odb.dbDatabase.destroy(db)
print("Python:", sys.version)
print("OpenROAD package:", openroad.__file__)
print("PASS: OpenROAD Tech/Design, thread control, OpenDB creation and file round trip")
