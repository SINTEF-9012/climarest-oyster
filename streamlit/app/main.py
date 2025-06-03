import datetime
import os

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean
import copernicusmarine
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
import streamlit as st
import xarray as xr
from dotenv import load_dotenv

########################################################################
########################################################################
########################################################################
# FUNCTIONS
########################################################################
########################################################################
########################################################################


def _load_locations():
    # fname = "../data/galicia_mussel_farms.geojson"
    # gdf_aoi = gpd.read_file(fname)
    # # return gdf_aoi.head(1).geometry.bounds
    # return gdf_aoi.head(1).geometry.bounds.values.tolist()[0]
    gdf_aoi = gpd.read_file("app/galicia_mussel_farms.geojson")
    gdf_aoi["centroid"] = gdf_aoi.geometry.to_crs(epsg=25830).centroid.to_crs(epsg=4326)
    return gdf_aoi


@st.cache_data
def _load_and_average_ocean_data_for_location(bounds, tlo, thi):
    xlo, ylo, xhi, yhi = bounds
    data_request = {
        "dataset_id": "cmems_mod_ibi_phy_anfc_0.027deg-2D_PT1H-m",
        "longitude": [xlo, xhi],
        "latitude": [ylo, yhi],
        "time": [tlo, thi],
        "variables": ["thetao", "zos"],
    }
    dset = copernicusmarine.open_dataset(
        dataset_id=data_request["dataset_id"],
        minimum_longitude=data_request["longitude"][0],
        maximum_longitude=data_request["longitude"][1],
        minimum_latitude=data_request["latitude"][0],
        maximum_latitude=data_request["latitude"][1],
        start_datetime=data_request["time"][0],
        end_datetime=data_request["time"][1],
        variables=data_request["variables"],
    )
    df = dset.to_dataframe()
    df = df.groupby("time").agg(
        {
            "thetao": "mean",
            "zos": "mean",
        }
    )
    return df


@st.cache_data
def _load_and_average_ocean_data_for_all_locations(_locations, tlo, thi):
    frames = {}
    for row in locations.itertuples():
        frames[row.name] = _load_and_average_ocean_data_for_location(
            shapely.bounds(row.geometry),
            tlo,
            thi,
        )
    return frames


def _load_ocean_data_for_map(bounds, tlo, thi):
    xlo, ylo, xhi, yhi = bounds
    data_request = {
        "dataset_id": "cmems_mod_ibi_phy_anfc_0.027deg-2D_PT1H-m",
        "longitude": [xlo, xhi],
        "latitude": [ylo, yhi],
        "time": [tlo, thi],
        "variables": ["thetao", "zos"],
    }
    dset = copernicusmarine.open_dataset(
        dataset_id=data_request["dataset_id"],
        minimum_longitude=data_request["longitude"][0],
        maximum_longitude=data_request["longitude"][1],
        minimum_latitude=data_request["latitude"][0],
        maximum_latitude=data_request["latitude"][1],
        start_datetime=data_request["time"][0],
        end_datetime=data_request["time"][1],
        variables=data_request["variables"],
    )
    return dset


########################################################################
########################################################################
# STREAMLIT INIT
########################################################################
########################################################################

# ---------- Configuration ----------
st.set_page_config(layout="wide")
st.title("🌊 Climate Monitoring Dashboard")

########################################################################
########################################################################
# LOGIC INIT
########################################################################
########################################################################

load_dotenv()
CMEMS_USER = os.getenv("CMEMS_USER")
CMEMS_PASS = os.getenv("CMEMS_PASS")
if copernicusmarine.login(
    username=CMEMS_USER, password=CMEMS_PASS, force_overwrite=True
):
    st.toast("CMEMS Login Successfull")
else:
    st.error("CMEMS Login Failed ")

# Site Locations
locations = _load_locations()

# Timestamps of Interest
now = datetime.datetime.now()
tlo = datetime.datetime(now.year, now.month, now.day, now.hour)
thi = (tlo + datetime.timedelta(hours=24)).isoformat()
tlo = tlo.isoformat()

# Map Boundaries
map_bounds = [-9.5, 42.0, -8.5, 43.0]

# Load Ocean Data for Sites
frames = _load_and_average_ocean_data_for_all_locations(locations, tlo, thi)

# Load Ocean Data for Map
dset = _load_ocean_data_for_map(map_bounds, tlo, thi)

########################################################################
########################################################################
# STREAMLIT STUFF
########################################################################
########################################################################

# ---------- Time Selection ----------
st.sidebar.header("🕒 Time Control (Map Only)")
time_options = pd.date_range(tlo, thi, freq="h").to_pydatetime()
selected_time = st.sidebar.slider(
    "Select Time",
    min_value=time_options[0],
    max_value=time_options[-1],
    step=datetime.timedelta(hours=1),
    value=time_options[0],
    format="ddd HH:mm",
)

# Sidebar or within col1
st.sidebar.header("🗺️ Map Settings")
map_variable = st.sidebar.radio(
    "Select Variable for Map", ["Temperature", "Sea Surface Above Geoid"]
)


# ---------- User Thresholds ----------
st.sidebar.header("🚨 Alarm Thresholds")
temp_thresh = st.sidebar.slider(
    "Temperature Threshold (°C)", min_value=0, max_value=25, value=15, step=1
)
sea_thresh = st.sidebar.slider(
    "Sea Surface Above Geoid Threshold (m)",
    min_value=0.0,
    max_value=2.0,
    value=1.0,
    step=0.1,
)

# # ---------- Select Locations ----------
# locations = {
#     "Ría de Arousa": (-8.85, 42.61002),
#     "Ría de Vigo": (-8.73, 42.26002),
#     "Ría de Pontevedra": (-8.78, 42.39001),
#     "Ría de Muros e Noia": (-8.96501, 42.79503),
# }

# ---------- Alarm Evaluation ----------
alarm_triggered = False
alarm_messages = []

# for site, (lat, lon) in locations.items():
for i, (site_name, df) in enumerate(frames.items()):
    ts_temp = df.thetao
    ts_sea = df.zos

    if (ts_temp > temp_thresh).any():
        alarm_triggered = True
        alarm_messages.append(f"🚨 {site_name}: Temperature Threshold Exceeded")
    if (ts_sea > sea_thresh).any():
        alarm_triggered = True
        alarm_messages.append(
            f"🌊 {site_name}: Sea Surface (Above Geoid) Threshold Exceeded"
        )

# ---------- Display Alarm Widget ----------
st.subheader("🔔 Alarm Status")

if alarm_triggered:
    for msg in alarm_messages:
        st.error(msg)
else:
    st.success("✅ All values within safe thresholds.")


# ---------- Layout ----------
col1, col2 = st.columns([1, 1])

# ---------- Map View (col1) ----------
with col1:
    st.subheader(f"🗺️ Map Overview ({selected_time.strftime('%a, %d %B, %H:%M')})")

    # Select variable
    if map_variable == "Temperature":
        var_data = dset.thetao.sel(time=selected_time, method="nearest")
        var_label = "Temperature (°C)"
        cmap = cmocean.cm.thermal
        vmin = None
        vmax = None
    else:
        var_data = dset.zos.sel(time=selected_time, method="nearest")
        var_label = "Sea Surface Above Geoid (m)"
        cmap = "viridis"
        vmin = None
        vmax = None
        # cmap = cmocean.cm.balance_r
        # vmin = -1.0
        # vmax = 1.0

    # Choose the projection
    proj = ccrs.PlateCarree()

    # Create pcolormesh plot
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={"projection": proj})

    # Add map features
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue")
    ax.gridlines(draw_labels=True)

    # Plot actual data
    mesh = ax.pcolormesh(
        dset.longitude,
        dset.latitude,
        var_data.values,
        cmap=cmap,
        shading="auto",
        vmin=vmin,
        vmax=vmax,
    )
    cbar = plt.colorbar(mesh, ax=ax, label=var_label)

    # Add site locations
    for row in locations.itertuples():
        ax.plot(
            row.centroid.x,
            row.centroid.y,
            marker="*",
            color="black",
            markersize=4**2,
            transform=ccrs.PlateCarree(),
        )
        ax.text(
            row.centroid.x + 0.04,
            row.centroid.y + 0.04,
            row.name,
            transform=ccrs.PlateCarree(),
            fontsize=9,
            color="black",
            bbox=dict(facecolor="orange", alpha=0.9),
        )

    ax.set_title(f"{var_label} at {selected_time.strftime('%a, %d %B, %H:%M')}")
    # # ax.set_xlabel("Longitude")
    # # ax.set_ylabel("Latitude")
    # # ax.set_aspect("auto")
    ax.set_xlim([map_bounds[0], map_bounds[2]])
    ax.set_ylim([map_bounds[1], map_bounds[3]])
    st.pyplot(fig)


# ---------- Time Series (col2) ----------
with col2:
    st.subheader("📈 Time Series for Key Locations")
    fig_ts, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
    for i, (site_name, df) in enumerate(frames.items()):
        ts_temp = df.thetao
        ts_sea = df.zos
        axs[i].plot(
            ts_temp.index, ts_temp.values, label="Temperature (°C)", color="red"
        )
        axs[i].plot(
            ts_sea.index,
            ts_sea.values,
            label="Sea Surfac Above Geoid (m)",
            color="blue",
        )
        axs[i].set_title(f"{site_name}")
        axs[i].legend(loc="upper right")
        axs[i].grid(True)

    st.pyplot(fig_ts)
