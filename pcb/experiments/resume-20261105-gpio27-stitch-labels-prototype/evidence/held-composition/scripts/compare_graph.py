from pathlib import Path
import json,collections
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/combined27';a=json.loads((R/'continuation-c782/header/qa/material-graph.json').read_text());b=json.loads((D/'qa/material-graph.json').read_text());u=json.loads((D/'qa/BUILD.json').read_text())['added_GND_stitch_uuid'];assert a['pad_inventory']==b['pad_inventory'];assert a['pad_partitions_by_net']==b['pad_partitions_by_net']
keys=lambda g:{(x,y,l) for x,y,ls in g['direct_edges']for l,area in ls};zs=lambda g:{(z,u)for z,u,area in g['zone_edges']};lost_direct=sorted(keys(a)-keys(b));lost_zone=sorted(zs(a)-zs(b));contacts=[e for e in b['zone_edges']if e[1]==u];roots=b['object_material_roots'][u];assert len(roots)==1;groundpads=[(uid,meta)for uid,meta in b['pad_inventory'].items()if meta['net']=='GND'and b['object_material_roots'][uid]==roots];assert groundpads;layers={b['material_nodes'][e[0]]['layer']for e in contacts};assert layers=={'In1.Cu','In2.Cu'};assert all(b['material_roots'][e[0]]==roots[0]for e in contacts)
r=dict(pad_inventory_equal=True,pad_partitions_equal=True,old_direct_layer_contacts_lost=lost_direct,old_zone_contacts_lost=lost_zone,new_via_zone_contacts=contacts,new_via_object_layers=b['object_nodes_by_layer'][u],new_via_barrel_joins=[x for x in b['barrel_joins']if u in str(x)],new_via_unique_material_root=roots,ground_pad_count_on_same_root=len(groundpads),ground_pad_examples=groundpads[:8],both_planes_and_rooted_ground_joined=True,guard_failures=b['guard_failing_material_edges'],source_sha256=a['board_sha256'],candidate_sha256=b['board_sha256']);(D/'qa/graph-comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))

assert not lost_direct and not lost_zone
for key in ["guard_failing_material_edges","empty_material_layers","multiple_material_islands"]:
 if key in a: assert a[key]==b[key],key
# Exact old contact areas, not just edge presence.
direct=lambda g:{(x,y,l):area for x,y,ls in g["direct_edges"] for l,area in ls}
zone=lambda g:{(z,u):area for z,u,area in g["zone_edges"]}
ad,bd=direct(a),direct(b);az,bz=zone(a),zone(b)
assert all(bd[k]==v for k,v in ad.items())
assert all(bz[k]==v for k,v in az.items())
r["all_old_direct_and_zone_contact_areas_exact"]=True
r["all_old_nonzone_object_material_nodes_exact"]=all(k in b["material_nodes"] and v==b["material_nodes"][k]for k,v in a["material_nodes"].items() if v["kind"]!="zone")
assert r["all_old_nonzone_object_material_nodes_exact"]
r["changed_zone_material_nodes"]=[dict(node=k,before=v,after=b["material_nodes"][k]) for k,v in a["material_nodes"].items() if v["kind"]=="zone" and v!=b["material_nodes"].get(k)]
assert len(r["changed_zone_material_nodes"])==2
for row in r["changed_zone_material_nodes"]:
 assert row["before"]["net"]=="GND" and row["before"]["layer"]in["In1.Cu","In2.Cu"]
 assert {k:v for k,v in row["before"].items()if k!="area_mm2"}=={k:v for k,v in row["after"].items()if k!="area_mm2"}
r["zone_area_change_interpretation"]="Only the two GND plane material areas change: actual new through-drill removal, geometrically verified in geometry.json. Serialized fill forms remain exact. Object-node identity is not a claim that drilled plane material is unchanged."
(D/"qa/graph-comparison.json").write_text(json.dumps(r,indent=2)+"\n")
