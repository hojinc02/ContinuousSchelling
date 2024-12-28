import matplotlib.pyplot as plt
from datashader.colors import Sets1to3
from read_data import race_types

avail_races = race_types+['Mixed']
color_key = list(Sets1to3[0:len(avail_races)])
figlegend = plt.figure(figsize=(3,2))
fig,ax = plt.subplots(1,1)
scatters = [ax.scatter([0],[0], c=c) for c in color_key]
fig.show()
figlegend.legend(scatters, avail_races, loc='center')
figlegend.show()
figlegend.savefig('legend.png', bbox_inches='tight', dpi=500)
