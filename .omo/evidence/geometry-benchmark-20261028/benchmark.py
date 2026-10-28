"""Offline geometry diagnostics under the frozen protocol; never model inference."""
from pathlib import Path
import datetime
import hashlib
import itertools
import json
import math
import os
import resource
import socket
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
import trimesh
from trimesh.registration import icp

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PROTOCOL = json.loads((OUT / "protocol.json").read_text())
STARTED = time.monotonic()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def union_boxes(scene):
    """Exact boundary for these axis-aligned boxes, with no hidden internal faces."""
    bounds = []
    for obj in scene["objects"]:
        assert obj["kind"] == "cube" and obj["rotation_degrees"] == [0, 0, 0]
        center, half = np.asarray(obj["position"]), np.asarray(obj["scale"])
        bounds.append(np.array([center - half, center + half]))
    coordinates = [np.unique(np.round(np.array(bounds)[:, :, axis], 12)) for axis in range(3)]
    shape = tuple(len(axis) - 1 for axis in coordinates)
    occupied = np.zeros(shape, dtype=bool)
    for cell in np.ndindex(shape):
        mid = np.array([(axis[i] + axis[i + 1]) / 2 for axis, i in zip(coordinates, cell)])
        occupied[cell] = any(np.all(mid > box[0]) and np.all(mid < box[1]) for box in bounds)
    vertices, faces, vertex_ids, volume = [], [], {}, 0.0
    directions = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]
    for cell in np.ndindex(shape):
        if not occupied[cell]:
            continue
        x, y, z = [(axis[i], axis[i + 1]) for axis, i in zip(coordinates, cell)]
        volume += (x[1] - x[0]) * (y[1] - y[0]) * (z[1] - z[0])
        quads = [
            [(x[0], y[0], z[0]), (x[0], y[0], z[1]), (x[0], y[1], z[1]), (x[0], y[1], z[0])],
            [(x[1], y[0], z[0]), (x[1], y[1], z[0]), (x[1], y[1], z[1]), (x[1], y[0], z[1])],
            [(x[0], y[0], z[0]), (x[1], y[0], z[0]), (x[1], y[0], z[1]), (x[0], y[0], z[1])],
            [(x[0], y[1], z[0]), (x[0], y[1], z[1]), (x[1], y[1], z[1]), (x[1], y[1], z[0])],
            [(x[0], y[0], z[0]), (x[0], y[1], z[0]), (x[1], y[1], z[0]), (x[1], y[0], z[0])],
            [(x[0], y[0], z[1]), (x[1], y[0], z[1]), (x[1], y[1], z[1]), (x[0], y[1], z[1])],
        ]
        for direction, quad in zip(directions, quads):
            neighbor = tuple(i + offset for i, offset in zip(cell, direction))
            inside = all(0 <= i < n for i, n in zip(neighbor, shape))
            if inside and occupied[neighbor]:
                continue
            indices = []
            for point in quad:
                if point not in vertex_ids:
                    vertex_ids[point] = len(vertices)
                    vertices.append(point)
                indices.append(vertex_ids[point])
            faces.extend([[indices[0], indices[1], indices[2]], [indices[0], indices[2], indices[3]]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    details = dict(primitive_count=len(bounds), grid_shape=list(shape), occupied_cells=int(occupied.sum()),
                   vertices=len(mesh.vertices), faces=len(mesh.faces), bounds=mesh.bounds.tolist(),
                   area=float(mesh.area), occupancy_volume=float(volume), mesh_signed_volume=float(mesh.volume),
                   watertight=bool(mesh.is_watertight))
    assert np.isclose(mesh.volume, volume, atol=1e-10) and mesh.is_watertight
    return mesh, details


def normalize(mesh):
    center = mesh.bounds.mean(axis=0)
    maximum = float(np.max(mesh.extents))
    matrix = np.eye(4)
    matrix[:3, :3] /= maximum
    matrix[:3, 3] = -center / maximum
    result = mesh.copy()
    result.apply_transform(matrix)
    return result, matrix


def points(mesh, count, seed):
    return trimesh.sample.sample_surface(mesh, count=count, seed=seed)[0]


def distance(a, b):
    ab = cKDTree(b).query(a, workers=1)[0]
    ba = cKDTree(a).query(b, workers=1)[0]
    result = {}
    for key, values in [("prediction_to_reference", ab), ("reference_to_prediction", ba)]:
        result[key] = dict(mean=float(values.mean()), mean_sq=float(np.mean(values ** 2)),
                           rms=float(np.sqrt(np.mean(values ** 2))), p95=float(np.quantile(values, 0.95)))
    result["CD_mean_sq"] = float(np.mean(ab ** 2) + np.mean(ba ** 2))
    result["sampled_CD_sum_sq"] = float(np.sum(ab ** 2) + np.sum(ba ** 2))
    return result


def register(prediction, reference):
    cfg = PROTOCOL["registration"]
    p = points(prediction, cfg["fit_samples_per_shape"], cfg["prediction_seed"])
    g = points(reference, cfg["fit_samples_per_shape"], cfg["groundtruth_seed"])
    candidates = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            rotation = np.eye(3)[list(permutation)] * np.asarray(signs)[:, None]
            if not np.isclose(np.linalg.det(rotation), 1):
                continue
            initial = np.eye(4)
            initial[:3, :3] = rotation
            matrix, transformed, cost = icp(p, g, initial=initial, **cfg["icp"])
            score = distance(transformed, g)["CD_mean_sq"]
            assert np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-8)
            assert np.isclose(np.linalg.det(matrix[:3, :3]), 1, atol=1e-8)
            candidates.append(dict(index=len(candidates), initial=initial.tolist(), transform=matrix.tolist(),
                                   fit_CD_mean_sq=score, icp_one_direction_cost=float(cost)))
    assert len(candidates) == 24
    selected = min(candidates, key=lambda item: (item["fit_CD_mean_sq"], item["index"]))
    return np.asarray(selected["transform"]), dict(selected_candidate=selected["index"], candidates=candidates,
                                                  selected_fit_CD_mean_sq=selected["fit_CD_mean_sq"]), p, g


def cameras(scene, reference_normalization):
    camera = scene["camera"]
    position = np.asarray(camera["position"], dtype=float)
    target = np.asarray(camera["target"], dtype=float)
    radius = float(np.linalg.norm((position - target)[:2]))
    height = float(position[2] - target[2])
    positions = [("input", position), ("front_minus_y", target + [0, -radius, height]),
                 ("right_plus_x", target + [radius, 0, height]),
                 ("rear_plus_y", target + [0, radius, height]), ("left_minus_x", target + [-radius, 0, height])]
    target_n = trimesh.transform_points([target], reference_normalization)[0]
    return [dict(id=key, position=trimesh.transform_points([value], reference_normalization)[0].tolist(),
                 target=target_n.tolist(), lens_mm=camera["lens_mm"], width=scene["width"], height=scene["height"])
            for key, value in positions]


def silhouette(mesh, camera):
    position, target = np.asarray(camera["position"]), np.asarray(camera["target"])
    forward = target - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    rel = mesh.vertices - position
    depth = rel @ forward
    assert depth.min() > 1e-6, "near-plane clipping invalidates this diagnostic"
    tangent = 36 / (2 * camera["lens_mm"])
    w, h, ss = camera["width"], camera["height"], PROTOCOL["views"]["supersample"]
    pixels = np.stack([w * (0.5 + (rel @ right) / (2 * depth * tangent)),
                       h * (0.5 - (rel @ up) / (2 * depth * tangent))], axis=-1)
    bbox = np.array([pixels.min(axis=0), pixels.max(axis=0)])
    clipped = bool(np.any(bbox[0] <= 0) or bbox[1, 0] >= w - 1 or bbox[1, 1] >= h - 1)
    assert not clipped, "framing clipping invalidates this diagnostic"
    high = Image.new("L", (w * ss, h * ss), 0)
    draw = ImageDraw.Draw(high)
    for triangle in (pixels * ss)[mesh.faces]:
        draw.polygon([tuple(point) for point in triangle], fill=255)
    mask = np.asarray(high.resize((w, h), Image.Resampling.LANCZOS)) >= 128
    return mask, dict(projected_bbox=bbox.tolist(), minimum_depth=float(depth.min()), clipped=clipped)


def iou(a, b):
    intersection, union = int(np.logical_and(a, b).sum()), int(np.logical_or(a, b).sum())
    return dict(intersection_pixels=intersection, union_pixels=union, iou=intersection / union)


def difference_image(reference, prediction):
    value = np.full((*reference.shape, 3), 247, dtype=np.uint8)
    value[reference & prediction] = (36, 142, 80)
    value[reference & ~prediction] = (40, 91, 210)
    value[~reference & prediction] = (224, 108, 41)
    return Image.fromarray(value)


def contact_sheet(case, view_ids):
    tile, label_width, row_height = 200, 160, 235
    rows = ["groundtruth", "A_normalized_raw_basis", "B_groundtruth_assisted_registration", "A_difference", "B_difference"]
    sheet = Image.new("RGB", (label_width + tile * len(view_ids), 45 + row_height * len(rows)), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 5), case + " | geometry-only; raw basis / one GT-assisted transform", fill="black")
    draw.text((10, 20), "Difference: green=both; blue=reference only; orange=prediction only", fill="black")
    for row_index, row in enumerate(rows):
        y = 45 + row_index * row_height
        draw.text((5, y + 30), row[:22], fill="black")
        if len(row) > 22:
            draw.text((5, y + 45), row[22:44], fill="black")
        for column, view in enumerate(view_ids):
            path = OUT / case / row / (view + ".png")
            image = Image.open(path).convert("RGB").resize((tile, tile), Image.Resampling.NEAREST)
            sheet.paste(image, (label_width + column * tile, y + 20))
            draw.text((label_width + column * tile + 5, y + 5), view, fill="black")
    sheet.save(OUT / case / "comparison.png")


def geometry_controls():
    def box(x):
        return dict(id=str(x), kind="cube", position=[x, 0, 0], scale=[0.5] * 3, rotation_degrees=[0, 0, 0])
    duplicate, dd = union_boxes(dict(objects=[box(0), box(0)]))
    overlap, od = union_boxes(dict(objects=[box(0), box(0.5)]))
    assert np.isclose(dd["area"], 6) and np.isclose(dd["occupancy_volume"], 1)
    assert np.isclose(od["area"], 8) and np.isclose(od["occupancy_volume"], 1.5)
    return dict(duplicate_cube=dd, overlapping_cubes=od)


def case_run(case):
    print("CASE", case, "start", round(time.monotonic() - STARTED, 3), flush=True)
    source = PROTOCOL["source_files"]
    scene = json.loads((ROOT / source[case + "_scene"]["path"]).read_text())
    reference_raw, reference_info = union_boxes(scene)
    reference, reference_matrix = normalize(reference_raw)
    raw = trimesh.load(ROOT / source[case + "_raw"]["path"], force="mesh", process=False)
    prediction, prediction_matrix = normalize(raw)
    assert np.isfinite(raw.vertices).all() and len(raw.faces) > 0
    transform, registration, fit_p, fit_g = register(prediction, reference)
    registered = prediction.copy()
    registered.apply_transform(transform)
    evaluation = PROTOCOL["evaluation"]
    g = points(reference, evaluation["samples_per_shape"], evaluation["groundtruth_seed"])
    p = points(prediction, evaluation["samples_per_shape"], evaluation["prediction_seed"])
    p_registered = trimesh.transform_points(p, transform)
    independent_self = points(reference, evaluation["samples_per_shape"], evaluation["prediction_seed"])
    exact_self = distance(g, g)
    assert exact_self["CD_mean_sq"] == 0
    conditions = [("A_normalized_raw_basis", prediction, p), ("B_groundtruth_assisted_registration", registered, p_registered)]
    cameras_fixed = cameras(scene, reference_matrix)
    results = {}
    frame_controls = {}
    for key, mesh, cloud in conditions:
        result = dict(surface_metrics=distance(cloud, g), views={})
        for camera in cameras_fixed:
            name = camera["id"]
            gt_mask, gt_frame = silhouette(reference, camera)
            pred_mask, pred_frame = silhouette(mesh, camera)
            for row, mask in [("groundtruth", gt_mask), (key, pred_mask)]:
                path = OUT / case / row / (name + ".png")
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray((mask * 255).astype(np.uint8)).save(path)
            error_row = "A_difference" if key.startswith("A_") else "B_difference"
            ep = OUT / case / error_row / (name + ".png")
            ep.parent.mkdir(parents=True, exist_ok=True)
            difference_image(gt_mask, pred_mask).save(ep)
            result["views"][name] = dict(**iou(gt_mask, pred_mask), reference_framing=gt_frame, prediction_framing=pred_frame)
            frame_controls[name] = iou(gt_mask, gt_mask)
            assert frame_controls[name]["iou"] == 1
        results[key] = result
    # The known-transform test intentionally retains the frozen AABB/maxside rule.
    known = trimesh.transformations.rotation_matrix(math.radians(37), [1, 2, 3])
    known[:3, :3] *= 1.7
    known[:3, 3] = [0.3, -0.4, 0.2]
    altered = reference_raw.copy()
    altered.apply_transform(known)
    altered_n, altered_n_matrix = normalize(altered)
    known_fit, known_registration, _, _ = register(altered_n, reference)
    kp = points(altered_n, evaluation["samples_per_shape"], evaluation["prediction_seed"])
    kp = trimesh.transform_points(kp, known_fit)
    known_distance = distance(kp, g)
    original_points = points(reference_raw, 1000, 777)
    roundtrip = trimesh.transform_points(trimesh.transform_points(original_points, known), np.linalg.inv(known))
    roundtrip_max = float(np.max(np.abs(roundtrip - original_points)))
    assert roundtrip_max < 1e-10
    known_control = dict(transform=known.tolist(), normalization=altered_n_matrix.tolist(),
                         registration=known_registration, surface_metrics=known_distance,
                         inverse_algebra_max_abs_error=roundtrip_max,
                         interpretation="Residual error is retained: maxside AABB normalization is rotation dependent and ICP scale remains disabled. This is not an invariance pass.")
    negative = None
    if case == "chair":
        missing_scene = dict(objects=[x for x in scene["objects"] if x["id"] != "backrest"])
        missing, missing_info = union_boxes(missing_scene)
        missing.apply_transform(reference_matrix)
        missing_points = points(missing, evaluation["samples_per_shape"], evaluation["prediction_seed"])
        negative = dict(kind="synthetic_reference_backrest_removed_not_AI", geometry=missing_info,
                        surface_metrics=distance(missing_points, g), views={})
        for camera in cameras_fixed:
            gt_mask, _ = silhouette(reference, camera)
            missing_mask, _ = silhouette(missing, camera)
            negative["views"][camera["id"]] = iou(gt_mask, missing_mask)
        assert negative["surface_metrics"]["CD_mean_sq"] > 0
        assert min(x["iou"] for x in negative["views"].values()) < 1
    output = dict(reference_geometry=reference_info,
                  raw_prediction_geometry=dict(vertices=len(raw.vertices), faces=len(raw.faces), bounds=raw.bounds.tolist()),
                  normalization=dict(reference=reference_matrix.tolist(), prediction=prediction_matrix.tolist()),
                  registration=registration, registered_total_raw_to_reference_normalized=(transform @ prediction_matrix).tolist(),
                  cameras=cameras_fixed, conditions=results,
                  controls=dict(exact_same_pointcloud=exact_self, independent_seed_reference_floor=distance(independent_self, g),
                                identical_silhouettes=frame_controls, known_transform=known_control, negative=negative))
    np.savez_compressed(OUT / case / "sampled-points.npz", reference_evaluation=g, prediction_evaluation=p,
                        registered_prediction_evaluation=p_registered, reference_registration=fit_g, prediction_registration=fit_p)
    write(case + "/results.json", output)
    contact_sheet(case, [camera["id"] for camera in cameras_fixed])
    print("CASE", case, "complete", round(time.monotonic() - STARTED, 3), flush=True)
    return output


def main():
    assert not (OUT / "report.json").exists(), "Single-run evidence already exists"
    for item in PROTOCOL["source_files"].values():
        assert sha(ROOT / item["path"]) == item["sha256"]
    network_probe = None
    try:
        with socket.socket() as probe:
            probe.connect(("127.0.0.1", 9))
    except PermissionError as exc:
        network_probe = dict(os_network_denied=True, exception=type(exc).__name__, errno=exc.errno)
    assert network_probe and network_probe["os_network_denied"], "Network sandbox not verified"
    controls = geometry_controls()
    result = {case: case_run(case) for case in ["cube", "chair"]}
    preserved = {key: sha(ROOT / value["path"]) == value["sha256"] for key, value in PROTOCOL["source_files"].items()}
    assert all(preserved.values())
    report = dict(schema="loretune-offline-geometry-results/1", completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  protocol_sha256=sha(OUT / "protocol.json"), script_sha256=sha(__file__),
                  elapsed_seconds=time.monotonic() - STARTED, peak_rss_native_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  platform=sys.platform, environment_keys=sorted(os.environ), network_probe=network_probe,
                  source_hashes_preserved=preserved, construction_controls=controls, cases=result,
                  measured="Conditional synthetic geometry diagnostics only; visual image review is separate and pending.",
                  raw_commercial_comparison=False, model_inference_calls=0, provider_calls=0, product_changes=0,
                  shape_normalization_warning="AABB/maxside is rotation dependent; no post-result normalization change was made.",
                  canonical_input_pose_recovered=False, commercial_open_quality_equivalence_proven=False)
    write("report.json", report)
    print("DONE", report["elapsed_seconds"], flush=True)


if __name__ == "__main__":
    main()
