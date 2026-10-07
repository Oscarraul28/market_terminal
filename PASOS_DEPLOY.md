# Market Terminal — pasos para subirlo

## 1. Copia estos archivos a tu repo

Respetando la estructura de carpetas. Reemplazan a los actuales:

```
requirements.txt          <- NUEVO (borra requirements.txt.txt)
.gitignore                <- NUEVO
build.sh                  <- NUEVO
render.yaml               <- NUEVO
.env.example              <- NUEVO
config/settings.py        <- REEMPLAZA
core/views.py             <- REEMPLAZA
core/urls.py              <- REEMPLAZA
```

En Linux/Mac, `build.sh` necesita permiso de ejecución:

```bash
chmod +x build.sh
```

## 2. Saca la basura del repo

```bash
git rm -r --cached . -q
git add -A
git commit -m "Preparar para deploy: config de produccion y cache de bots"
git push
```

Esto quita `__pycache__/` y `db.sqlite3` del control de versiones
(los archivos siguen en tu disco, solo dejan de subirse).

## 3. Despliega en Render

1. render.com → New → Web Service → conecta tu repo de GitHub
2. Render detecta `render.yaml` solo. Si no lo toma:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application --timeout 120 --workers 1 --threads 4`
3. En Environment, confirma que estén:
   - `SECRET_KEY` (Render la genera sola si usa render.yaml)
   - `DEBUG` = `False`
4. Deploy.

## 4. Antes de que lleguen los jueces

El plan gratis de Render duerme el servicio tras 15 minutos sin tráfico.
Abre tu link unos 5 minutos antes: eso lo despierta y de paso deja la
caché del bloque macro caliente. La primera consulta es la lenta; todas
las demás van rápido.

Si quieres evitar que duerma del todo: configura un ping cada 10 minutos
a `https://TU-APP.onrender.com/healthz/` desde cron-job.org (gratis).

## Qué cambió y por qué

- **requirements.txt** — tenía doble extensión (`.txt.txt`), así que Render
  no lo encontraba y no instalaba nada. Además pedía Django 5.0 cuando tu
  proyecto está hecho con 6.0.4. Quité pytrends, praw, plotly y requests
  (no se usan en ningún archivo). Agregué gunicorn y whitenoise.

- **settings.py** — SECRET_KEY y DEBUG ahora salen de variables de entorno.
  ALLOWED_HOSTS se arma solo con el dominio que Render asigna. Agregué
  CSRF_TRUSTED_ORIGINS, necesario para que tu formulario POST funcione
  sobre HTTPS; sin eso Django responde 403 al analizar.

- **views.py** — los bots 1 y 2 analizan el mercado completo, no el ticker:
  daban exactamente el mismo resultado para TSLA que para AAPL, pero se
  recalculaban en cada consulta. Eran 16 descargas de un año de datos,
  repetidas cada vez. Ahora se cachean 15 minutos. Primera consulta: 21
  llamadas a Yahoo. Las siguientes: 5.

- **urls.py** — agregué `/healthz/` para el health check de Render y para
  poder mantener el servicio despierto con un ping externo.

## Pendientes que no son bloqueantes

- `db.sqlite3` sigue usándose, pero tu app no guarda nada, así que da igual
  que Render borre el disco en cada deploy.
- Los bots no tienen timeout propio en sus llamadas a Yahoo. Si Yahoo se
  pone lento un día, el `--timeout 120` de gunicorn es tu única red de
  seguridad. Para el hackathon alcanza.
