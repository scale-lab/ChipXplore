# OpenLane and PicoRV32 DEF generation

This setup installs OpenLane **2.3.10** as an Apptainer container and runs the
official PicoRV32 RTL with **Sky130A / sky130_fd_sc_hd**. It uses OpenLane's
bundled synthesis and physical-design tools and the PDK revision selected by
Volare for that release.

## Current status

OpenLane **2.3.10 is installed** and its version check passed. The first job,
**6967548**, failed before synthesis while Volare downloaded the Sky130 PDK:
`OSError: [Errno 28] No space left on device`. Apptainer's contained temporary
filesystem has a 64 MB limit on this system.

Retry job **6975588** binds the container's `/tmp` to node-local disk, sets
`TMPDIR=/work/tmp`, and requires at least 20 GiB free before starting. **DEF
generation is pending; no successful design run has been verified yet.** The
retry retains the original output directory below. Its log is
`openlane-picorv32-6975588.log`. The original failure is retained in
`job-status-original-6967548.txt`; `run-info.txt` identifies the retry job.

Expected output directory:

```text
designs/picorv32-openlane-6967548/
├── floorplan/  # picorv32.def, picorv32.sdc, picorv32.odb
├── placement/  # picorv32.def, picorv32.sdc, picorv32.odb
├── cts/        # picorv32.def, picorv32.sdc, picorv32.odb
├── routing/    # picorv32.def, picorv32.sdc, picorv32.odb, picorv32.spef
├── manifest.json
├── pdk-libs-ref.txt
├── versions.txt
├── config.json
├── src/
├── runs/       # full flow outputs, reports, and per-step logs
└── job-status.txt
```

Success requires `exit_code=0` in `job-status.txt`, the final `PASS: PicoRV32 DEF
snapshots generated and checked` message in the log, and all four entries in
`manifest.json`. A partial or failed run is preserved for diagnosis and must not
be treated as complete.

## Reproduce the run

Inspect [run_picorv32_openlane.sbatch](run_picorv32_openlane.sbatch), then submit
from this repository's root:

```bash
cd /oscar/data/sreda/mabdelat/ChipXplore
sbatch run_picorv32_openlane.sbatch
```

The script requests one CPU, 32 GB RAM, and up to 24 hours on `batch`. It builds
the Apptainer SIF and runs implementation on a compute node. Downloads, container
caches, PDK setup, and design work use node-local temporary storage. Final
artifacts, logs, and the matching PDK are preserved on shared storage.
Each normal submission writes a new output directory based on its Slurm job ID.
To retry the original failed run's output directory after checking that it has
no stage snapshots, the submitted recovery command was:

```bash
sbatch --export=ALL,OPENLANE_RESULT_ID=6967548 run_picorv32_openlane.sbatch
```

The script refuses to replace any existing floorplan, placement, CTS, or routing
snapshot. `job-status.txt` reflects the most recent attempt after it exits.

Sources are pinned:

- OpenLane: `2.3.10`, upstream commit
  `b89f7866fd3d19da470220baf89d0e7804962941`.
- Container: `ghcr.io/efabless/openlane2` at digest
  `sha256:1c85892f7e745780c4c6bf634205f53761e34e1eab124b057889975cc5908000`.
- PicoRV32 RTL: `ef203c2b0a3fb793280f5114941416c425c5b461` from
  [YosysHQ/picorv32](https://github.com/YosysHQ/picorv32/tree/ef203c2b0a3fb793280f5114941416c425c5b461).
  Its license is downloaded with the RTL.

[picorv32.openlane.json](picorv32.openlane.json) specifies the `picorv32` top
module, `clk`, a 100 ns clock period, 35% core utilization, and 45% placement
density. STA and detailed routing are limited to one thread. Lint warnings
remain in the reports but do not stop the example run; lint errors remain fatal.
These settings are for generating an inspectable example, not for performance
optimization or tapeout qualification.

## Installed command

The installation is under `.tools/openlane-2.3.10/`. After the image and launcher
have been installed:

```bash
export PATH="$PWD/.tools/openlane-2.3.10/bin:$PATH"
openlane --version
```

The launcher invokes the pinned image through Apptainer. Pass ordinary OpenLane
arguments; do not add `--docker`. Use the batch script for reproducible runs with
node-local work directories and controlled thread counts.

## Flow and exported snapshots

The flow runs through `OpenROAD.STAPostPNR`, including detailed routing, filler
insertion, RC extraction, and post-route timing analysis. It stops before GDS
stream-out and the subsequent physical signoff steps. These DEF files are not a
claim of completed signoff or timing closure.

[export_openlane_def.py](export_openlane_def.py) selects the following completed
OpenLane states:

| ChipXplore stage | OpenLane step |
|---|---|
| floorplan | OpenROAD.GeneratePDN |
| placement | OpenROAD.DetailedPlacement |
| cts | OpenROAD.ResizerTimingPostCTS |
| routing | OpenROAD.STAPostPNR |

For each snapshot it requires DEF, SDC, and ODB, checks the DEF design name and
end marker, and checks nonzero component/net counts. It records counts and file
hashes in the manifest. Routing also requires a nominal-corner SPEF. Exactly one
SPEF is placed at the routing directory's top level because ChipXplore's parser
selects the first matching file. Other corners remain in the full run outputs.
These export checks are structural checks, not an independent DRC/LVS run.

The exporter was tested against synthetic states, including rejection of an
incomplete DEF. That test does not establish that the actual flow has finished.

## Use in ChipXplore

After successful completion, use the matching PDK recorded by the job:

```bash
source .tools/openroad/env.sh
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
DESIGN_DIR="$PWD/designs/picorv32-openlane-6967548"
PDK_LIBS_REF=$(cat "$DESIGN_DIR/pdk-libs-ref.txt")
openroad-python core/parsers/design/design_parser.py \
  --input "$DESIGN_DIR" \
  --pdk "$PDK_LIBS_REF" \
  --stage routing \
  --format load \
  --output_dir ./output/picorv32/routing
```

This also requires the separate [OpenROAD Python installation](README.openroad.md)
and ChipXplore's Python dependencies. Run parsing in a compute allocation.
Prefer DEF/SDC for exchange between OpenLane's OpenROAD version and the separate
Bazel installation; ODB files are retained as native flow artifacts and may have
version compatibility constraints.

## References

- [OpenLane installation options](https://openlane2.readthedocs.io/en/latest/getting_started/installation_overview.html)
- [Pinned Classic flow](https://github.com/chipfoundry/openlane2/blob/2.3.10/openlane/flows/classic.py)
- [Pinned container definition](https://github.com/chipfoundry/openlane2/blob/2.3.10/nix/docker.nix)
