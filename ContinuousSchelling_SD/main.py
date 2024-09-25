import numpy as np
import math
import shapely
from shapely.vectorized import contains
from tqdm import tqdm
from read_data import load_data
from read_shapefiles import load_bg
import holoviews as hv
from copy import deepcopy
from read_data import all_types, num_singular_groups
from shapely.geometry import MultiPolygon
import os
from time import time

hv.extension('bokeh')

max_iters = 20
radius_ratio = 1e-3
s_threshold = 0.3
pbuffer = 0.1
random_start = True
seed = None
savedir = f'iters_{"randominit_" if random_start else "_"}F-{s_threshold:.3f}_sept24'
basedir = '/home/hmchang/networkProject/'
os.makedirs(os.path.join(basedir, savedir), exist_ok=True)

state_name = 'California'
county_name = 'San Diego'

rng = np.random.default_rng(seed)

_pop_data = load_data()
blockgroups = load_bg(state_name, county_name)
# Parallel arrays constructed ensuring same GEOID
pop_data = [_pop_data[id] for id in blockgroups['GEOID']]
bg_geos = blockgroups['geometry'].tolist()
flatten_geos = []
for g in bg_geos: 
    if hasattr(g, 'geoms'): 
        flatten_geos.extend(g.geoms)
    else: 
        flatten_geos.append(g)
bgs_geo = MultiPolygon(flatten_geos)
for p in bg_geos: shapely.prepare(p)
shapely.prepare(bgs_geo)

pnum = np.array([int(sum(p.values())) for p in pop_data])

minx, miny, maxx, maxy = bgs_geo.bounds

width = maxx-minx
length = maxy-miny
woh = width / length
n_radius = width * radius_ratio
num_residents = int(pnum.sum())
max_pnum = (pnum*(1+pbuffer)).round().astype(int)

bottomleft = np.array([minx,miny])
def spatial_hash(c): # c.shape=(N,2)|(2,)
    hashed_arr = np.floor((c-bottomleft)/n_radius).astype(int)
    if hashed_arr.ndim == 1: 
        return tuple(hashed_arr.tolist())
    else: 
        return [tuple(h.tolist()) for h in hashed_arr]

r_races = np.empty((num_residents,), dtype=np.uint8)
r_coords = np.empty((num_residents,2), dtype=np.float32)
r_bg = np.empty((num_residents,), dtype=np.uint32)

j=0
for pidx, (p,pn,d) in tqdm(enumerate(zip(bg_geos, pnum, pop_data)), desc=f'Initial locations'): 
    r_bg[j:j+pn] = pidx
    pxmin,pymin,pxmax,pymax=p.bounds
    i=pn
    while i > 0: 
        randcoords_x = rng.uniform(pxmin,pxmax,(i,))
        randcoords_y = rng.uniform(pymin,pymax,(i,))
        inside = contains(p, randcoords_x, randcoords_y)
        num_inside = int(np.sum(inside))
        r_coords[j+i-num_inside:j+i,0] = randcoords_x[inside]
        r_coords[j+i-num_inside:j+i,1] = randcoords_y[inside]
        i-=num_inside
    t=0
    for k,v in d.items(): 
        r_races[j+t:j+t+v]=k
        t+=v
    j+=pn

if random_start: 
    rng.shuffle(r_races)

#coord_boxes = {}
num_x_boxes, num_y_boxes = math.ceil(width/n_radius), math.ceil(length/n_radius)
#for x in range(num_x_boxes): 
#    for y in range(num_y_boxes): 
#        cell_box = box(minx+x*n_radius,miny+y*n_radius,minx+(x+1)*n_radius,miny+(y+1)*n_radius)
#        if bgs_geo.boundary.intersects(cell_box): 
#            coord_boxes[(x,y)] = set()
coord_boxes = np.empty((num_x_boxes,num_y_boxes), dtype=object)
coord_boxes = np.vectorize(lambda _: set())(coord_boxes)
hashed_coords = spatial_hash(r_coords)
for r, hc in enumerate(hashed_coords): 
    coord_boxes[hc].add(r)

x_box_offsets, y_box_offsets = np.meshgrid([-1,0,1], [-1,0,1], indexing='ij')
x_box_offsets = x_box_offsets.flatten()
y_box_offsets = y_box_offsets.flatten()

cpnum = deepcopy(pnum)


np.save(os.path.join(basedir,savedir,'races.npy'), r_races)
np.save(os.path.join(basedir,savedir,'iter0_coords.npy'), r_coords)

binary_races = np.zeros((num_residents,num_singular_groups),dtype=bool)
rows = []
cols = []
for r in range(num_residents):
    rows.extend([r] * len(all_types[r_races[r]]))
    cols.extend(all_types[r_races[r]])
binary_races[rows,cols] = 1

with tqdm(total=max_iters*num_residents, desc=f'Iteration 1 (max={max_iters})') as pbar: 
    for iteration in range(max_iters): 
        start_time = time()
        satisfied = 0
        for r, (coord, race) in enumerate(zip(r_coords, r_races)): 

            hx, hy = spatial_hash(coord)
            box_idx_x, box_idx_y = hx + x_box_offsets, hy + y_box_offsets

            valid_box_idx = (box_idx_x >= 0) & (box_idx_x < coord_boxes.shape[0]) & \
                            (box_idx_y >= 0) & (box_idx_y < coord_boxes.shape[1])
            boxes_to_check = coord_boxes[box_idx_x[valid_box_idx], box_idx_y[valid_box_idx]]
            to_compare = np.array(np.concatenate([[c for c in box_to_check if c != r] for box_to_check in boxes_to_check]).astype(int))

            distances = np.linalg.norm(coord - r_coords[to_compare], ord=2, axis=1)
            in_radius_idx = to_compare[distances < n_radius]
            if in_radius_idx.shape[0] == 0: 
                frac = 0
            else: 
                anded = binary_races[r] & binary_races[in_radius_idx]
                ored = np.zeros((in_radius_idx.shape[0],), dtype=bool)
                for rrr in range(num_singular_groups): 
                    ored |= anded[:,rrr]
                same_count = int(np.sum(ored))
                frac = same_count / in_radius_idx.shape[0]

            if frac < s_threshold: 
                chosen_pi = rng.choice(np.arange(len(bg_geos))[cpnum<max_pnum])
                p = bg_geos[chosen_pi]
                pxmin,pymin,pxmax,pymax=p.bounds
                while True: 
                    new_x = rng.uniform(pxmin, pxmax)
                    new_y = rng.uniform(pymin, pymax)
                    if contains(p, new_x, new_y): 
                        break
                r_coords[r,0] = new_x
                r_coords[r,1] = new_y
                new_hx, new_hy = spatial_hash(r_coords[r,:])
                if new_hx != hx or new_hy != hy: 
                    coord_boxes[hx, hy].remove(r)
                    coord_boxes[new_hx, new_hy].add(r)
                cpnum[chosen_pi] += 1
                cpnum[r_bg[r]] -= 1
                r_bg[r] = chosen_pi
            else: 
                satisfied += 1

            pbar.update(1)

        np.save(os.path.join(basedir,savedir,f'iter{iteration+1}_coords.npy'), r_coords)

        end_time = time()
        if satisfied == num_residents: 
            pbar.set_description(f'Iteration {iteration+1} (max={max_iters}) [Early Stopped]')
            #print(f'Iteration {iteration+1} (max={max_iters}) time={(end_time-start_time)/60:.1f}m [Early Stopped]')
            break
        pbar.set_description(f'Iteration {iteration+1} (max={max_iters})')
        #print(f'Iteration {iteration+1} (max={max_iters}) time={(end_time-start_time)/60:.1f}m')

'''
plot_height = 700
plot_width = round(woh * plot_height)
colors = ['red', 'blue', 'green', 'orange', 'yellow', 'pink', 'brown']

points = []
for i in range(7): 
    rr = r_races==i
    rc = np.ones((int(rr.sum()),1), dtype=np.float32) * i
    points.append(np.hstack((r_coords[rr],rc)))
points = {f'Race {i}': hv.Points(points[i], ['x', 'y'], 'r').opts(color=colors[i]) for i in range(7)}
points = datashade(hv.NdOverlay(points, kdims='k'), aggregator=ds.by('k', ds.count()))
points = dynspread(points, threshold=0.999)

innards = hv.Path(spatialpandas.GeoDataFrame(gpd.GeoDataFrame(dict(geometry=[bgs_geo])))).opts(color='black', line_width=1.2)

plot_panel = points * innards

layout = panel.Row(
    panel.Spacer(styles=dict(background='white'), sizing_mode='stretch_both'),
    plot_panel.opts(width=plot_width, height=plot_height),
    panel.Spacer(styles=dict(background='white'), sizing_mode='stretch_both'),
    width=1500, height=plot_height
)
panel.serve(panels=layout, port=5066, title=f'Schelling: {state_name}, {county_name}', show=False)

'''