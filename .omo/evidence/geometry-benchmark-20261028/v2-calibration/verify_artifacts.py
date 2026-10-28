"""Read-only integrity, quadrature and persisted-metric checks for this trial."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
import trimesh

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quadrature_moments(mesh):
    # Symmetric three-point triangle quadrature is exact for degree-two terms.
    barycentric = np.full((3, 3), 1 / 6)
    np.fill_diagonal(barycentric, 2 / 3)
    locations = np.einsum("qv,nvd->nqd", barycentric, mesh.triangles)
    area = mesh.area_faces
    center = np.sum(area[:, None] * locations.mean(axis=1), axis=0) / area.sum()
    second = float(np.sum(area * np.sum(locations ** 2, axis=2).mean(axis=1)) / area.sum())
    return center, np.sqrt(second - center @ center)


def main():
    report = json.loads((OUT / "report.json").read_text())
    protocol = json.loads((OUT / "protocol.json").read_text())
    execution = json.loads((OUT / "execution.json").read_text())
    calibration = json.loads((OUT / "calibration.json").read_text())
    assert sha(OUT / "protocol.json") == execution["protocol_sha256"] == report["protocol_sha256"]
    assert sha(OUT / "benchmark.py") == execution["script_sha256"] == report["script_sha256"]
    predecessor = json.loads((OUT.parent / "manifest.json").read_text())
    for entry in predecessor["entries"]:
        path = OUT.parent / entry["path"]
        assert path.stat().st_size == entry["bytes"] and sha(path) == entry["sha256"]
    for item in protocol["source_files"].values():
        assert sha(ROOT / item["path"]) == item["sha256"]
    assert calibration["all_gate_pass"]
    for case in calibration["cases"].values():
        assert case["analytic_invariance"]["pass"] and case["gate"]["pass_gate"]
        assert case["surface_metrics"]["CD_mean_sq"] <= case["gate"]["maximum_CD_mean_sq"]
    pngs = sorted(OUT.rglob("*.png"))
    for path in pngs:
        with Image.open(path) as im:
            im.load()
            assert im.size == ((1160, 1220) if path.name == "comparison.png" else (512, 512))
    jsons = sorted(OUT.rglob("*.json"))
    for path in jsons:
        json.loads(path.read_text())
    module_spec = importlib.util.spec_from_file_location("geometry_v2_trial", OUT / "benchmark.py")
    trial = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(trial)
    metrics, reference_rasters, quadrature = {}, {}, {}
    for name, body in report["cases"].items():
        reference_rasters[name] = {}
        for view in body["conditions"]["A_normalized_raw_basis"]["views"]:
            current = np.asarray(Image.open(OUT / name / "groundtruth" / (view + ".png")))
            original = np.asarray(Image.open(OUT.parent / name / "groundtruth" / (view + ".png")))
            different = int(np.count_nonzero(current != original))
            assert different == 0
            reference_rasters[name][view] = different
        scene = json.loads((ROOT / protocol["source_files"][name + "_scene"]["path"]).read_text())
        reference_mesh, _ = trial.union_boxes(scene)
        raw_mesh = trimesh.load(ROOT / protocol["source_files"][name + "_raw"]["path"], force="mesh", process=False)
        quadrature[name] = {}
        for role, mesh in [("reference", reference_mesh), ("prediction", raw_mesh)]:
            center, radius = quadrature_moments(mesh)
            expected = body["normalization"][role + "_moments"]
            center_error = float(np.max(np.abs(center - expected["centroid"])))
            radius_error = float(abs(radius - expected["rms_radius"]))
            assert center_error < 1e-12 and radius_error < 1e-12
            quadrature[name][role] = dict(centroid_max_abs_error=center_error, radius_abs_error=radius_error)
        with np.load(OUT / name / "sampled-points.npz", allow_pickle=False) as data:
            g, p, pr = [data[key] for key in ["reference_evaluation", "prediction_evaluation", "registered_prediction_evaluation"]]
            assert g.shape == p.shape == pr.shape == (20000, 3)
            assert np.isfinite(g).all() and np.isfinite(p).all() and np.isfinite(pr).all()
            selected = body["registration"]["candidates"][body["registration"]["selected_candidate"]]
            transform = np.asarray(selected["transform"])
            assert np.allclose(pr, p @ transform[:3, :3].T + transform[:3, 3], atol=1e-12)
            assert np.allclose(np.linalg.svd(transform[:3, :3])[1], [1, 1, 1], atol=1e-8)
            assert np.isclose(np.linalg.det(transform[:3, :3]), 1, atol=1e-8)
            metrics[name] = {}
            for condition, cloud in [("A_normalized_raw_basis", p), ("B_groundtruth_assisted_registration", pr)]:
                ab, ba = cKDTree(g).query(cloud, workers=1)[0], cKDTree(cloud).query(g, workers=1)[0]
                value = float(np.mean(ab ** 2) + np.mean(ba ** 2))
                assert abs(value - body["conditions"][condition]["surface_metrics"]["CD_mean_sq"]) < 1e-12
                metrics[name][condition] = value
    print(json.dumps(dict(status="pass", v1_manifest_entries_preserved=len(predecessor["entries"]),
                         protocol_and_script_before_after_matched=True, calibration_gate_passed_before_raw=True,
                         png_decoded=len(pngs), json_parsed=len(jsons), analytic_moments_quadrature_crosscheck=quadrature,
                         source_reference_raster_changed_pixels=reference_rasters,
                         persisted_pointcloud_metrics_recomputed=metrics,
                         scope="Evidence integrity/calibration only; not real-user, model execution, appearance, commercial parity or whole-platform acceptance.")))


if __name__ == "__main__":
    main()
