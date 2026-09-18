# Contributing

This repository preserves the numerical protocol of the accompanying manuscript. Please describe whether a proposed change affects the scientific protocol or only the repository tooling.

For a tooling change, run `python -m unittest discover -s tests -v` and the smoke test. A change touching numerical execution should also run the full reproduction and retain its verification report. Keep the archived results intact.

An issue about an output mismatch should include the command and the Python/package versions. Include the relevant excerpt from `verification.json` and any optimizer error message. Avoid uploading unrelated local files or credentials.

The paper's fixed-stream results serve as a regression baseline. New experiments should be labelled separately and should state their changed parameters and random seeds.
