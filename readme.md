# VibeGames API

https://games.h4ks.com

Showroom for shitty vibed projects. Synced to github for easy access and collaboration.

## User data API

Projects get per-user storage and a Logto login at `/<project>/__api`. See
[docs/rows-api.md](docs/rows-api.md).

## API
```sh
cd api
poetry install
poetry run python -m app
```

## Frontend
```sh
cd frontend
npm install
npm run dev
```


## Local dev
TODO compose.yaml

```sh
make run-api
make run-frontend
make run-webcapture
```
