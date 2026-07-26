# Automated troubleshooting protocol

1. Reproduce with `./scripts/gate_phaseN.sh`; capture logs under `artifacts/debug/`.
2. Classify: schema | timing/EDL | ffmpeg | ASR | UI/jobs | CV | ranking.
3. Open `docs/debug/phaseN.md` and run listed checks.
4. Apply a minimal surgical fix.
5. Re-run the gate; commit and push to `main` with `fix(phaseN): …`.
6. Do not skip gates. Optional smoke (Whisper weights, Azure, full encode) may skip when tools/keys are absent.
