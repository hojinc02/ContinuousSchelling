import numpy as np
import shapely
import geopandas as gpd
from read_shapefiles import load_bg
import holoviews as hv
import spatialpandas
import datashader as ds
from holoviews.operation.datashader import dynspread, datashade
import panel as pn
import param
from read_data import num_singular_groups, race_types
from shapely.geometry import MultiPolygon
import os
from os.path import join

hv.extension('bokeh')
dynspread.max_px=20
dynspread.threshold=0.5

legend = False

# Load data as before
state_name = 'California'
county_name = 'San Diego'
blockgroups = load_bg(state_name, county_name)

iters_path = f'iters_sept18'
file_names = os.listdir(iters_path)

r_coords = {}
for f in file_names: 
    if not '.npy' in f: 
        continue
    loaded = np.load(join(iters_path,f))
    if 'iter' in f: 
        iternum = int(f.replace('iter','').replace('_coords.npy',''))
        r_coords[iternum] = loaded
    elif 'races' in f: 
        r_races = loaded
r_coords = dict(sorted(r_coords.items()))
avail_iters = list(r_coords.keys())
r_races[r_races>=num_singular_groups] = num_singular_groups

# Prepare blockgroup geometry
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

minx, miny, maxx, maxy = bgs_geo.bounds
width = maxx-minx
length = maxy-miny
woh = width / length
plot_height = 700
plot_width = round(woh * plot_height)

colors = ['#FF0000', '#FFFF00', '#00FF00', '#00FFFF', '#FF00FF', '#0000FF', '#FF69B4']
dim_expr = hv.dim('k').categorize({r:colors[r] for r in range(num_singular_groups+1)})
markers = hv.Cycle(['P', 'o', 'v', '^', 's', '*', '<', '>'])

avail_races = ['All']+race_types+['Mixed']

# Define a Param class with a slider for iterations
class IterationPlot(param.Parameterized):
    iteration = param.Selector(objects=avail_iters, default=avail_iters[0])
    race_type = param.Selector(objects=avail_races, default=avail_races[0])
    def __init__(self, **params):
        super().__init__(**params)
        
        points = {i:{} for i in avail_iters}
        self.hv_points = {}
        for i in avail_iters: 

            for r in range(num_singular_groups+1): 
                rr = r_races==r
                rc = np.full((int(rr.sum()), 1), r, dtype=np.float32)
                points[i][r]=np.hstack((r_coords[i][rr], rc))

            ttt = {avail_races[0]:
                    hv.NdOverlay(
                        {f'Race {l}': hv.Points(points[i][l], ['x', 'y'], 'r') \
                        for l in range(num_singular_groups+1)}, 
                        kdims='k'
                    )
            }
            
            for r,race in enumerate(avail_races[1:]): 
                dd = {}
                for x in range(num_singular_groups+1): 
                    if x != r: 
                        dd[f'Race {x}'] = hv.Points(np.array([[(maxx-minx)/2, (maxy-miny)/2, x]]), ['x', 'y'], 'r')
                    else: 
                        dd[f'Race {x}'] = hv.Points(points[i][r], ['x', 'y'], 'r')
                ttt[race] = hv.NdOverlay(dd, kdims='k').opts(hv.opts.Points(color=dim_expr))
            self.hv_points[i]=ttt

    @param.depends('iteration', 'race_type', watch=True)
    def plot_points(self):
        return self.hv_points[self.iteration][self.race_type]

# Create an instance of the plot
iteration_plot = IterationPlot()

# Path for the blockgroup geometry
innards = hv.Path(spatialpandas.GeoDataFrame(gpd.GeoDataFrame(dict(geometry=[bgs_geo])))).opts(color='black', line_width=1.2)

# Create a DynamicMap for the points
dynamic_points = hv.DynamicMap(iteration_plot.plot_points)

points = dynspread(datashade(dynamic_points, aggregator=ds.by('k', ds.count())), 
                             threshold=0.95, shape='circle').opts(legend_position='bottom_right')


if legend: 
    from datashader.colors import Sets1to3 # default datashade() and shade() color cycle
    color_key = list(enumerate(Sets1to3[0:len(avail_races[1:])]))
    color_points = hv.NdOverlay({avail_races[k+1]: hv.Points([( (maxx-minx)/2,(maxy-miny)/2 )], label=str(k)).opts(color=v, size=0) for k,v in color_key})

    plot_panel = color_points * points * innards
else: 
    plot_panel = points * innards
    
def hook(plot, element):
    p = plot.handles['plot']
    p.axis.visible = False

nr = width/1000
plot_panel = plot_panel.opts(hooks=[hook], xlim=(minx-nr,maxx+nr), ylim=(miny-nr,maxy+nr))

# Layout with the slider
layout = pn.Row(
    pn.Spacer(styles=dict(background='white'), sizing_mode='stretch_both'),
    pn.Column(
        pn.Row('Iteration:', pn.Param(iteration_plot.param, widgets={'iteration': pn.widgets.DiscreteSlider})),
        plot_panel.opts(width=plot_width, height=plot_height)
    ),
    pn.Spacer(styles=dict(background='white'), sizing_mode='stretch_both'),
    width=1500, height=plot_height
)

# Serve the layout
pn.serve(layout, port=5066, title=f'Schelling: {state_name}, {county_name}', show=False)
