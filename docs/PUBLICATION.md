# Preparing the GitHub release

## Author decisions

The MIT license at the repository root is a proposed default. Confirm the copyright attribution and licensing choice before making the repository public. The source archive did not specify a release license. Dependencies remain governed by their own licenses.

`CITATION.cff` identifies the manuscript and software version without a repository URL or DOI. Add the real repository URL after creating it. Add a publication DOI or an archival software identifier only after it exists. The manuscript citation is currently marked as unpublished because the supplied sources do not establish a final published version.

The package excludes the editor's decision letter and reviewer correspondence. It also excludes the full manuscript PDFs. The exact numerical-section source fragment is included solely to identify the reported protocol. Review that fragment and the provenance metadata before public release.

## Initial upload

Create an empty GitHub repository, using a name such as `contextual-collective-tube-mpc`. From the extracted package directory, initialize the local repository and upload it with Git:

```bash
git init -b main
git add .
git status --short
git commit -m "Add numerical reproducibility package"
git remote add origin <YOUR-REPOSITORY-URL>
git push -u origin main
```

Replace `<YOUR-REPOSITORY-URL>` with the actual URL of the empty repository. Run `git status` before committing to verify that only the intended package files are staged. The `.gitignore` excludes local environments and generated runs. Uploading through Git also preserves the hidden `.github/` workflow directory.

## First validation after upload

Allow the routine reproducibility workflow to finish. Then launch **Full paper reproduction** manually from the Actions tab. Its artifact contains the regenerated tables and figures together with the verification report. The local package validation is recorded in `validation/`; the hosted workflow supplies a separate check of installation and execution on the selected GitHub runner.

After that run passes, a version tag can identify the exact source snapshot:

```bash
git tag -a v1.0.0 -m "Reproducibility snapshot for the current manuscript"
git push origin v1.0.0
```

The tag and any subsequent release should retain the reference outputs and numerical source hashes. A permanent software archive can then refer to that exact tag. This package does not create a GitHub repository, publish a release, or assign a DOI.

## Maintaining the paper reference

The four scripts in `experiments/` are intentionally preserved. Experimental extensions should use a separate branch or a separate driver and a fresh results directory. Keep the current reference files as the baseline, so that changes to the experimental design remain visible.

When a future paper revision changes the numerical protocol, update the provenance record and the manuscript mapping together. Regenerate the results and retain the prior release tag. The checksum manifest should be updated only as part of that recorded protocol change, rather than to conceal an unexpected mismatch.

## Documentation sources

The repository-structure guidance was checked against GitHub's official documentation on citation files and repository licensing. The workflow syntax was checked against the official action repositories. The license text follows the Open Source Initiative's MIT license text. These checks concern packaging and publication conventions; the numerical methodology comes from the supplied manuscript and experiment code.
