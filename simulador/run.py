"""Corre los escenarios de VirtualStore."""

import csv
from pathlib import Path

from spl_abm.agents import STORE_CONCRETE
from spl_abm.engine import SplEngine
from spl_abm.store_model import StoreFamily

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parent / "spl-js-engine"
STORE_MODEL_PATH = ENGINE_ROOT / "examples" / "VirtualStore" / "model.json"
SCRIPT_PATH = HERE / "validate-batch.mjs"
OUTPUT = HERE / "output"

N_CLIENTS = 80
STORE_TICKS = 30
SEED = 1
SCENARIOS = ("parecidos", "distintos")
STORE_FEATURES = tuple((name, name) for name in sorted(STORE_CONCRETE))


def _si(present: bool) -> str:
    return "si" if present else "no"


def client_row(scenario: str, agent) -> dict[str, str]:
    asked = set(agent.initial_order)
    final = set(agent.product or ())
    row = {
        "cliente": str(agent.unique_id),
        "escenario": scenario,
        "estado": agent.status,
        "motor_completo": _si(agent.reworks > 0),
    }
    for feature, label in STORE_FEATURES:
        row[f"pidio_{label}"] = _si(feature in asked)
        row[f"producto_{label}"] = _si(feature in final)
    return row


def run_scenario(engine: SplEngine, scenario: str):
    model = StoreFamily(engine, scenario, n_clients=N_CLIENTS, seed=SEED)
    for _ in range(STORE_TICKS):
        model.step()
        if not model.running:
            break
    frame = model.datacollector.get_model_vars_dataframe()
    frame.insert(0, "scenario", scenario)
    return model, frame


def _print_summary(scenario: str, model, frame) -> None:
    last = frame.iloc[-1]
    print(f"\ntienda {scenario}")
    print(f"  aceptados tal cual:     {int(last['accepted_as_asked'])}")
    print(f"  completados por el motor: {int(last['completed_by_engine'])}")
    print(f"  abandonados:            {int(last['abandoned'])}")
    print(f"  productos distintos:    {int(last['unique_products'])}")
    products: dict[tuple[str, ...], int] = {}
    for agent in model.agents:
        if agent.product:
            products[agent.product] = products.get(agent.product, 0) + 1
    for product, count in sorted(products.items(), key=lambda item: -item[1]):
        print(f"    {count:3d}  {', '.join(product)}")


def _write_clients(path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    store = SplEngine(ENGINE_ROOT, STORE_MODEL_PATH, SCRIPT_PATH)
    try:
        store_rows: list[dict[str, str]] = []
        for scenario in SCENARIOS:
            model, frame = run_scenario(store, scenario)
            frame.to_csv(OUTPUT / f"tienda_{scenario}.csv", index_label="tick")
            store_rows.extend(client_row(scenario, agent) for agent in model.agents)
            _print_summary(scenario, model, frame)
        _write_clients(OUTPUT / "tienda_clientes.csv", store_rows)
    finally:
        store.close()


if __name__ == "__main__":
    main()
