import geopandas as gpd

class Notes: 
    state_bg_filepaths = {
        'Alabama': r'/home/hmchang/networkProject/Geopandas/shapefiles/alabama/tl_2020_01_bg.shp',
        'California': r'/home/hmchang/networkProject/Geopandas/shapefiles/california/tl_2020_06_bg.shp'
    }

    county_codes = {
        'San Diego': '06073'
    }

    state_filepath= r'/home/hmchang/networkProject/Geopandas/shapefiles/states/tl_2020_us_state.shp'

def load_bg(state_name, county=None): 
    
    bg = gpd.read_file(Notes.state_bg_filepaths[state_name], columns=['geometry', 'GEOID'])
    if county is not None: 
        county_code = Notes.county_codes[county]
        bg = bg[bg['GEOID'].str.startswith(county_code)]
        
    #state = gpd.read_file(Notes.state_filepath, columns=['geometry', 'NAME'])
    #state.drop(index=state[state.NAME!=state_name].index, inplace=True)
    
    return bg