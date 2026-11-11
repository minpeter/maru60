"""Build an isolated TC-M2x3.0 catch-mount trial and test its nominal CAD envelopes.

Run from the repository: uv run tools/study_catch_inserts.py --output PATH
This never overwrites topcase-draft/, bottomcase-draft/, models/ or evidence/.
The normal generators still default to the existing self-tapping pilots.

Insert dimensions: https://cnckitchen.store/products/heat-set-insert-m2-x-3-100-pieces
The stock catches are photo-derived envelopes, NOT manufacturer CAD. In particular,
the 1.45 mm lower ear thickness used to illustrate an M2x4 screw is only a trial.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import manifold3d as md
import numpy as np
import shapely.geometry as sg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_bottomcase_draft as bottom
import build_topcase_draft as top
import rule60_spec as spec
from verify_topcase import plate_gas_world


def box(x0, y0, x1, y1, z0, z1):
    return md.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])


def cylinder(x, y, z, height, radius):
    return md.Manifold.cylinder(height, radius, circular_segments=96).translate([x, y, z])


def volume(m):
    return max(0.0, float(m.volume()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--board', choices=spec.board_ids(), default=spec.default_board())
    args = ap.parse_args()
    out = args.output.resolve()
    protected = [Path(top.OUT).resolve(), Path(bottom.OUT).resolve(),
                 Path(top.__file__).parent/'models', Path(top.__file__).parent/'evidence']
    assert not any(out == p or p in out.parents for p in protected), 'choose a separate trial output directory'
    out.mkdir(parents=True, exist_ok=True)
    base_halves = top.build_halves(args.board)
    trial_halves = top.build_halves(args.board, catch_inserts=True)
    baseline_top, trial_top = sum(base_halves, md.Manifold()), sum(trial_halves, md.Manifold())
    meshes = {}

    def save(name, m):
        tm = bottom.to_trimesh(m)
        tm.export(out/f'{name}-world.stl')
        meshes[name] = {'vertices': tm.vertices.tolist(), 'faces': tm.faces.tolist()}
        return tm

    for label, halves in [('baseline', base_halves), ('trial', trial_halves)]:
        for side, m in zip(['left', 'right'], halves):
            tm = save(f'{label}-upper-{side}', m)
            tm.apply_translation([128-(tm.bounds[0,0]+tm.bounds[1,0])/2,
                                  128-(tm.bounds[0,1]+tm.bounds[1,1])/2,-tm.bounds[0,2]])
            assert len(tm.split())==1 and np.all(tm.bounds[1]<=256)
            top.write_3mf(out/f'{label}-upper-{side}-trial.3mf', 'LOCAL INSERT STUDY / NOT RELEASED',
                          [(f'{label}-upper-{side}',tm)])
    report = {'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
              'board': args.board, 'insert': top.CATCH_INSERT, 'variants': {},
              'assumptions': {'material': 'PETG thermoplastic, not confirmed by owner',
                'stock_hardware': 'photo-derived spec envelopes, no manufacturer identity/drawing confirmed',
                'lower_clamp_thickness_mm': 1.45, 'lower_clamp_thickness_status': 'illustrative only; unmeasured',
                'countersunk_head': '90 degree, diameter 4.1 mm photo upper bound; not a certified part drawing',
                'pcb': 'GH60 rectangular envelope, bottom components 2.0 mm; not a routed MARU60 PCB',
                'USB': 'existing 9.0 x 7.4 x 3.26 mm candidate gauge, not final selected connector'},
              'sources': ['https://cnckitchen.store/products/heat-set-insert-m2-x-3-100-pieces',
                          'https://cnckitchen.store/products/m2-screw-stainless-steel-aisi-304-low-head']}
    holes = []
    for name, xp, yp in top.strike_centers_p():
        for i, dx in enumerate([-6.5, 6.5], 1):
            holes.append({'name': f'U-{name}.{i}', 'case': 'upper', 'world': list(top.pw(xp+dx, yp)),
                          'seat': top.Z_STRIKE, 'direction': -1})
    for site in bottom.catch_sites_p():
        for i, axis in enumerate(site['screws_p'], 1):
            holes.append({'name': f'D-{site["name"]}.{i}', 'case': 'lower', 'world': list(top.pw(*axis)),
                          'seat': bottom.CATCH_FLOOR_ZP, 'direction': 1})
    assert len(holes) == 16
    plate = md.CrossSection([plate_gas_world()]).extrude(spec.value('plate.thickness')).translate([0,0,top.Z_PLATE])
    pcb_frame = json.loads((Path(top.__file__).parent/'spec/boards.json').read_text())['frames']['pcb_to_plate']
    (x0,y0),(x1,y1) = top.pw(pcb_frame['dx']+285,pcb_frame['y0']-94.6), top.pw(pcb_frame['dx'],pcb_frame['y0'])
    pcb = box(x0,y0,x1,y1,12.5,14.1) + box(x0+1,y0+1,x1-1,y1-1,14.1,16.1)
    ux = spec.usb_centre_plate_x(args.board)
    (ux0,uy0),(ux1,uy1) = top.pw(ux+4.5,pcb_frame['y0']-7.4), top.pw(ux-4.5,pcb_frame['y0']+.6)
    usb = box(ux0,uy0,ux1,uy1,14.1,17.36)
    save('gauge-pcb', pcb)
    save('gauge-usb', usb)
    save('gauge-plate', plate)
    sp = spec.value('ball_catch.strike_plate')
    cb = spec.value('ball_catch.catch_body')
    strikes, catches, inserts, screws = md.Manifold(),md.Manifold(),md.Manifold(),md.Manifold()
    for name,xp,yp in top.strike_centers_p():
        x,y=top.pw(xp,yp)
        strike = box(x-sp['length']/2,y-sp['width']/2,x+sp['length']/2,y+sp['width']/2,5.55,7)
        catch = box(x-10.6,y-cb['width']/2,x+10.6,y+cb['width']/2,7.6,15.3)
        for sign in [-1,1]:
            catch += box(min(x+sign*10.6,x+sign*15.9),y-cb['width']/2,
                         max(x+sign*10.6,x+sign*15.9),y+cb['width']/2,13.85,15.3)
        for h in [h for h in holes if h['name'].startswith(f'U-{name}.')]:
            hx,hy=h['world']
            strike -= cylinder(hx,hy,5.5,2,1.1)
        for h in [h for h in holes if h['name'].startswith(f'D-{name}.')]:
            hx,hy=h['world']
            catch -= cylinder(hx,hy,13.8,2,1.1)
        # Gauges are not drawn as detailed stock hardware; the tongue/ball engagement is intentionally not simulated.
        strikes += strike
        catches += catch
        save(f'gauge-strike-{name}', strike)
        save(f'gauge-catch-{name}', catch)
    for h in holes:
        x,y=h['world'];seat=h['seat'];direction=h['direction']
        z0=min(seat,seat+direction*3)
        insert=cylinder(x,y,z0,3,1.8)-cylinder(x,y,z0-.01,3.02,1.0)
        # Countersunk L includes the head: t=1.45 -> M2x4 penetrates 2.55 beyond the seat.
        face=seat-direction*1.45
        head = md.Manifold.cylinder(1.05,2.05,1.0,96)
        shank = md.Manifold.cylinder(2.95,1,1,96).translate([0,0,1.05])
        screw=head+shank
        if direction < 0:
            screw=screw.rotate([180,0,0])
        screw=screw.translate([x,y,face])
        inserts+=insert;screws+=screw
        save(f'insert-{h["name"]}',insert)
        save(f'gauge-screw-{h["name"]}',screw)

    for bay in [False, True]:
        key='with-bay' if bay else 'no-bay'
        baseline,_=bottom.build(args.board,battery_bay=bay)
        trial,meta=bottom.build(args.board,battery_bay=bay,catch_inserts=True)
        base_parts=bottom.split(baseline);trial_parts=bottom.split(trial)
        for label,parts in [('baseline',base_parts),('trial',trial_parts)]:
            for side,m in zip(['left','right'],parts):
                save(f'{key}-{label}-lower-{side}',m)
                tm=bottom.on_bed(m)
                assert len(tm.split())==1 and np.max(tm.extents)<=256
                top.write_3mf(out/f'{key}-{label}-lower-{side}-trial.3mf', 'LOCAL INSERT STUDY / NOT RELEASED',
                              [(f'{key}-{label}-{side}',tm)],fine_layer_z=None)
        trial=sum(trial_parts,md.Manifold())
        baseline=sum(base_parts,md.Manifold())
        checks={}
        for h in holes:
            x,y=h['world'];seat=h['seat'];direction=h['direction']
            material=trial_top if h['case']=='upper' else trial
            z0=min(seat,seat+direction*4)
            witness_r=2.9 if h['case']=='upper' else 3.1
            annulus=cylinder(x,y,z0+.001,3.998,witness_r)-cylinder(x,y,z0,4.001,1.605)
            bore=cylinder(x,y,z0+.001,3.998,1.59)
            tool_z=seat+.02 if direction < 0 else seat-20.02
            tool=cylinder(x,y,tool_z,20,2.0)
            missing=volume(annulus-material)
            blocked=volume(bore^material)
            access=volume(tool^material)
            assert max(missing,blocked,access)<.001,(h['name'],missing,blocked,access)
            # Conservative blind-floor skin over the whole Ø3.2 hole, not just its centre axis.
            skin_z=z0-.80 if direction < 0 else z0+4
            skin=cylinder(x,y,skin_z,.80,1.6)
            skin_missing=volume(skin-material)
            assert skin_missing<.001,(h['name'],'blind skin',skin_missing)
            outside_skin=(5.55-4 if direction<0 else
                          (1.3 if y>150 else bottom.desk_zp(y-1.6)-seat-4))
            checks[h['name']]={**h,'hole_d_mm':3.2,'hole_depth_mm':4,
                'required_wall_1p3_missing_mm3':missing,'bore_blockage_mm3':blocked,
                'wall_witness_mm':witness_r-1.6,
                'tool_d4_access_blockage_mm3':access,'blind_floor_0p8_missing_mm3':skin_missing,
                'minimum_axial_skin_over_hole_mm':outside_skin,'M2x4_engagement_mm':2.55,'M2x4_tip_to_hole_bottom_mm':1.45}
        assembly={'cases_seated_mm3':volume(trial^trial_top),
                  'cases_xy_shift_0p1_mm3':max(volume(trial.translate([dx,dy,0])^trial_top)
                                              for dx in [-.1,0,.1] for dy in [-.1,0,.1]),
                  'case_insertion_path_mm3':max(volume(trial.translate([0,0,d])^trial_top)
                                                for d in [.1,.2,1,3,6,12,24]),
                  'plate_up_0p25_mm3':volume(plate.translate([0,0,-.25])^(trial_top+trial)),
                  'plate_down_1_mm3':volume(plate.translate([0,0,1])^trial),
                  'PCB_USB_down_0p8_mm3':volume((pcb+usb).translate([0,0,.8])^(trial_top+trial)),
                  'catch_envelope_case_mm3':volume(catches^(trial_top+trial)),
                  'strike_envelope_case_mm3':volume(strikes^(trial_top+trial)),
                  'catch_envelope_pcb_mm3':volume(catches^pcb),
                  'screws_vs_pcb_plate_mm3':volume(screws^(pcb+usb+plate)),
                  'lower_half_insertion_path_mm3':max(volume((trial_parts[0].translate((d*np.asarray(bottom.FROM_PRINT)[:,2]).tolist())^trial_parts[1])-bottom.seam_rib_zones_world())
                                                      for d in [0,.2,1,3,6,12,24]),
                  'screw_envelopes_case_mm3':volume(screws^(trial_top+trial))}
        assert max(assembly.values())<.01,assembly
        caps=[]
        for i,points in enumerate(spec.gasket_outlines_plate(),1):
            ring=sg.Polygon([top.pw(x,y) for x,y in points])
            cap=bottom.prism(ring,9,10.19)
            collision=volume(cap^trial)
            bearing=volume(cap.translate([0,0,.1])^trial)
            before_bearing=volume(cap.translate([0,0,.1])^baseline)
            assert collision<.01 and abs(bearing-before_bearing)<.001,(i,collision,bearing,before_bearing)
            caps.append({'cap':i,'collision_mm3':collision,'bearing_mm3':bearing,'baseline_bearing_mm3':before_bearing})
        # Exact Boolean witnesses ensure all 12 gasket sites and USB retain their current shapes, not just radii.
        delta=(trial-baseline)+(baseline-trial)
        cap_changed=volume(delta^box(-160,80,160,198,9.65,10.3))
        usb_changed=volume(delta^box(ux0-6,uy0-10,ux1+6,220,9.6,35))
        assert cap_changed<.001 and usb_changed<.001,(cap_changed,usb_changed)
        upper_delta=(trial_top-baseline_top)+(baseline_top-trial_top)
        assert volume(upper_delta^box(-160,80,160,198,6.2,9.7))<.001
        # The manufacturer's minimum lateral wall and blind depth do not certify strength or heat-set process.
        report['variants'][key]={'status':'NOMINAL_CAD_PASSED_PHYSICAL_VALIDATION_REQUIRED',
            'holes':checks,'assembly':assembly,'caps':caps,'gasket_region_changed_mm3':cap_changed,
            'USB_region_changed_mm3':usb_changed,'rear_skin_mm':1.3,
            'added_volume_mm3':volume(trial-baseline),'removed_volume_mm3':volume(baseline-trial),
            'metadata':meta}
    report['screw_length_sweep']=[{'length_mm':L,'flush_countersunk_clamp_thickness_for_2_to_3_mm_engagement':[L-3,L-2]}
                                  for L in [4,5,6,8]]
    report['upper_skirt_min_remaining_at_lower_boss_reliefs_mm']=2.125
    report['upper_wedge_change']={'shortened_x_mm':.2,'underside_z_p_at_seam_mm':2.2,'strike_seat_z_p_mm':5.55,
                                 'glue_gap_mm':.2,'reason':'retain >=1.3 mm insert-hole wall beside the seam-key notch'}
    report['limitations']=['No strength/FEA certification or heat-set process test.',
        'No actual thread, knurl or ball/tongue contact simulation; insert interference with pilot is intentional.',
        'Lower ear thickness, countersink geometry and stock hole pitches need measurements before selecting screws.',
        'The 0.20 mm nested-boss clearance and Ø3.20 holes require a print/heat-set coupon; no universal printer tolerance assumed.']
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'render-meshes.json').write_text(json.dumps(meshes,separators=(',',':')))
    print(json.dumps({k:{'status':v['status'],'assembly':v['assembly']} for k,v in report['variants'].items()},indent=2))


if __name__=='__main__':
    main()
