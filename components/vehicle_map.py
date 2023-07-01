import folium
import pandas as pd
import pytz
import streamlit as st
from shapely.geometry import Point, Polygon
from streamlit_folium import folium_static
from components.active_blocks import get_active_blocks
from calls.supa_select import supabase_active_location


def move_to_vehicle_location(pos, m):
    # Update the map's center to the vehicle's position
    m.location = pos
    # Re-render the map
    folium_static(m)


def vehicle_map(vehicle):
    # TODO: rewrite to just select vehicle
    df = supabase_active_location()
    df = df[df['coach'] == vehicle]
    df = df.sort_values(by=['created_at'], ascending=False)
    df = df.drop_duplicates(subset=['coach'], keep='first')
    
    if len(df) == 0:
        pass
    else:

        # round lat and long to 6 decimal places
        df['lat'] = df['lat'].round(6)
        df['long'] = df['long'].round(6)

        # convert date to california time and format
        california_tz = pytz.timezone('US/Pacific')
        df['created_at'] = pd.to_datetime(df['created_at'])
        # df['created_at'] = df['created_at'].dt.tz_convert(california_tz)
        df['created_at'] = df['created_at'].dt.strftime('%m/%d/%y %I:%M %p')
        df['speed'] = df['speed'].astype(int).astype(str) + " mph"

                
        # Define the polygon coordinates of the depot
        depot_coordinates = [
            [37.41999522465071, -121.93949237138894],
            [37.41649876221854, -121.93810797555054],
            [37.41748834361772, -121.932785425544],
            [37.42105072840012, -121.93267467387127],
        ]

        depot_polygon = Polygon(depot_coordinates)

        location = check_location(df, depot_polygon, vehicle)
        loc_str = f'{location}'
        st.subheader(f"Current Location: {loc_str}")
        # st.write(df)
        

        # get the first row of the dataframe
        # st.write(df)
        row = df.iloc[0, :]

        m = folium.Map(location=[row['lat'], row['long']], zoom_start=15)


        folium.Polygon(depot_coordinates, color='red', fill=True, fill_color='red', fill_opacity=0.2).add_to(m)

        # add markers to map
        popup_text = f"Coach: {row['coach']}" \
                        f"<br>Latitude: {row['lat']}" \
                        f"<br>Longitude: {row['long']}" \
                        f"<br>Speed: {row['speed']} " \
                        f"<br>Last Transmission: {row['created_at']}"
        folium.Marker(location=[row['lat'], row['long']], popup=popup_text).add_to(m)

        folium_static(m)


def check_location(df, depot_polygon, vehicle = None):
    df['point'] = [Point(xy) for xy in zip(df['lat'], df['long'])]
    df['at_depot'] = df.apply(
        lambda row: row['point'].within(depot_polygon), axis=1)
    merged_df = get_active_blocks()
    df['location'] = df.apply(
        lambda row: 'Depot' if row['at_depot']
        else "Block " + str(merged_df[merged_df['coach'] == row['coach']].iloc[0, 1]) if row['coach'] in merged_df[
            'coach'].values
        else 'Unlisted', axis=1)
    
    tolerance = 0.0001
    
    if vehicle is None:
        df = df.drop(columns=['created_at'])
        buffered_polygon = depot_polygon.buffer(tolerance)
        
        df = df.sort_values(by=['coach'])
        df = df.drop(columns=['point', 'at_depot'])
        return df['location']
    else:
        return df['location'].iloc[0]
        