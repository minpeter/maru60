import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Patch
import pathlib, json
R = pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4')
d = json.loads((R / 'qa/local-native-view.json').read_text())
palette = {'GND':'#6e9b75','USB_DVDT':'#d99100','USB_DVDT_CAP':'#00a6ba','USB_OVLO':'#9b51ab','USB_UVLO':'#3d68c8','USB_ILM':'#d44d3a','VBUS_PROTECTED_RAW':'#db6964','VBUS_FUSED':'#c95c52'}
fig, axs = plt.subplots(1, 2, figsize=(17, 9))
fig.patch.set_facecolor('#f5f7fa')
for ax, (layer, rows) in zip(axs, d['layers'].items()):
    ax.set_facecolor('#fff')
    ax.set_title(layer + ' • same X/Y orientation', fontsize=14, fontweight='bold')
    for row in rows:
        typ = row['type']
        color = palette.get(row.get('net'), '#8c929b') if typ == 'copper' else '#242a33' if typ == 'silk' else '#65788b' if typ == 'fab' else '#b6bec8'
        alpha = .85 if typ == 'copper' else .9 if typ == 'silk' else .6
        for z in row['poly']:
            verts, codes = [], []
            for ring in [z['o']] + z['h']:
                if len(ring) < 3:
                    continue
                verts += ring + [ring[0]]
                codes += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 1) + [Path.CLOSEPOLY]
            if verts:
                ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor='none', alpha=alpha, zorder=3 if typ == 'silk' else 2 if typ == 'copper' else 1))
    ax.set_xlim(6.5, 23)
    ax.set_ylim(24.3, 14.5)
    ax.set_aspect('equal')
    ax.set_xlabel('Board X (mm)')
    ax.set_ylabel('Board Y (mm)')
    ax.grid(color='#e8edf3', linewidth=.4, zorder=0)
fig.suptitle('UNSELECTED V4 • actual saved board 8c45df36', fontsize=20, fontweight='bold', y=.94)
keys = ['USB_DVDT','USB_DVDT_CAP','USB_OVLO','USB_UVLO','USB_ILM','GND']
fig.legend([Patch(color=palette[k]) for k in keys], ['DVDT before R125','CAP after R125','OVLO','UVLO','ILM','GND'], loc='lower center', ncol=6, bbox_to_anchor=(.5,.16), frameon=False)
fig.text(.5, .12, 'Source: exact 7c23. New signal drills: 0. Native body/courtyard lines are footprint graphics, not a verified socket/plate envelope.', ha='center', fontsize=10)
fig.text(.5, .085, 'Analog, mechanical, assembly and production qualification remain false. This is not the selected board.', ha='center', fontsize=11, color='#a33330')
fig.subplots_adjust(top=.87, bottom=.22, left=.06, right=.98, wspace=.12)
fig.savefig(R / 'qa/local-top-bottom-unselected.png', dpi=180)
print(R / 'qa/local-top-bottom-unselected.png')
