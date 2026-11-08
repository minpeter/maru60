from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu');exec((R/'scripts/audit_north_return_b_c.py').read_text().split("print('Capture source planes")[0]);b,new,_,holes=capture(B,False);q=next(q for q in b.GetTracks() if uid(q)=='db39d882-6ecf-4006-b107-6b00b1abd04a');un=delta(delta(poly(q.GetEffectiveShape(p.F_Cu),True),holes),new[p.In1_Cu]);env=p.SHAPE_POLY_SET()
for v in b.GetTracks():
 if isinstance(v,p.PCB_VIA) and v.GetNetname()=='+1V1':env.Append(poly(p.SHAPE_CIRCLE(v.GetPosition(),v.GetWidth(p.F_Cu)//2+205000),True))
env.Simplify();outside=delta(un,env);parts=[]
for i in range(outside.OutlineCount()):
 o=outside.Outline(i);z=p.SHAPE_POLY_SET();z.AddOutline(o);bb=o.BBox();parts.append({'area_mm2':z.Area()/1e12,'bbox_mm':[bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6],'polygon_mm':[[o.CPoint(j).x/1e6,o.CPoint(j).y/1e6] for j in range(o.PointCount())]})
report={'candidate_sha256':h(B),'failed_track_uuid':uid(q),'uncovered_outside_unchanged_own_transition_mm2':outside.Area()/1e12,'parts':parts,'limits':'Local exact geometry of rejected D only. Not a global routing impossibility statement.'};(R/'qa/repair-D-failure-geometry.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
