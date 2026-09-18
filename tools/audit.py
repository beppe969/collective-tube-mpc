"""Recompute geometric certificates and logged mission statistics.

These checks use the actual stored boxes and trajectories. They supplement the
reference comparison; a copied summary by itself cannot satisfy this audit.
The synthetic shock and the uninflated/no-edge diagnostics retain their stated
limitations. In particular, a row labelled 'certified_reset' by the common
simulation loop does not certify an uninflated deployment law in Benchmark B.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist
from tools.common import load_engine, load_json


def audit_results(results: Path) -> dict:
    engine = load_engine()
    core = engine.r
    errors: list[str] = []
    checks = 0
    atlases = missions = rows_checked = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not bool(condition):
            errors.append(message)

    def close(a, b, message: str, atol: float = 2e-7, rtol: float = 1e-8) -> None:
        check(np.shape(a) == np.shape(b) and bool(np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=True)), message)

    for apath in sorted(results.rglob("*_atlas.json")):
        rel = apath.relative_to(results).as_posix()
        label = rel.removesuffix("_atlas.json")
        parts = apath.relative_to(results).parts
        plant = core.make_plant("B" if parts[0] == "B" else "A")
        if parts[0] == "B":
            plant = replace(plant, gamma=float(parts[1].removeprefix("Gamma_")))
        record = load_json(apath)
        atlas = engine.load_atlas(apath, plant)
        atlases += 1
        nc, H = len(atlas.charts), plant.H
        sections = np.asarray([c.S for c in atlas.charts])
        check(sections.shape == (nc, H + 1, 2), label + ": section array shape")
        check(bool(np.isfinite(sections).all()) and bool((sections >= 0).all()), label + ": finite nonnegative boxes")
        close(sections[:, 0], np.zeros((nc, 2)), label + ": S_0 = {0}", 0, 0)
        margins = np.array([[atlas.charts[i].S[t+1]
            - np.abs(np.linalg.matrix_power(plant.AK, t)) @ atlas.charts[i].S[1]
            - atlas.charts[j].S[t]
            for i in range(nc) for j in range(nc)] for t in range(H)])
        derived = (margins.min(axis=(0, 2)) >= -1e-10).reshape(nc, nc)
        check(bool(np.array_equal(derived, atlas.edges)), label + ": recomputed edge matrix")
        audit = record["audit"]
        check(int((margins < -1e-10).sum()) == audit["failed_scalar_cross_section_inequalities"],
              label + ": scalar inclusion-failure count")
        check(int(derived.sum()) == audit["verified_edge_pairs"], label + ": edge count")
        if record["name"] != "noedge":
            check(bool(derived.all()), label + ": all claimed transitions verified")
        else:
            check(not bool(derived.any()), label + ": expected no-edge diagnostic failures retained")

        # Re-evaluate the terminal parallelogram's support inequalities using
        # its stored matrix; this does not depend on eigensolver sign choices.
        F, b = atlas.terminal_F, atlas.terminal_b
        transform = F[:2]
        inverse = np.linalg.inv(transform)
        radius = b[0]
        close(F[2:], -transform, label + ": terminal opposite facets")
        close(b, np.full(4, radius), label + ": terminal common radius")
        s1, sH, sHm = sections[:, 1].max(axis=0), sections[:, -1].max(axis=0), sections[:, -2].max(axis=0)
        terminal_invariance = radius - (
            np.abs(transform @ plant.AK @ inverse).sum(axis=1)*radius
            + np.abs(transform @ np.linalg.matrix_power(plant.AK, H)) @ s1)
        terminal_state = plant.xmax - (np.abs(inverse).sum(axis=1)*radius + sH)
        terminal_input = plant.umax - (
            np.abs(plant.K @ inverse).sum()*radius
            + (np.abs(plant.K @ np.linalg.matrix_power(plant.AK, H-1)) @ s1).item()
            + (np.abs(plant.K) @ sHm).item())
        check(float(terminal_invariance.min()) >= -1e-10, label + ": terminal robust invariance")
        check(float(terminal_state.min()) >= -1e-10, label + ": terminal state inclusion")
        check(float(terminal_input) >= -1e-10, label + ": terminal input inclusion")
        close(terminal_invariance.min(), audit["terminal_invariance_slack_min"], label + ": recorded invariance slack")
        close(terminal_state.min(), audit["terminal_state_slack_min"], label + ": recorded terminal state slack")
        close(terminal_input, audit["terminal_input_slack_min"], label + ": recorded terminal input slack")

        # Check each charged calibration risk against the stated binomial bound.
        for i, c in enumerate(atlas.charts):
            confidence = .001 / nc
            dim = 2*H
            if record["name"] == "bonferroni":
                confidence /= dim
                charge = dim * beta_dist.ppf(1-confidence, c.discards+1, c.count-c.discards)
            elif record["name"] == "scenario":
                charge = beta_dist.ppf(1-confidence, dim, c.count-dim+1)
            else:
                factor = plant.gamma if record["name"] == "shift_corrected" else 1.0
                charge = min(1.0, factor * beta_dist.ppf(1-confidence, c.discards+1, c.count-c.discards))
            close(c.risk, charge, f"{label}: chart {i} exact risk charge", atol=2e-12)
        if audit.get("construction") == "compatibility_first":
            thresholds = audit["context_thresholds"]
            rho = max(thresholds)
            close(rho, audit["common_scale"], label + ": maximum calibrated common scale")
            close(sections, rho*np.asarray(audit["template_sections"]), label + ": common scaling of compatible templates")

        spath = apath.with_name(apath.name.replace("_atlas.json", "_summary.json"))
        mpath = apath.with_name(apath.name.replace("_atlas.json", "_missions.csv"))
        if not (spath.exists() and mpath.exists()):
            check(False, label + ": missing mission log or summary")
            continue
        summary = load_json(spath)
        frame = pd.read_csv(mpath)
        missions += 1
        rows_checked += len(frame)
        T = summary["T"]
        J = core.reserves(atlas, T)
        if record["reserve"] is not None:
            close(np.asarray(record["reserve"]), J, label + ": continuation reserve recursion")
        feasible = frame[frame["mode"].isin(["certified_reset", "recovery"])].copy()
        check(len(feasible) == summary["steps"], label + ": executed step count")
        check(int((feasible.groupby("mission").size() == T).sum()) == summary["completed_missions"],
              label + ": completed missions")
        for mode, key in (("budget_rejection", "budget_rejections"), ("budget_exhaustion", "budget_exhaustions"),
                          ("initial_state_rejection", "state_rejections")):
            check(int((frame["mode"] == mode).sum()) == summary[key], label + ": " + key)
        if feasible.empty:
            continue
        for _, group in frame.groupby("mission"):
            good = group[group["mode"].isin(["certified_reset", "recovery"])]
            if len(good) > 1:
                close(good[["next_x0", "next_x1"]].values[:-1], good[["x0", "x1"]].values[1:], label + ": state continuity")
                close(good.budget_after.values[:-1], good.budget_before.values[1:], label + ": budget continuity")
            if len(good):
                close(good.budget_before.iloc[0], summary["epsilon"], label + ": initial budget")
        close(feasible.budget_after.values, feasible.budget_before.values - feasible.risk.values,
              label + ": charged budget updates")
        check(float(feasible.budget_after.min()) >= -1e-12, label + ": nonnegative budgets")
        recovery = feasible["mode"].eq("recovery").values
        idx = feasible.chart.to_numpy(dtype=int)
        charges = np.array([atlas.charts[i].risk for i in idx])
        close(feasible.risk.values, np.where(recovery, 0.0, charges), label + ": statistical charging stops in recovery")
        remaining = T-feasible.k.to_numpy(dtype=int)-1
        if record["name"] != "noedge":
            close(feasible.reserve.values, J[remaining, idx], label + ": logged continuation reserves")
        if summary["reserve_enforced"]:
            ok = ~recovery
            slack = feasible.budget_before.values[ok] - charges[ok] - J[remaining[ok], idx[ok]]
            check(float(slack.min()) >= -1e-12, label + ": reserve guard")
        xx = feasible[["x0", "x1"]].to_numpy()
        xp = feasible[["next_x0", "next_x1"]].to_numpy()
        uu = feasible.u.to_numpy()
        yy = feasible[["nominal_x0", "nominal_x1"]].to_numpy()
        close(xx[~recovery], yy[~recovery], label + ": measured-state initialization")
        close(feasible.stage_cost.values, np.einsum("ni,ij,nj->n", xx, plant.Q, xx) + plant.R*uu**2,
              label + ": realized stage costs")
        close(feasible.state_tightening.values, np.mean(sections[idx, 1:] / plant.xmax, axis=(1, 2)),
              label + ": selected-chart state tightening")
        close(feasible.input_tightening.values,
              np.mean(sections[idx, :-1] @ np.abs(plant.K).ravel()/plant.umax, axis=1),
              label + ": selected-chart input tightening")
        state_flags = np.any(np.abs(xp) > plant.xmax + 1e-7, axis=1).astype(int)
        input_flags = (np.abs(uu) > plant.umax + 1e-7).astype(int)
        check(bool(np.array_equal(state_flags, feasible.state_violation.values)), label + ": physical state flags")
        check(bool(np.array_equal(input_flags, feasible.input_violation.values)), label + ": physical input flags")
        check(bool((feasible.nominal_feasible == 1).all()), label + ": nominal QP success flags")
        check(summary["max_qp_constraint_violation"] <= 2e-7, label + ": accepted QP primal tolerance")
        check(set(summary["accepted_optimizer_statuses"]) <= {"0"}, label + ": accepted optimizer status")
        totals = feasible.groupby("mission").risk.sum()
        recomputed = {
            "cost_mean": feasible.groupby("mission").stage_cost.sum().mean(),
            "horizon_escape_pct": 100*feasible.horizon_escape.mean(),
            "first_escape_count": feasible.first_escape.sum(),
            "state_violation_count": feasible.state_violation.sum(),
            "input_violation_count": feasible.input_violation.sum(),
            "reset_failure_count": feasible.reset_failed.sum(),
            "backup_steps": int(recovery.sum()),
            "risk_spent_min": totals.min(), "risk_spent_max": totals.max(),
            "budget_final_min": summary["epsilon"]-totals.max(),
            "state_tightening_pct": 100*feasible.state_tightening.mean(),
            "input_tightening_pct": 100*feasible.input_tightening.mean(),
        }
        for key, value in recomputed.items():
            close(value, summary[key], label + ": summary from logs: " + key)

        # Regenerate the exact primitive stream and verify each actual transition.
        if parts[0] == "A":
            seed = int(parts[1].removeprefix("seed_"))+5100
        elif parts[0] == "B":
            seed = 105100
        elif parts[0] == "budget":
            seed = 9100 if mpath.name.startswith("reserve_contextual") else 10100
        else:
            seed = 11100
        modes, eta, mix = core.paths(plant, summary["missions"], seed, None, T+H)
        mi = feasible.mission.to_numpy(dtype=int)
        ki = feasible.k.to_numpy(dtype=int)
        gg = feasible.g.to_numpy(dtype=int)
        check(bool(np.array_equal(gg, modes[mi, ki])), label + ": exogenous regime stream")
        noise = np.einsum("nij,nj->ni", plant.L[gg], eta[mi, ki]) + plant.means[gg]
        if plant.alpha0:
            alpha = plant.alpha0*(1+(plant.gamma**(1/H)-1)*np.tanh(
                (xx[:,0]/2)**2+(xx[:,1]/1.5)**2+(uu/2)**2))
            noise *= np.where(mix[mi, ki] < alpha, plant.heavy_scale, 1)[:,None]
        if parts[0] == "recovery":
            noise[ki == 3] += np.array([6.5, 3.0])
        close(xp, xx @ plant.A.T + uu[:,None]*plant.B.ravel() + noise, label + ": dynamics driven by recorded seeds")
        first = np.any(np.abs(noise) > sections[idx, 1] + 1e-10, axis=1).astype(int)
        check(bool(np.array_equal(first, feasible.first_escape.values)), label + ": first-error escape flags")

    # Recompute the stationary-weighted feasibility percentages from the LP masks.
    grid_summary = results / "feasible_grid/summary.json"
    if grid_summary.exists():
        weights = core.stationary(core.make_plant("A").transition)
        for summary in load_json(grid_summary):
            table = pd.read_csv(results / "feasible_grid" / (summary["method"] + ".csv"))
            columns = ["context_0", "context_1", "context_2"]
            # Preserve the explicit column names used by the original grid writer.
            if not all(c in table for c in columns):
                columns = [c for c in table if c.startswith("feasible_g")]
            check(len(columns) == 3, "Grid masks: three context columns")
            if len(columns) == 3:
                rates = 100*table[columns].mean().to_numpy()
                close(rates, summary["context_feasible_pct"], "Grid: context feasibility percentages")
                close(float(weights @ rates), summary["weighted_feasible_pct"], "Grid: stationary-weighted feasibility")

    mixture = results / "mixture_diagnostic.json"
    if mixture.exists():
        data = load_json(mixture)
        weights = np.asarray(data["initial_mode_weights"])
        close(weights.sum(), 1.0, "Mixture: normalized stationary weights")
        close(float(weights @ np.asarray(data["conditional_escape_rates"])),
              data["mixture_weighted_test_rate"], "Mixture: weighted conditional test rate")
        check(data["mixture_certificate"] <= .004, "Mixture: reference-law certificate")
    sweep_path = results / "B/shift_sweep.csv"
    if sweep_path.exists():
        sweep = pd.read_csv(sweep_path)
        for row in sweep.to_dict("records"):
            minimum = int(np.ceil(np.log(.001/2)/np.log1p(-.004/row["Gamma"])))
            check(minimum == row["minimum_calibration_samples"], "B sweep: minimum calibration sample count")
            if row["status"] == "sample_rejected":
                check(minimum > 50000, "B sweep: reason for sample rejection")
                check(pd.isna(row["corrected_test_pct"]), "B sweep: rejected design has no corrected performance")
            else:
                check(minimum <= 50000, "B sweep: sample-admissible corrected design")
                check(row["risk_spent"] <= .1+1e-12, "B sweep: corrected mission budget")
    check(checks > 0, "No auditable scientific outputs found")
    return {"ok": not errors, "checks": checks, "atlases_checked": atlases,
            "mission_logs_checked": missions, "rows_checked": rows_checked,
            "errors": errors}
