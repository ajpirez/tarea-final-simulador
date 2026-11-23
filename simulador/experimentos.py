"""Repite VirtualStore: tres escenarios, diez semillas, 80 clientes.

Escribe una fila por corrida, el promedio por escenario y la figura de las curvas.
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

from run import ENGINE_ROOT, N_CLIENTS, SCRIPT_PATH, STORE_MODEL_PATH, STORE_TICKS
from spl_abm.engine import SplEngine
from spl_abm.store_model import StoreFamily

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
SEEDS = tuple(range(1, 11))
SCENARIOS = ("parecidos", "distintos", "azar")
CURVES = ("pending", "accepted_as_asked", "completed_by_engine", "abandoned")

COLUMNS = (
    "escenario",
    "semilla",
    "ticks",
    "aceptados_tal_cual",
    "completados_por_el_motor",
    "abandonados",
    "pendientes",
    "productos_distintos",
    "errores_estructurales",
    "errores_restriccion",
)


def correr(engine: SplEngine, escenario: str, semilla: int):
    modelo = StoreFamily(engine, escenario, n_clients=N_CLIENTS, seed=semilla)
    for _ in range(STORE_TICKS):
        modelo.step()
        if not modelo.running:
            break
    marco = modelo.datacollector.get_model_vars_dataframe()
    ultimo = marco.iloc[-1]
    fila = {
        "escenario": escenario,
        "semilla": str(semilla),
        "ticks": str(len(marco)),
        "aceptados_tal_cual": str(int(ultimo["accepted_as_asked"])),
        "completados_por_el_motor": str(int(ultimo["completed_by_engine"])),
        "abandonados": str(int(ultimo["abandoned"])),
        "pendientes": str(int(ultimo["pending"])),
        "productos_distintos": str(int(ultimo["unique_products"])),
        "errores_estructurales": str(int(marco["structural_errors"].sum())),
        "errores_restriccion": str(int(marco["implies_errors"].sum())),
    }
    curvas = {}
    for nombre in CURVES:
        serie = [float(valor) for valor in marco[nombre]]
        ultimo_valor = serie[-1]
        curvas[nombre] = serie + [ultimo_valor] * (STORE_TICKS - len(serie))
    return fila, curvas


def _media(filas: list[dict[str, str]], escenario: str) -> dict[str, str]:
    del_escenario = [fila for fila in filas if fila["escenario"] == escenario]
    resumen = {"escenario": escenario, "repeticiones": str(len(del_escenario))}
    for columna in COLUMNS[2:]:
        valores = [float(fila[columna]) for fila in del_escenario]
        resumen[columna] = f"{sum(valores) / len(valores):.2f}"
    return resumen


def _figura(series: dict[str, dict[str, list[float]]], destino: Path, apilada: bool = False) -> None:
    if apilada:
        fig, ejes = plt.subplots(3, 1, figsize=(3.5, 7.2), sharex=True)
    else:
        fig, ejes = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True)
    colores = {
        "pending": "#9aa0a6",
        "accepted_as_asked": "#2e7d32",
        "completed_by_engine": "#e6a817",
        "abandoned": "#c62828",
    }
    leyendas = {
        "pending": "pendientes",
        "accepted_as_asked": "tal cual",
        "completed_by_engine": "corregidos",
        "abandoned": "abandonos",
    }
    for eje, escenario in zip(ejes, SCENARIOS):
        for nombre in CURVES:
            eje.plot(series[escenario][nombre], color=colores[nombre], label=leyendas[nombre])
        eje.set_title(escenario)
        eje.set_xlim(0, STORE_TICKS - 1)
    ejes[-1].set_xlabel("Tick")
    ejes[0].set_ylabel("Clientes")
    ejes[-1].legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(destino, dpi=160)
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    filas: list[dict[str, str]] = []
    acumulado = {
        escenario: {nombre: [0.0] * STORE_TICKS for nombre in CURVES}
        for escenario in SCENARIOS
    }
    conteo = {escenario: 0 for escenario in SCENARIOS}
    motor = SplEngine(ENGINE_ROOT, STORE_MODEL_PATH, SCRIPT_PATH)
    try:
        for escenario in SCENARIOS:
            for semilla in SEEDS:
                fila, curvas = correr(motor, escenario, semilla)
                filas.append(fila)
                conteo[escenario] += 1
                for nombre in CURVES:
                    for tick, valor in enumerate(curvas[nombre]):
                        acumulado[escenario][nombre][tick] += valor
                print(
                    f"{escenario} semilla {semilla}: "
                    f"tal cual {fila['aceptados_tal_cual']}, "
                    f"corregidos {fila['completados_por_el_motor']}, "
                    f"abandonos {fila['abandonados']}"
                )
    finally:
        motor.close()

    with (OUTPUT / "experimentos_corridas.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNS)
        escritor.writeheader()
        escritor.writerows(filas)

    promedios = [_media(filas, escenario) for escenario in SCENARIOS]
    campos = ["escenario", "repeticiones", *COLUMNS[2:]]
    with (OUTPUT / "experimentos_resumen.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(promedios)

    medias = {
        escenario: {
            nombre: [valor / conteo[escenario] for valor in acumulado[escenario][nombre]]
            for nombre in CURVES
        }
        for escenario in SCENARIOS
    }
    _figura(medias, OUTPUT / "experimentos_curvas.png")
    _figura(medias, OUTPUT / "experimentos_curvas_columna.png", apilada=True)
    for fila in promedios:
        print(
            f"media {fila['escenario']}: tal cual {fila['aceptados_tal_cual']}, "
            f"corregidos {fila['completados_por_el_motor']}, "
            f"abandonos {fila['abandonados']}, "
            f"productos {fila['productos_distintos']}"
        )


if __name__ == "__main__":
    main()
