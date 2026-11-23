# Simulación: familia VirtualStore

Los agentes piden una compra en la tienda. [spl-js-engine](../spl-js-engine) dice si ese pedido es un miembro legal de la familia, con `completeFeatureSelection`.

La simulación utiliza solo el completado y la validación del motor; no genera el código de la tienda. Cada cliente es un agente BDI: cree que su pedido es el correcto, desea que lo acepten y, si el motor lo rechaza, aplica una reparación por tick, que en la política dirigida puede modificar varias features.

## Qué mide

Tres escenarios, 80 clientes, tope de 30 ticks:

- `parecidos`: pedidos bien armados (al menos un rubro, un pago y un canal). Las reglas `implies` pueden fallar.
- `distintos`: cada cliente sortea un subconjunto de las 32 features solicitables (33 concretas en el modelo, incluido el carrito).
- `azar`: el pedido se sortea y, en cada fallo, la corrección también.

Si el pedido ya servía, queda aceptado tal cual. Si el motor agrega solo el carrito, también. Si hace falta otra corrección, el cliente aplica una reparación por tick. A los 30 intentos abandona.

## Cómo correrlo

Hace falta Node, bun y Python 3.11+. El motor está en `spl-js-engine`, dentro de este repositorio.

```powershell
cd spl-js-engine
bun install --ignore-scripts
cd ..\simulador
python -m venv .venv
.\.venv\Scripts\python -m pip install "mesa[viz]" matplotlib
.\.venv\Scripts\python run.py
```

`run.py` corre `parecidos` y `distintos` con la semilla 1. Los CSV quedan en `simulador/output/`.

Para las diez semillas de los tres escenarios, la tabla de promedios y la figura de las curvas:

```powershell
.\.venv\Scripts\python experimentos.py
```

Para ver una corrida en el navegador, con play y paso a paso:

```powershell
.\.venv\Scripts\solara run viz.py
```

Cada cuadrado es un cliente. Verde: el pedido ya servía. Amarillo: hubo que corregirlo. Gris: pendiente. Rojo: abandonó. El borde negro es el agente que se está leyendo.

## Columnas

`experimentos_corridas.csv` tiene una fila por escenario y semilla. `experimentos_resumen.csv` promedia esas filas.

- `aceptados_tal_cual`: el primer pedido ya era un producto, o el motor solo agregó el carrito.
- `completados_por_el_motor`: el cliente tuvo que corregir el pedido y aun así fue aceptado.
- `abandonados`: llegó a 30 intentos sin un producto.
- `pendientes`: seguían sin cerrar al detenerse la corrida.
- `productos_distintos`: configuraciones finales distintas.
- `errores_estructurales`: rechazos por la forma del pedido (grupo vacío, grupo con más de un miembro).
- `errores_restriccion`: rechazos por una regla `implies`.
