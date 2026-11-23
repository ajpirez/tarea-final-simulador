"""Vista en el navegador: cada cliente de VirtualStore y los conteos de la corrida."""

import random
import threading

import pandas as pd
import solara
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch

from run import ENGINE_ROOT, SCRIPT_PATH, STORE_MODEL_PATH
from spl_abm.engine import SplEngine
from spl_abm.store_model import StoreFamily

store_engine = SplEngine(ENGINE_ROOT, STORE_MODEL_PATH, SCRIPT_PATH)

STORE_FEATURES = [
    "structural_errors",
    "implies_errors",
    "feature_cart",
    "feature_login",
    "feature_invoice",
]


def new_seed() -> int:
    return random.randrange(1, 10000)


def _blank(fig: Figure) -> None:
    fig.patch.set_facecolor("white")


def client_board(model, revision: int, followed: int):
    caption = (
        "Verde: el pedido ya servía.  Amarillo: hubo que corregirlo.  "
        "Gris: pendiente.  Rojo: abandonó."
    )
    fig = Figure(figsize=(10, 3.4))
    _blank(fig)
    ax = fig.subplots()
    ax.set_facecolor("white")
    agents = list(model.agents)
    columns = 16
    xs = []
    ys = []
    colors = []
    edgecolors = []
    linewidths = []
    for index, agent in enumerate(agents):
        if agent.status == "pending":
            color = "#9aa0a6"
        elif agent.status == "abandoned":
            color = "#c62828"
        elif agent.reworks:
            color = "#e6a817"
        else:
            color = "#2e7d32"
        xs.append(index % columns)
        ys.append(-(index // columns))
        colors.append(color)
        if index == followed - 1:
            edgecolors.append("#000000")
            linewidths.append(2.4)
        else:
            edgecolors.append(color)
            linewidths.append(0.3)
    if xs:
        ax.scatter(
            xs,
            ys,
            c=colors,
            s=140,
            marker="s",
            edgecolors=edgecolors,
            linewidths=linewidths,
        )
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(caption, color="black", fontsize=9)
    fig.tight_layout()
    return solara.FigureMatplotlib(fig, dependencies=[revision, followed])


def _followed_agent(model, followed: int):
    agents = list(model.agents)
    if not agents:
        return None
    index = min(max(followed, 1), len(agents)) - 1
    return agents[index]


def feature_strip(model, followed: int, revision: int):
    agent = _followed_agent(model, followed)
    fig = Figure(figsize=(10, 2.4))
    _blank(fig)
    ax = fig.subplots()
    ax.set_facecolor("white")
    ax.axis("off")
    if agent is None:
        return solara.FigureMatplotlib(fig, dependencies=[revision, followed])
    last = agent.trace[-1] if agent.trace else None
    added = set(last["added"]) if last else set()
    removed = set(last["removed"]) if last else set()
    if agent.status == "accepted" and agent.product:
        current = set(agent.product)
    else:
        current = set(agent.proposal)
    names = sorted(agent.concrete)
    columns = 8
    for index, name in enumerate(names):
        if name in added:
            color = "#1565c0"
        elif name in removed:
            color = "#c62828"
        elif name in current:
            color = "#2e7d32"
        else:
            color = "#eceff1"
        text = "white" if color != "#eceff1" else "#455a64"
        x = index % columns
        y = -(index // columns)
        ax.add_patch(
            FancyBboxPatch(
                (x, y - 0.35),
                0.92,
                0.7,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor=color,
                edgecolor="none",
            )
        )
        ax.text(x + 0.46, y, name, ha="center", va="center", fontsize=7, color=text)
    rows = max((len(names) + columns - 1) // columns, 1)
    ax.set_xlim(-0.15, columns)
    ax.set_ylim(-rows + 0.45, 0.55)
    ax.set_title(
        "Azul: la agregó en este tick.  Rojo: la sacó.  Verde: está en el pedido.  "
        "Gris: no la pidió.",
        color="black",
        fontsize=9,
    )
    fig.tight_layout()
    return solara.FigureMatplotlib(fig, dependencies=[revision, followed])


def search_log(model, followed: int) -> str:
    agent = _followed_agent(model, followed)
    if agent is None:
        return "No hay agentes."
    lines = [
        f"### Agente {agent.unique_id} · {agent.status} · intento {agent.attempts}"
    ]
    if not agent.trace:
        asked = ", ".join(agent.initial_order) or "(vacío)"
        lines.append(f"Todavía no pidió. El pedido inicial es: {asked}.")
        return "\n\n".join(lines)
    last = agent.trace[-1]
    if last["ok"]:
        lines.append("El motor aceptó el último pedido.")
    else:
        lines.append(f"El motor rechazó el último pedido: {last['error']}")
    if last["added"]:
        lines.append("Agregó: " + ", ".join(last["added"]) + ".")
    if last["removed"]:
        lines.append("Sacó: " + ", ".join(last["removed"]) + ".")
    if agent.product:
        lines.append("Producto: " + ", ".join(agent.product) + ".")
    lines.append("#### Reintentos")
    for step in agent.trace:
        sent = ", ".join(step["sent"]) or "(vacío)"
        if step["ok"]:
            outcome = "aceptado"
        else:
            outcome = f"falló ({step['error']})"
        change = []
        if step["added"]:
            change.append("agregó " + ", ".join(step["added"]))
        if step["removed"]:
            change.append("sacó " + ", ".join(step["removed"]))
        extra = ". " + "; ".join(change) if change else ""
        lines.append(
            f"{step['attempt']}. Mandó {sent}. {outcome}. Quedó {step['status']}{extra}."
        )
    return "\n\n".join(lines)


def history_frame(model):
    columns = {
        name: list(values)
        for name, values in model.datacollector.model_vars.items()
    }
    if not columns:
        return None
    length = min(len(values) for values in columns.values())
    if length == 0:
        return None
    return pd.DataFrame({name: values[:length] for name, values in columns.items()})


def trend_plot(measures):
    def draw(model, revision: int):
        frame = history_frame(model)
        fig = Figure(figsize=(8, 3.2))
        _blank(fig)
        ax = fig.subplots()
        ax.set_facecolor("white")
        if frame is not None:
            for measure in measures:
                ax.plot(frame[measure], label=measure, marker="o")
            ax.legend(loc="best", fontsize=8)
            ax.set_xlim(-0.2, max(len(frame) - 1, 1) + 0.2)
        ax.set_xlabel("Tick")
        fig.tight_layout()
        return solara.FigureMatplotlib(fig, dependencies=[revision])

    return draw


def status_line(model) -> str:
    pending = sum(agent.status == "pending" for agent in model.agents)
    same = sum(
        agent.status == "accepted" and agent.reworks == 0 for agent in model.agents
    )
    completed = sum(
        agent.status == "accepted" and agent.reworks > 0 for agent in model.agents
    )
    return (
        f"### Tick {model.steps} · pendientes {pending} · "
        f"iguales {same} · completados por el motor {completed}"
    )


@solara.component
def page():
    preference = solara.use_reactive("azar")
    n_clients = solara.use_reactive(80)
    opening_seed = solara.use_memo(new_seed, [])
    seed = solara.use_reactive(opening_seed)
    playing = solara.use_reactive(False)
    tick = solara.use_reactive(0)
    followed = solara.use_reactive(1)
    initial = solara.use_memo(
        lambda: StoreFamily(store_engine, "azar", n_clients=80, seed=opening_seed),
        [],
    )
    model = solara.use_reactive(initial)

    def loop(cancel: threading.Event):
        if not playing.value:
            return
        while not cancel.is_set():
            if cancel.wait(0.8):
                return
            current = model.value
            if not current.running:
                playing.value = False
                return
            current.step()
            tick.value = current.steps
            if not current.running:
                playing.value = False
                return

    solara.use_thread(loop, dependencies=[playing.value])

    def do_step():
        current = model.value
        if not current.running:
            return
        current.step()
        tick.value = current.steps

    def do_reset():
        playing.value = False
        seed.value = new_seed()
        model.value = StoreFamily(
            store_engine,
            preference.value,
            n_clients=n_clients.value,
            seed=seed.value,
        )
        followed.value = 1
        tick.value = 0

    def do_play_pause():
        if not model.value.running:
            return
        playing.value = not playing.value

    with solara.Column(style={"padding": "16px", "max-width": "1100px"}):
        solara.Markdown("## Familia VirtualStore")
        with solara.Row():
            solara.Button("Reset", on_click=do_reset, color="primary")
            solara.Button(
                "Pausa" if playing.value else "Play",
                on_click=do_play_pause,
                disabled=not model.value.running,
            )
            solara.Button(
                "Step",
                on_click=do_step,
                disabled=playing.value or not model.value.running,
            )
        solara.Select(
            "Gustos",
            values=["parecidos", "distintos", "largo", "azar"],
            value=preference,
        )
        solara.SliderInt("Clientes", value=n_clients, min=1, max=120, step=1)
        solara.SliderInt("Semilla", value=seed, min=1, max=9999, step=1)
        agent_count = max(len(list(model.value.agents)), 1)
        solara.SliderInt("Agente", value=followed, min=1, max=agent_count, step=1)
        solara.Markdown(
            "Reset sortea una semilla nueva. "
            "Agente elige a quién seguir. Con 1 cliente se ve solo su búsqueda; "
            "con varios, todos avanzan juntos y el borde negro marca al elegido. "
            "Gustos largo repite siempre el mismo pedido de muchos intentos. "
            "Gustos azar sortea el pedido y en cada fallo elige al azar una corrección. "
            "Puede abandonar a los 30 intentos."
        )
        solara.Markdown(status_line(model.value))
        solara.Markdown(search_log(model.value, followed.value))
        feature_strip(model.value, followed.value, tick.value)
        client_board(model.value, tick.value, followed.value)
        trend_plot(
            ["accepted_as_asked", "completed_by_engine", "pending", "abandoned"]
        )(model.value, tick.value)
        trend_plot(STORE_FEATURES)(model.value, tick.value)
