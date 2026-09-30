# Gestion_Tickets

Gestor personal de tickets de incidencias y notas de trabajo. Cada nota es un **ticket** que avanza por una serie de **pasos**, y la app te dice en cada momento qué te toca hacer a ti y qué estás esperando de otros.

Es una web local sin dependencias: un servidor en Python (solo librería estándar) y una página HTML de un solo fichero. Los datos se guardan en ficheros JSON.

## Arranque rápido

Requisitos: Python 3.8 o superior.

```bash
python server.py
```

Abre <http://localhost:8791>. En Windows también puedes hacer doble clic en `iniciar.bat`, que arranca el servidor y abre el navegador.

| Variable de entorno | Por defecto | Uso |
|---|---|---|
| `PORT` | `8791` | Puerto del servidor |
| `HOST` | `127.0.0.1` | Dirección de escucha (`0.0.0.0` para exponerlo en la red o en Docker) |
| `DATA_DIR` | `./data` | Carpeta donde se guardan los datos |

> El servidor no tiene autenticación. Mantenlo en `127.0.0.1` o detrás de una red de confianza.

## Cómo funciona

### Tickets y pasos

Un ticket es una lista de pasos, en orden. Cada paso tiene un texto y un estado:

| Estado | Significado |
|---|---|
| **A realizar** | Te toca a ti. Es el estado del primer paso de todo ticket nuevo. |
| **Pendiente** | Esperas una acción de otra persona o empresa. |
| **Realizada** | El paso está hecho. |

Ejemplo de un ticket completo:

```
Enviado correo a Sage para comentar la actualización de SQL 2019          A realizar  -> Realizada
  Quedamos a la espera de respuesta                                       Pendiente   -> Realizada
  Me ha llamado Juan Luis con las opciones, que enviará por mail          Pendiente   -> Realizada
  He recibido presupuesto y tengo que revisarlo con dirección             A realizar  -> Realizada
  Decidimos ir a cloud por flexibilidad y ahorro, falta la firma          A realizar  -> Realizada (cerrado)
```

### Flujo

1. Escribe una nota en la caja superior y pulsa Enter. Se crea el ticket con su primer paso en **A realizar**.
2. Al marcar un paso **A realizar** como Realizada, la app pregunta: *¿hay más pasos?*
   - **Se acaba aquí**: el ticket se cierra y se oculta de la vista diaria.
   - **Hay más pasos**: aparece debajo una línea nueva, con sangría, para escribir el siguiente paso. Lo guardas como **A realizar** o como **Pendiente**.
3. Al marcar un paso **Pendiente** como Realizada (la otra parte ya ha actuado), se abre automáticamente la línea siguiente, vacía.
4. Si marcas **Realizada** en esa línea vacía sin escribir nada, el ticket se cierra.

Puedes cambiar un paso entre A realizar y Pendiente pulsando su etiqueta, editar su texto (✎) y reabrir (↩) o borrar (✕) un ticket. Estos botones aparecen al pasar el ratón por encima del ticket.

### Vista "Mi día"

Agrupa los tickets abiertos en secciones:

- **Reclamar hoy**: pasos Pendientes cuya fecha de seguimiento ha llegado (ver más abajo).
- **A realizar**: lo que te toca a ti.
- **Pendiente**: lo que esperas de otros, con los días que lleva esperando.

Cada ticket tiene un borde de color según su estado: naranja (A realizar), ámbar (Pendiente), rojo (Reclamar) y verde (cerrado).

### Contraer y expandir

Los tickets con más de un paso tienen una flecha (▾/▸). Contraído, se ve la primera línea y un resumen con el número de pasos restantes, el **estado actual** del ticket y el texto del paso en curso. Hay también botones **Contraer todo / Expandir todo**. El navegador recuerda lo que dejaste contraído.

### Fecha de seguimiento

Cada paso Pendiente puede llevar una fecha de seguimiento (selector de fecha en la línea, o "Recordar el" al crear el paso). Cuando llega ese día, el ticket sube a **Reclamar hoy** con una etiqueta roja, para que no se quede olvidado.

### Búsqueda

La caja de la cabecera busca en todo el texto de los tickets, **incluidos los cerrados**, y en los contactos:

- No distingue mayúsculas ni acentos.
- Un teléfono se encuentra aunque lo escribas con otro formato (`600 111 222`, `600111222`).
- Los resultados salen de más reciente a más antiguo, según la última actividad.
- Si buscas una empresa o una persona, salen también los tickets enlazados a sus contactos.

### Contactos

La pestaña **Contactos** guarda nombre, empresa, puesto, teléfono y correo, agrupados por empresa. Cada contacto muestra los tickets en los que aparece.

- **Mencionar con `@`**: en cualquier nota o paso, escribe `@Juan` y aparece la lista de todos los Juan, con empresa, teléfono y correo. `@sage` muestra todos los contactos de Sage. Se elige con las flechas y Enter (o con el ratón). La mención queda como una etiqueta azul; al pulsarla se abre el contacto.
- **Alta automática**: al guardar una nota con un teléfono o correo que no tengas, se abre un formulario ya relleno. Con "he hablado con Laura de Fortinet al 699 888 777" propone *Laura*, *Fortinet* y el teléfono (y si hay correo, deduce la empresa del dominio). Confirmas o corriges. Funciona con reglas, sin IA y sin conexión a internet.

### Copias de seguridad

- Se guarda una copia automática al día en `data/backups/backup-AAAA-MM-DD.json` (la primera del día y al arrancar). Se conservan las últimas 30.
- **Exportar** descarga todos los tickets y contactos en un único JSON.
- **Importar** restaura desde ese fichero, reemplazando los datos actuales. Antes guarda una copia `pre-import-*.json` por si te arrepientes.

## Estructura

```
server.py          Servidor HTTP (librería estándar) y API JSON
static/index.html  Toda la interfaz (HTML + CSS + JS)
data/              Datos: tickets.json, contacts.json, backups/   (no se sube al repo)
iniciar.bat        Arranque en Windows
```

### API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/tickets`, `/api/contacts` | Lista completa |
| PUT | `/api/tickets/<id>`, `/api/contacts/<id>` | Crea o reemplaza un elemento |
| DELETE | `/api/tickets/<id>`, `/api/contacts/<id>` | Borra un elemento |
| GET | `/api/export` | Descarga todo en un JSON |
| POST | `/api/import` | Restaura desde un JSON exportado |

### Modelo de datos

```jsonc
// ticket
{ "id": "...", "created": "ISO", "updated": "ISO", "closed": null,
  "lines": [ { "text": "...", "status": "A realizar|Pendiente|Realizada",
               "created": "ISO", "done": null, "remind": "AAAA-MM-DD", "contacts": ["id"] } ] }
// contacto
{ "id": "...", "name": "", "company": "", "role": "", "phone": "", "email": "" }
```

## Hoja de ruta

- Dockerfile / docker-compose.
- Deshacer, atajos de teclado, pestaña de tickets cerrados y resumen con contadores.
