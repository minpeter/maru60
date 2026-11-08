"""Shared print mesh export and geometry checks; units are millimetres."""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import manifold3d as md
import numpy as np
import shapely.geometry as sg
import trimesh

FINE_LAYER_Z = (5.40, 10.00)
FINE_LAYER_H = 0.10


def write_3mf(
    path: Path,
    title: str,
    named_meshes: list[tuple[str, trimesh.Trimesh]],
    fine_layer_z: tuple[float, float] | None = FINE_LAYER_Z,
) -> None:
    model = ET.Element(
        "model",
        {
            "unit": "millimeter",
            "xmlns": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
        },
    )
    ET.SubElement(model, "metadata", {"name": "Title"}).text = title
    ET.SubElement(model, "metadata", {"name": "Designer"}).text = "minpeter"
    ET.SubElement(
        model, "metadata", {"name": "License"}
    ).text = "CC BY-NC 4.0 (non-commercial use only) — https://creativecommons.org/licenses/by-nc/4.0/"
    resources, build = ET.SubElement(model, "resources"), ET.SubElement(model, "build")
    for idx, (name, m) in enumerate(named_meshes, 1):
        obj = ET.SubElement(
            resources, "object", {"id": str(idx), "type": "model", "name": name}
        )
        mesh_el = ET.SubElement(obj, "mesh")
        vs, ts = ET.SubElement(mesh_el, "vertices"), ET.SubElement(mesh_el, "triangles")
        for v in m.vertices:
            _ = ET.SubElement(
                vs,
                "vertex",
                dict(zip(("x", "y", "z"), (f"{float(val):.6f}" for val in v))),
            )
        for f in m.faces:
            _ = ET.SubElement(
                ts, "triangle", dict(zip(("v1", "v2", "v3"), map(str, f)))
            )
        _ = ET.SubElement(build, "item", {"objectid": str(idx)})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "3D/3dmodel.model",
            ET.tostring(model, encoding="utf-8", xml_declaration=True),
        )
        zf.writestr(
            "[Content_Types].xml",
            (
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                "</Types>"
            ),
        )
        zf.writestr(
            "_rels/.rels",
            (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
                "</Relationships>"
            ),
        )
        if fine_layer_z is None:
            return
        # Bambu Studio / Orca height-range modifier on every object: 0.10 mm layers across the strike, cap-pocket and
        # base-pocket floors. With 0.20 mm layers the 6.30 cap floor prints at 6.4 and the 9.69 rim floor at 9.6, so the
        # silicone caps sit 0.19 mm tighter between top and bottom case; at 0.10 mm they print at 6.3 / 9.7 (sliced).
        zf.writestr(
            "Metadata/layer_config_ranges.xml",
            '<?xml version="1.0" encoding="utf-8"?>\n<objects>\n'
            + "".join(
                f' <object id="{idx}">\n  <range min_z="{fine_layer_z[0]}" max_z="{fine_layer_z[1]}">\n'
                '   <option opt_key="extruder">0</option>\n'
                f'   <option opt_key="layer_height">{FINE_LAYER_H}</option>\n  </range>\n </object>\n'
                for idx in range(1, len(named_meshes) + 1)
            )
            + "</objects>\n",
        )


def to_trimesh(m: md.Manifold, *, single_shell: bool = False) -> trimesh.Trimesh:
    # As in the top-case exporter, retain precision at tangent cuts before removing zero-area seam triangles.
    mesh = m.simplify(1e-6).to_mesh64()
    tm = trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=False)
    tm.merge_vertices(digits_vertex=6)
    tm.update_faces(tm.nondegenerate_faces(height=1e-8))
    tm.remove_unreferenced_vertices()
    assert tm.is_watertight and tm.is_winding_consistent, "non-manifold export"
    assert abs(tm.volume - m.volume()) < 1e-3, "export changed solid volume"
    if single_shell:
        assert len(tm.split(only_watertight=False)) == 1, (
            "export changed component count"
        )
    return tm


def slice_material(mf: md.Manifold, z: float) -> sg.base.BaseGeometry:
    rings = [sg.Polygon(p) for p in mf.slice(z).to_polygons() if len(p) >= 3]
    material = sg.Polygon()
    for ring in sorted(rings, key=lambda r: -abs(r.area)):
        material = material.symmetric_difference(ring.buffer(0))
    return material


def to_manifold(tm: trimesh.Trimesh) -> md.Manifold:
    m = tm.copy()
    m.merge_vertices(digits_vertex=5)
    mf = md.Manifold(
        md.Mesh64(
            np.asarray(m.vertices, dtype=np.float64),
            np.asarray(m.faces, dtype=np.uint64),
        )
    )
    assert mf.status() == md.Error.NoError, mf.status()
    return mf
