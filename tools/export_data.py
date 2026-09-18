"""Materialize the paper's synthetic samples, with array hashes and seed provenance."""
from __future__ import annotations
from dataclasses import replace
import hashlib
from pathlib import Path
import numpy as np
from tools.common import REFERENCE, load_engine, load_json, sha256, write_json


def export_data(args, output: Path) -> None:
    engine = load_engine()
    core = engine.r
    offset = args.seed_offset
    if offset is None:
        offset = 0 if args.benchmark == "A" else 100000
    allowed = engine.OFFSETS if args.benchmark == "A" else [100000]
    if offset not in allowed:
        raise ValueError(f"Allowed offsets for {args.benchmark}: {allowed}")
    plant = core.make_plant(args.benchmark)
    if args.benchmark == "B":
        if args.gamma not in engine.SHIFT_FACTORS:
            raise ValueError(f"Choose a paper shift factor: {engine.SHIFT_FACTORS}")
        plant = replace(plant, gamma=args.gamma)
    manifest = {"benchmark": args.benchmark, "seed_offset": offset,
                "gamma": plant.gamma, "arrays": {}, "reference_hash_checks": {}}

    def save(name: str, array: np.ndarray, seed=None, expected=None) -> None:
        file = output / f"{name}.npy"
        np.save(file, array, allow_pickle=False)
        raw = hashlib.sha256(array.tobytes()).hexdigest()
        manifest["arrays"][file.name] = {"shape": list(array.shape), "dtype": str(array.dtype),
            "primitive_seed": seed, "raw_c_order_sha256": raw, "npy_file_sha256": sha256(file)}
        if expected is not None:
            good = raw == expected
            manifest["reference_hash_checks"][file.name] = good
            if not good:
                raise RuntimeError(f"Generated array differs from archived calibration manifest: {name}")

    if args.benchmark == "A":
        ref = load_json(REFERENCE / "results/A/data_manifest.json")[str(offset)]
    else:
        ref = load_json(REFERENCE / "results/B/data_manifest.json")
    for split, count, base in [("design", engine.NDES, 1100), ("calibration", engine.NCAL, 2100)]:
        hashes = ref[f"{split}_hashes"] if args.benchmark == "A" else ref[split]
        for g in range(plant.ng):
            seed = offset+base+g
            E = core.calibration_trajectories(plant, count, seed, g)
            save(f"{split}_g{g}", E, seed, hashes[g])

    if args.include_test and args.benchmark == "A":
        for g in range(plant.ng):
            seed = offset+3100+g
            E = core.calibration_trajectories(plant, engine.NTEST, seed, g)
            save(f"test_g{g}", E, seed, ref["test_hashes"][g])
    elif args.include_test:
        # This is the particular nominal K-feedback-tail diagnostic in §8.4.
        # The uniform guarantee comes from the likelihood-ratio proof, not this test.
        n, seed = engine.NTEST, 104100
        rng = np.random.default_rng(seed+100)
        initial = np.c_[rng.uniform(-2.4, 2.4, n), rng.uniform(-.35, .35, n)]
        save("test_initial_states", initial, seed+100)
        for g in range(plant.ng):
            modes, eta, mix = core.paths(plant, n, seed+g, g)
            real, nominal = initial.copy(), initial.copy()
            errors = []
            for t in range(plant.H):
                u = (real @ plant.K.T).ravel()
                alpha = plant.alpha0*(1+(plant.gamma**(1/plant.H)-1)*np.tanh(
                    (real[:,0]/2)**2+(real[:,1]/1.5)**2+(u/2)**2))
                noise = np.einsum("nij,nj->ni", plant.L[modes[:,t]], eta[:,t])+plant.means[modes[:,t]]
                noise *= np.where(mix[:,t] < alpha, plant.heavy_scale, 1)[:,None]
                real = real @ plant.AK.T + noise
                nominal = nominal @ plant.AK.T
                errors.append(real-nominal)
            save(f"test_g{g}", np.stack(errors, axis=1), seed+g)
            save(f"test_modes_g{g}", modes, seed+g)
            save(f"test_eta_g{g}", eta, seed+g)
            save(f"test_mixture_uniforms_g{g}", mix, seed+g)
        manifest["test_scope"] = "State-dependent K-feedback-tail diagnostic from the paper, at the selected Gamma."

    if args.include_mission_primitives:
        seed = offset+5100 if args.benchmark == "A" else 105100
        n = engine.MISSIONS if args.benchmark == "A" or args.gamma == 3 else 40
        modes, eta, mix = core.paths(plant, n, seed, None, engine.T+plant.H)
        save("mission_modes", modes, seed)
        save("mission_eta", eta, seed)
        save("mission_mixture_uniforms", mix, seed)
        rng = np.random.default_rng(seed+777)
        initial = np.c_[rng.uniform(-6, 6, n), rng.uniform(-.6, .6, n)]
        if args.benchmark == "B":
            initial[:,0] *= 3.2/6
            initial[:,1] *= .5/.6
        save("mission_initial_states", initial, seed+777)
    write_json(output / "data_manifest.json", manifest)
    print(f"Exported {len(manifest['arrays'])} arrays to {output}; all available reference hashes match.")
