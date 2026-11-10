"""Prove that a hardware variant of the housing leaves its exterior untouched."""

from __future__ import annotations

import manifold3d as md
import numpy as np
import trimesh


def surface(m: md.Manifold) -> trimesh.Trimesh:
    mesh = m.to_mesh64()
    return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=False)


def solid(m: md.Manifold) -> md.Manifold:
    return md.Manifold.batch_boolean([p for p in m.decompose() if p.volume() > 1e-3], md.OpType.Add)


def exposed_changes(
    stock: list[md.Manifold],
    variant: list[md.Manifold],
    occluders: list[md.Manifold],
    *,
    density: float = 4.0,
) -> dict[str, object]:
    """Changed faces of each part that face open air outside the assembled housing.

    Per part, material the variant removes (stock minus variant) and adds (variant minus stock) is sampled `density`
    points per mm^2, dropping zero-volume boolean slivers. A removed piece's samples on the stock surface are stock
    faces it takes away; an added piece's samples on the variant surface are faces it creates. Such a face is exterior
    when its outward normal ray leaves that assembly (every part plus `occluders`) without hitting anything.
    """
    scenes = {id(parts): trimesh.util.concatenate([surface(m) for m in (*parts, *occluders)]) for parts in (stock, variant)}
    report: dict[str, object] = {"removed_mm3": 0.0, "added_mm3": 0.0}
    sampled = exterior = 0
    points_out: list[list[float]] = []
    for s, v in zip(stock, variant):
        for key, change, owner, parts in (("removed_mm3", s - v, s, stock), ("added_mm3", v - s, v, variant)):
            change = solid(change)
            if change.is_empty():
                continue
            report[key] = round(float(report[key]) + change.volume(), 4)
            mesh = surface(change)
            points, faces = trimesh.sample.sample_surface(mesh, int(np.ceil(mesh.area * density)), seed=0)
            _, distance, _ = trimesh.proximity.closest_point(surface(owner), points)
            on_face = distance < 1e-3
            normals = mesh.face_normals[faces][on_face]
            escapes = ~scenes[id(parts)].ray.intersects_any(points[on_face] + normals * 0.01, normals)
            sampled += int(on_face.sum())
            exterior += int(escapes.sum())
            points_out += np.round(points[on_face][escapes][:5], 2).tolist()
    report.update({"changed_face_samples": sampled, "exterior_samples": exterior, "exterior_sample_points": points_out})
    return report
