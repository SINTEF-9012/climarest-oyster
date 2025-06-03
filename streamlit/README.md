# ClimaREST Oyster

![Frontend Screenshot](screenshots/app.png?raw=true)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Data

⚠️ There exists a file called `galicia_mussel_farms.geojson`. The repository has two copies of the file -- one in `../data` and one in `./streamlit/app`. This is because Docker cannot access a file outside its own build context. If you update the file, make sure it updates in both locations.

## Prerequisites

```sh
$ mamba create --name climarest python=3.11
$ mamba activate climarest
$ mamba install streamlit xarray matplotlib plotly numpy pandas cartopy cmocean python-dotenv shapely copernicusmarine geopandas
```

You also need `.env` file with your API credentials for the [Copernicus Marine Service](https://marine.copernicus.eu). If you do not have any credentials, you need to register on the site.

The `.env` file should look like this:

```sh
$ cd ./streamlit
$ cat .env
CMEMS_USER=you@yourdomain.com
CMEMS_PASS=password
```

## Development

You can run the dashboard with

```sh
$ cd ./streamlit
$ streamlit run app/main.py
```

If you don't want the browser to pop up, do this instead

```sh
$ cd ./streamlit
$ streamlit run app/main.py --server.headless true
```

## Running in Docker

Build:

```sh
$ cd ./streamlit
$ docker build --tag climarest-mussels .
```

Run:

```sh
$ cd ./streamlit
$ docker run --interactive \
    --env-file ./.env \
    --tty \
    --publish 14858:14858 \
    climarest-mussels
```

Then point your browser to [http://localhost:1458](http://localhost:1458).

## Contact and Blame

- Volker Hoffmann (volker.hoffmann@sintef.no)
