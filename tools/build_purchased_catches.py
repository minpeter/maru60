"""Generate and verify a separate purchased 32 mm catch / CANOT OD3.5 L3 trial.

Not production-ready: hole diameter/depth, head seating, material and engagement
height require physical coupons/measurements. Does not overwrite published files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import manifold3d as md
import numpy as np
import shapely.geometry as sg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_bottomcase_draft as b
import build_topcase_draft as t
import rule60_spec as spec


def box(x0, y0, x1, y1, z0, z1):
    return md.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])


def cyl(x, y, z, h, r):
    return md.Manifold.cylinder(h, r, circular_segments=96).translate([x, y, z])


def vol(m):
    return max(0.0, float(m.volume()))


def union(parts):
    return md.Manifold.batch_boolean(list(parts), md.OpType.Add)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--board', choices=spec.board_ids(), default=spec.default_board())
    ap.add_argument('--insert-hole-d', type=float, choices=[3.0, 3.1, 3.2], default=3.2)
    ap.add_argument('--mount-design', choices=['boxed', 'sculpted'], default='boxed',
                    help='sculpted preserves the original upper seat and limits body relief to its height band')
    ap.add_argument('--weight-holes', type=Path, help='JSON [[x,y],...] in DWG plate frame; measured A plate only')
    args = ap.parse_args()
    sculpted = args.mount_design == 'sculpted'
    uz = t.SCULPTED_CATCH['strike_z'] if sculpted else t.PURCHASED_STRIKE_Z
    dz = t.SCULPTED_CATCH['catch_z'] if sculpted else t.PURCHASED_CATCH_Z
    depth = t.SCULPTED_CATCH['depth'] if sculpted else t.PURCHASED_INSERT['depth']
    out = args.output.resolve()
    root = Path(t.__file__).parent
    assert not any(out == root/p or root/p in out.parents for p in ['models','evidence','topcase-draft','bottomcase-draft'])
    out.mkdir(parents=True, exist_ok=True)
    weight_holes = json.loads(args.weight_holes.read_text()) if args.weight_holes else None
    if weight_holes is not None:
        assert len(weight_holes) == 4 and all(len(p) == 2 and all(np.isfinite(p)) for p in weight_holes)
        assert all(b.deco_poly_print().buffer(-2.7).contains(sg.Point(*b.deco_to_print(*p))) for p in weight_holes)
    report = {'board': args.board, 'mount_design': args.mount_design,
              'seats_zp': {'upper':uz,'lower':dz},
              'insert': {**t.PURCHASED_INSERT,'hole_d': args.insert_hole_d,'depth':depth},
              'seller_dimensions_mm': {'catch':[31.6,8,9], 'body_pitch':25, 'strike_pitch':11,
                                       'strike_length':18, 'ear_thickness':2,'assembled_height':11,'holes_d':3.2},
              'assumptions': ['Width 8 used conservatively for both metal parts; strike width not separately dimensioned.',
                  f'Pilot 3.0/3.1/3.2 and {depth} depth are trial candidates, not CANOT recommendations.',
                  f'Depth {depth} leaves {depth-3:.1f} below insert; thermal flow, holding force and screw-head seating untested.',
                  'PETG assumed for coupons, owner printing material unconfirmed.',
                  'M2x4 countersunk, head diameter3.85 height1.4; material and recess unconfirmed.',
                  'GH60 rectangular PCB/component and USB candidate envelopes, not routed MARU60 electronics.',
                  'No knurl, thread or ball/tongue contact simulation; no FEA/strength claim.'],
              'weight_holes_status':'measured override' if weight_holes else 'photo-derived provisional; not purchased-plate measurement',
              'checks':{},'variants':{}}
    failures = []

    def check(group, name, value, maximum=.001):
        group[name] = value
        if value > maximum:
            failures.append((name,value))

    def save(name, m, print_kind=None):
        tm = b.to_trimesh(m)
        tm.export(out/f'{name}-world.stl')
        assert tm.is_watertight and tm.is_winding_consistent, name
        if print_kind:
            assert len(tm.split()) == 1, name
            if print_kind == 'lower':
                tm = b.on_bed(m)
            else:
                tm.apply_translation([128-tm.bounds[:,0].mean(),128-tm.bounds[:,1].mean(),-tm.bounds[0,2]])
            assert np.all(tm.bounds[0]>=-1e-5) and np.all(tm.bounds[1]<=256), (name,tm.bounds)
            t.write_3mf(out/f'{name}.3mf','PURCHASED HARDWARE TRIAL / MEASURE BEFORE PRINT',[(name,tm)],fine_layer_z=None)

    baseline_u = t.build_halves(args.board,catch_inserts=True)
    upper = t.build_halves(args.board,purchased_catches=True,insert_hole_d=args.insert_hole_d,sculpted_catches=sculpted)
    U = union(upper); U0 = union(baseline_u)
    for label, halves in [('before',baseline_u),('purchased',upper)]:
        for side,m in zip(['left','right'],halves):
            save(f'{label}-upper-{side}',m,'upper')
    holes=[]
    catches=[];strikes=[];screws=[];inserts=[]
    for name,xp,yp in t.strike_centers_p(purchased=True):
        x,y=t.pw(xp,yp)
        # Conservative full bounding volume, not a reverse-engineered barrel or ball/tongue model.
        c=box(x-15.8,y-4,x+15.8,y+4,dz-9,dz)
        s=box(x-9,y-4,x+9,y+4,uz,uz+2)
        for part,offset,seat,direction in [('U',5.5,uz,-1),('D',12.5,dz,1)]:
            for i,dx in enumerate([-offset,offset],1):
                hx=x+dx
                h={'name':f'{part}-{name}.{i}','part':part,'x':hx,'y':y,'seat':seat,'direction':direction}
                holes.append(h)
                if part=='U': s-=cyl(hx,y,uz-.01,2.02,1.6)
                else: c-=cyl(hx,y,dz-9-.01,9.02,1.6)
                insert=cyl(hx,y,min(seat,seat+direction*3),3,1.75)-cyl(hx,y,min(seat,seat+direction*3)-.01,3.02,1)
                head=md.Manifold.cylinder(1.4,1.925,1,96)
                shank=md.Manifold.cylinder(2.6,1,1,96).translate([0,0,1.4])
                screw=head+shank
                if direction<0: screw=screw.rotate([180,0,0])
                screw=screw.translate([hx,y,seat-direction*2])
                save(f'insert-{h["name"]}',insert);save(f'screw-{h["name"]}',screw)
                inserts.append(insert);screws.append(screw)
        save(f'catch-{name}',c);save(f'strike-{name}',s)
        catches.append(c);strikes.append(s)
    assert len(holes)==16
    C,S,SC=union(catches),union(strikes),union(screws)
    plate_points=[t.pw(x,y) for x,y in spec.outline_points('plate_gas')]
    if not sg.LinearRing(plate_points).is_ccw: plate_points.reverse()
    plate=md.CrossSection([plate_points]).extrude(1.5).translate([0,0,7.5])
    frame=json.loads((root/'spec/boards.json').read_text())['frames']['pcb_to_plate']
    (x0,y0),(x1,y1)=t.pw(frame['dx']+285,frame['y0']-94.6),t.pw(frame['dx'],frame['y0'])
    pcb=box(x0,y0,x1,y1,12.5,14.1)+box(x0+1,y0+1,x1-1,y1-1,14.1,16.1)
    ux=spec.usb_centre_plate_x(args.board)
    if ux is None: ux=spec.usb_notch(args.board)[0]
    (ux0,uy0),(ux1,uy1)=t.pw(ux+4.5,frame['y0']-7.4),t.pw(ux-4.5,frame['y0']+.6)
    usb=box(ux0,uy0,ux1,uy1,14.1,17.36)
    for label,m in [('plate',plate),('pcb',pcb),('usb',usb)]: save(label,m)
    for bay in [False,True]:
        key='with-bay' if bay else 'no-bay'
        base,_=b.build(args.board,battery_bay=bay,catch_inserts=True)
        lower,meta=b.build(args.board,battery_bay=bay,purchased_catches=True,
                           insert_hole_d=args.insert_hole_d,weight_holes=weight_holes,sculpted_catches=sculpted)
        parts=b.split(lower);oldparts=b.split(base)
        L=union(parts);L0=union(oldparts)
        checks={};hchecks={}
        for label,halves in [('before',oldparts),('purchased',parts)]:
            for side,m in zip(['left','right'],halves): save(f'{key}-{label}-lower-{side}',m,'lower')
        for h in holes:
            x,y,seat,d=h['x'],h['y'],h['seat'],h['direction']
            material=U if h['part']=='U' else L
            z=min(seat,seat+d*depth)
            hc={}
            # Require continuous material to 1.3 mm BEYOND the OD3.5 knurl, plus 0.8 blind floor.
            shell=cyl(x,y,z+.001,depth-.002,3.05)-cyl(x,y,z,depth+.001,1.601)
            check(hc,'wall_missing_mm3',vol(shell-material))
            check(hc,'bore_blocked_mm3',vol(cyl(x,y,z+.001,depth-.002,args.insert_hole_d/2-.005)^material))
            skinz=z-.8 if d<0 else z+depth
            check(hc,'blind_floor_0p8_missing_mm3',vol(cyl(x,y,skinz,.8,1.6)-material))
            toolz=seat+.02 if d<0 else seat-20.02
            check(hc,'tool_d4_blocked_mm3',vol(cyl(x,y,toolz,20,2)^material))
            hc.update(h);hc['nominal_M2x4_engagement_mm']=2;hc['tip_clearance_mm']=depth-2
            hchecks[h['name']]=hc
        for name,m in [('catch',C),('strike',S),('screws',SC)]:
            check(checks,f'{name}_vs_cases_mm3',vol(m^(L+U)))
            check(checks,f'{name}_vs_plate_pcb_usb_mm3',vol(m^(plate+pcb+usb)))
        bearing={}
        for name,c,s in zip(['BL','BR','FL','FR'],catches,strikes):
            lower_area=vol(c.translate([0,0,.05])^L)/.05
            upper_area=vol(s.translate([0,0,-.05])^U)/.05
            bearing[name]={'lower_mm2':lower_area,'upper_mm2':upper_area}
            check(checks,f'{name}_lower_bearing_shortfall_mm2',max(0,.75*(31.6*8-2*np.pi*1.6**2)-lower_area))
            check(checks,f'{name}_upper_bearing_shortfall_mm2',max(0,.95*(18*8-2*np.pi*1.6**2)-upper_area))
        check(checks,'cases_seated_mm3',vol(L^U))
        check(checks,'cases_xy_0p1_mm3',max(vol(L.translate([dx,dy,0])^U) for dx in [-.1,0,.1] for dy in [-.1,0,.1]))
        check(checks,'case_insertion_mm3',max(vol(L.translate([0,0,d])^U) for d in [.1,.2,1,3,6,12,24]))
        check(checks,'lower_split_insertion_mm3',max(vol(parts[0].translate((d*np.asarray(b.FROM_PRINT)[:,2]).tolist())^parts[1]) for d in [0,.2,1,3,6,12,24]))
        # The existing dovetails intentionally compress three rib bands. Test outside those
        # same permitted zones, rather than mistaking the unchanged press fit for a collision.
        rib_zones=union(box(.5,y-7,6.7,y+7,4,9.2) for y in t.JOINT_YC.values())
        check(checks,'upper_split_outside_ribs_mm3',max(vol((upper[0].translate([0,0,float(d)])^upper[1])-rib_zones)
                                                      for d in np.linspace(0,18,91)))
        checks['upper_intentional_rib_overlap_mm3']=vol(upper[0]^upper[1])
        check(checks,'upper_rib_overlap_change_mm3',abs(vol(upper[0]^upper[1])-vol(baseline_u[0]^baseline_u[1])))
        check(checks,'installed_hardware_opening_path_mm3',max(vol(((L+C).translate([0,0,d]))^(U+S))
                                                            for d in [.1,.2,1,3,6,12,24]))
        for travel in [-.25,0,1]: check(checks,f'plate_travel_{travel}_mm3',vol(plate.translate([0,0,travel])^(L+U)))
        for travel in [0,.8]: check(checks,f'pcb_usb_travel_{travel}_mm3',vol((pcb+usb).translate([0,0,travel])^(L+U+C+S)))
        caps=[]
        for i,points in enumerate(spec.gasket_outlines_plate(),1):
            plan=sg.Polygon([t.pw(x,y) for x,y in points])
            lo=b.prism(plan,9,10.19); hi=b.prism(plan,6.31,7.5)
            g={}
            check(g,'lower_cap_collision_mm3',vol(lo^L));check(g,'upper_cap_collision_mm3',vol(hi^U))
            check(g,'metal_cap_collision_mm3',vol((lo+hi)^(C+S+SC)))
            check(g,'lower_bearing_change_mm3',abs(vol(lo.translate([0,0,.1])^L)-vol(lo.translate([0,0,.1])^L0)))
            check(g,'upper_bearing_change_mm3',abs(vol(hi.translate([0,0,-.1])^U)-vol(hi.translate([0,0,-.1])^U0)))
            region=b.prism(plan.buffer(.03),5.9,10.4)
            check(g,'gasket_shape_delta_mm3',vol((((L-L0)+(L0-L)) + ((U-U0)+(U0-U)))^region))
            caps.append(g)
        delta=(L-L0)+(L0-L)
        check(checks,'usb_shape_delta_mm3',vol(delta^box(ux0-6,uy0-10,ux1+6,220,9.6,35)))
        # Verify hardware still bridges the intentional split seams (one axis on each half).
        bridges={}
        for name,xp,yp in t.strike_centers_p(purchased=True):
            x,y=t.pw(xp,yp)
            for part,halfset,pitch,seat,d in [('U',upper,11,uz,-1),('D',parts,25,dz,1)]:
                if (part=='U' and name==t.BACK_SEAM_STRIKE) or (part=='D' and name in [b.SEAM_BACK_CATCH,b.SEAM_FRONT_CATCH]):
                    owners=[]
                    for dx in [-pitch/2,pitch/2]:
                        ring=cyl(x+dx,y,seat+(-.1 if d<0 else .01),.09,2.5)-cyl(x+dx,y,seat-.2,.4,1.61)
                        owners.append(int(np.argmax([vol(ring^half) for half in halfset])))
                    assert owners[0]!=owners[1],(part,name,owners)
                    bridges[f'{part}-{name}']=owners
        report['variants'][key]={'checks':checks,'holes':hchecks,'caps':caps,'bearing_area_mm2':bearing,
                                 'minimum_axial_skin_mm': {'upper':uz-depth,'front_lower':b.desk_zp(min(h['y'] for h in holes)-1.6)-dz-depth,'rear_lower_pad':1.3},
                                 'split_bridge_axis_owners':bridges,'metadata':meta,
                                 'purchased_hardware_vs_previous_cases_mm3':vol((C+S)^(L0+U0)),
                                 'head_vs_plain_hardware_intersection_mm3':vol(SC^(C+S)),
                                 'head_seating_status':'UNRESOLVED: plain seller holes are not certified countersinks'}
    # A keyed corner makes the diameter order unambiguous even after removing the part from the bed.
    coupon=box(0,0,48,12,0,depth+1)
    coupon-=b.prism(sg.Polygon([(0,0),(3,0),(0,3)]),-.1,depth+1.1)
    for i,d in enumerate([3.0,3.1,3.2]): coupon-=cyl(8+i*16,6,1,depth+.01,d/2)
    save('pilot-coupon-3p0-3p1-3p2',coupon,'upper')
    report['failures']=failures
    report['status']='NOMINAL_CAD_PASS_PHYSICAL_CHECKS_PENDING' if not failures else 'CAD_CHECKS_FAILED'
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'failures':failures},indent=2))
    assert not failures, failures


if __name__=='__main__': main()
