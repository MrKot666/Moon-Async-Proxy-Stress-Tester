# Moon-Async-Proxy-Stress-Tester
Async proxy stress tester in Python. Hobby / learning project to experiment with asyncio, aiohttp and high concurrency. Expect bugs.


# Async Proxy Stress Tester

> Proyecto hecho por curiosidad, aprendizaje y ganas de experimentar con async en Python.
> No es perfecto, no es serio, y seguramente se puede romper

---

## 🇪🇸 Español

### ¿Que es esto?

Este script es basicamente un experimento para:

* Jugar con **asyncio** y **aiohttp**
* Enviar muchas peticiones HTTP al mismo tiempo
* Usar **proxies SOCKS5**
* Ver estadisticas en tiempo real desde la terminal

No es una herramienta profesional ni pretende serlo. Es mas un “a ver que pasa si…” convertido en codigo.

---

### ¿Que hace?

* Envia peticiones HTTP de forma asincrona a una URL
* Usa proxies desde:

  * Un archivo (`proxies.txt`)
  * O descargados automaticamente de internet
* Rota:

  * Proxies
  * User-Agents
  * Headers
  * Metodos HTTP
* Muestra estadisticas en vivo:

  * Requests totales
  * Exitos / fallos
  * RPS aproximado
* Guarda un resumen final en `stress_results.json`

---

### Como usarlo

#### Requisitos

* Python **3.9+** recomendado
* Instalar dependencias:

```bash
pip install aiohttp
```

---

#### Proxies

Tienes dos opciones:

**Opcion A – Archivo de proxies**

Crea un archivo `proxies.txt` con este formato:

```
ip:puerto
ip:puerto:usuario:contraseña
```

Ejemplo:

```
127.0.0.1:1080
1.2.3.4:1080:user:pass
```

---

**Opcion B – Auto-fetch (mas facil)**

El script puede descargar y testear proxies publicos automaticamente usando el flag `-f`.

---

####  Ejecutar el script

Ejemplo basico:

```bash
python moon.py https://example.com
```

Ejemplo con mas control:

```bash
python moon.py https://example.com \
  -c 1000 \
  -r 3000 \
  -d 60 \
  -f
```

---

### Parametros disponibles

| Parametro            | Descripcion                                   |
| -------------------- | --------------------------------------------- |
| `url`                | URL objetivo (obligatoria)                    |
| `-c`, `--concurrent` | Conexiones simultaneas (default: 2000)        |
| `-r`, `--rps`        | Requests por segundo objetivo (default: 5000) |
| `-d`, `--duration`   | Duracion en segundos (0 = infinito)           |
| `-p`, `--proxies`    | Archivo de proxies                            |
| `-f`, `--fetch`      | Descargar proxies automaticamente             |

---

### Cosas importantes 

* Puede consumir **muchos recursos**
* No todos los proxies funcionan
* Puede fallar, colgarse o comportarse raro
* No esta optimizado ni pulido al 100%

usalo con cabeza.

---

### Nota legal / etica

Este proyecto es solo para **aprendizaje y pruebas tecnicas**
No me hago responsable del uso que otros le den.

---

### ¿Se puede modificar?

Si, totalmente.

* Cambia lo que quieras
* Rompe cosas
* Arreglalas
* Aprende algo en el proceso

---

---

## 🇬🇧 English

### What is this?

This is basically a learning / hobby project made to experiment with:

* **asyncio** and **aiohttp**
* High concurrency HTTP requests
* SOCKS5 proxies
* Real-time terminal stats

It’s not meant to be professional or production-ready.

---

### What does it do?

* Sends async HTTP requests to a target URL
* Uses SOCKS5 proxies from:

  * A file
  * Or fetched automatically online
* Rotates:

  * Proxies
  * User-Agents
  * Headers
  * HTTP methods
* Shows live stats in terminal
* Saves final results to `stress_results.json`

---

### How to use it

#### Requirements

* Python **3.9+**
* Install dependencies:


pip install aiohttp


---

####  Proxies

**Option A – Proxy file**

Create a `proxies.txt` file:


ip:port
ip:port:username:password


---

**Option B – Auto-fetch**

Use `-f` to automatically download and test public proxies.

---

####  Run it

Basic example:


python moon.py https://example.com


Advanced example:


python moon.py https://example.com \
  -c 1000 \
  -r 3000 \
  -d 60 \
  -f


---

### Available arguments

| Argument             | Description                |
| -------------------- | -------------------------- |
| `url`                | Target URL (required)      |
| `-c`, `--concurrent` | Max concurrent connections |
| `-r`, `--rps`        | Target requests per second |
| `-d`, `--duration`   | Duration in seconds        |
| `-p`, `--proxies`    | Proxy file                 |
| `-f`, `--fetch`      | Auto-fetch proxies         |

---

### Disclaimer

* May contain bugs
* Uses a lot of resources if pushed too hard
* Public proxies are unreliable
* Not optimized or cleaned up perfectly

Use at your own risk.

---

### Final note

This is a **learning project**, not a finished product.
Feel free to tweak, break, fix or improve anything.

