exec(open('/workspace/shared/maru60-resume/continuation-c782/independent27/native_geometry_bounded.py').read().split('D={k:capture')[0])
uid='55e5d0cf-c179-4e88-925d-241a5a9d4416';D={k:capture(paths[k]) for k in ['base','combined']};sh={};un={}
for k in D:
 b,items,holes,planes=D[k];t=items[uid];sh[k]=minus(polygon(t.GetEffectiveShape(p.F_Cu)),holes);un[k]=minus(sh[k],planes[p.In1_Cu]);print(k,t.GetStart(),t.GetEnd(),flush=True)
new=minus(un['combined'],un['base']);window=polygon(p.SHAPE_CIRCLE(p.VECTOR2I(96650000,41625000),455000));out=minus(new,window);coords=[[[out.COutline(j).CPoint(i).x,out.COutline(j).CPoint(i).y]for i in range(out.COutline(j).PointCount())]for j in range(out.OutlineCount())];points=[xy for c in coords for xy in c];bounds=[min(x[0] for x in points),min(x[1] for x in points),max(x[0] for x in points),max(x[1] for x in points)];print('exception',out.Area()/1e12,bounds,flush=True)
near=[]
for u,x in D['combined'][1].items():
 if not isinstance(x,p.PCB_VIA):continue
 px,py=x.GetPosition().x,x.GetPosition().y
 if bounds[0]-1000000<px<bounds[2]+1000000 and bounds[1]-1000000<py<bounds[3]+1000000:near.append({'uuid':u,'net':x.GetNetname(),'xy_nm':[px,py]})
diagnostic={'current_copper_intersection_mm2':both(out,sh['combined']).Area()/1e12,'current_plane_intersection_mm2':both(out,D['combined'][3][p.In1_Cu]).Area()/1e12,'old_copper_intersection_mm2':both(out,sh['base']).Area()/1e12,'old_plane_intersection_mm2':both(out,D['base'][3][p.In1_Cu]).Area()/1e12};result={'diagnostic':diagnostic,'uuid':uid,'outside_area_mm2':out.Area()/1e12,'contours_nm':coords,'bounds_nm':bounds,'nearby_vias':near};(O/'exception-geometry.json').write_text(json.dumps(result,indent=2));print(near,flush=True)
