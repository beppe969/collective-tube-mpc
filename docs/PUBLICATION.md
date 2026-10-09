# Uploading the release

The destination is `https://github.com/beppe969/collective-tube-mpc`.

Extract the ZIP and upload the **contents of its `collective-tube-mpc/` folder** to the repository root. `README.md` should be directly visible at that root. Include the `.github/` directory and the other supplied dotfiles when using a local Git client.

The archive has no `.git` directory and carries no existing commit ancestry. Its included paper is the supplied PDF, and all manuscript source files are excluded. The package performs no remote writes.

## Fresh initial commit

These commands assume that an empty destination repository with the required name has already been created. Run them inside the extracted release folder:

```bash
git init -b main
git add .
git commit -m "Initial release"
git remote add origin https://github.com/beppe969/collective-tube-mpc.git
git push -u origin main
```

They use an ordinary push. A pre-existing remote history can cause that push to be rejected; complete the separate repository-reset procedure before publishing this fresh initial commit. Keep any private backups outside the upload directory.

## Publication checks

Run `python reproduce.py check-reference` before upload. After publication, the repository's Actions tab provides a manually triggered full reproduction. Its `verification.json` should report success.

The reference results include diagnostic failures discussed in the paper. Keep those rows and the sample-rejected shift settings when publishing the numerical record.

The code retains the license supplied with the input package. The included manuscript remains subject to its author's rights. `CITATION.cff` identifies the paper without adding an unverified journal citation or DOI.
