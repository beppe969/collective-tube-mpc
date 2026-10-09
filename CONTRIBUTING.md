# Contributions

Run the unit tests and a smoke simulation before proposing code changes:

```bash
python -m unittest discover -s tests -v
python reproduce.py smoke --output runs/contribution-smoke
```

Changes to the numerical engine should also undergo a full paper reproduction. Keep generated runs outside `reference/`, and retain the reference PDF and its checksum. Describe changes to statistical assumptions or experimental parameters explicitly.

The code distinguishes diagnostic cases from certified constructions. Preserve that distinction when adding methods, and report both accepted and rejected parameter settings.
