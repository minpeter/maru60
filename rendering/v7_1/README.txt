Keyboard visualization source checkpoint v7.1

This is a reconstructed 3D rendering project, NOT product photography or manufacturing-fit CAD.
Exact geometry: the user-supplied v7.4 front shell STEP and its STL tessellation.
Approximate reconstructed geometry: keycaps, bottom plate, metal strip and feet. These are visualization assets inferred from user videos/photos, not verified engineering dimensions.
The visually matched keycap set is YongQiu Retro Programmer 143 (Cherry-like profile). This is not the manufacturer's CAD or exact typeface reproduction.

V7 changes only CapsLock geometry and Kiro print/material relative to the individually reviewed v6.1 assets. CapsLock now has a smooth stepped transition instead of triangulated faceting. The Kiro background is continuous muted purple with no rounded patch, per the latest user preference; the exact official ghost shape is retained. Color is not instrument-calibrated. Other 58 caps unchanged.
Official FriendliAI, Upstage and Kiro logo shapes are used for this private visualization. Their inclusion does not grant trademark or commercial-use rights. See source attribution. Some legends were restored with image generation from user/source images, and legend wording was checked against later closeups; typeface and fine print remain reconstructed; see per-key provenance.

Blender 4.3.2. The .blend includes packed textures and is saved at front0.
Rebuild full72: blender -b --factory-startup --python render_studio.py -- final
Only35 degrees: blender -b --factory-startup --python render_studio.py -- final 35
Individual keycaps: blender -b --factory-startup --python render_individual_keycaps.py

Output: 1024x1536 RGBA transparent PNG, Cycles CPU256samples.
72 frames000..071 = angles0,5,...355 degrees (no duplicate360).
Fixed camera/lighting/model, rotation about keyboard long axis with15degree screen lean, not tabletop turntable yaw. Front0 has purple at top, blue at bottom and palm rest to left.
Per-frame checksum checkpoints support safe restart with unchanged source assets.

QA: all60 v6.1 actual individual renders reviewed; only two changed v7 keys separately re-reviewed under neutral and board35 lighting. Qualified visualization pass, not exact material, color, font or dimension certification.

Performance: first42 completed frames used6 CPU threads; remaining frames used9. Samples, resolution, lighting and visual assets unchanged. Run render_9threads.py for the9thread override; render_studio.py retains the6thread default. The performance manifest records the original script hash; release scripts use portable relative paths.
