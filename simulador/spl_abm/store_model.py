"""Familia VirtualStore: cada pedido es un subconjunto del menú de 32 features.

`cart` no se pide: el motor lo agrega. `parecidos` sortea un pedido bien armado
(165.150.720): al menos un rubro, un pago, un canal y las reglas implies pueden fallar.
`distintos` sortea cualquier subconjunto de las 32 (2^32). Cada tick corrige un solo
problema, así que la corrida cambia hasta que no queda nadie pendiente.
"""

from mesa import Model
from mesa.datacollection import DataCollector

from spl_abm.agents import STORE_CONCRETE, StoreClient
from spl_abm.engine import SplEngine

DEPARTMENTS = ("clothing", "electronics", "home", "sports", "books", "grocery")
PAYMENTS = ("cash", "card", "transfer", "wallet")
CHANNELS = ("web", "mobile")
SHIPPING = ("pickup", "homeDelivery", "express", "locker")
LISTING = ("search", "filters", "sortByPrice", "sortByRating", "wishlist", "compare")
ACCOUNT = ("guest", "login", "reviews", "loyalty")
SERVICES = ("coupons", "recommendations", "stockAlert", "invoice", "chat", "newsletter")
STORE_MENU = tuple(sorted(STORE_CONCRETE - {"cart"}))
# El pedido que más tarda con las reglas actuales: 11 rechazos y acepta al intento 12.
LONG_ORDER = (
    "card",
    "cash",
    "coupons",
    "express",
    "grocery",
    "guest",
    "homeDelivery",
    "locker",
    "mobile",
    "pickup",
    "transfer",
    "wallet",
    "web",
)


def _count(model, status: str) -> int:
    return sum(agent.status == status for agent in model.agents)


def _accepted_as_asked(model) -> int:
    return sum(
        agent.status == "accepted" and agent.reworks == 0 for agent in model.agents
    )


def _completed_by_engine(model) -> int:
    return sum(
        agent.status == "accepted" and agent.reworks > 0 for agent in model.agents
    )


def _unique_products(model) -> int:
    return len({agent.product for agent in model.agents if agent.product})


def _feature_count(name: str):
    def reporter(model) -> int:
        return sum(bool(agent.product) and name in agent.product for agent in model.agents)

    return reporter


class StoreFamily(Model):
    def __init__(self, engine: SplEngine, preference: str, n_clients: int = 80, seed: int = 1):
        super().__init__(rng=seed)
        self.engine = engine
        self.preference = preference
        self.structural_errors = 0
        self.implies_errors = 0
        for _ in range(n_clients):
            StoreClient(
                self,
                self._sample_client(),
                random_search=self.preference == "azar",
            )
        reporters = {
            "pending": lambda model: _count(model, "pending"),
            "accepted_as_asked": _accepted_as_asked,
            "completed_by_engine": _completed_by_engine,
            "abandoned": lambda model: _count(model, "abandoned"),
            "unique_products": _unique_products,
            "structural_errors": lambda model: model.structural_errors,
            "implies_errors": lambda model: model.implies_errors,
        }
        for name in sorted(STORE_CONCRETE):
            reporters[f"feature_{name}"] = _feature_count(name)
        self.datacollector = DataCollector(model_reporters=reporters)

    def _sample_client(self) -> list[str]:
        if self.preference == "parecidos":
            return self._sample_well_formed()
        if self.preference == "largo":
            return list(LONG_ORDER)
        return [name for name in STORE_MENU if self.random.random() < 0.5]

    def _sample_well_formed(self) -> list[str]:
        order = {name for name in DEPARTMENTS if self.random.random() < 0.5}
        if not order:
            order.add(self.random.choice(DEPARTMENTS))
        order.add(self.random.choice(PAYMENTS))
        order.add(self.random.choice(CHANNELS))
        shipping = self.random.choice((None, *SHIPPING))
        if shipping is not None:
            order.add(shipping)
        for group in (LISTING, ACCOUNT, SERVICES):
            order.update(name for name in group if self.random.random() < 0.5)
        return sorted(order)

    def step(self) -> None:
        """Un tick de Mesa. Junta a quienes siguen pendientes, manda el lote
        al motor y anota cada rechazo como error estructural o de restricción.
        """
        pending = [agent for agent in self.agents if agent.status == "pending"]
        self.structural_errors = 0
        self.implies_errors = 0
        if pending:
            results = self.engine.complete_many([agent.propose() for agent in pending])
            for agent, result in zip(pending, results):
                if not result["ok"]:
                    if "Constraints" in result["error"]:
                        self.implies_errors += 1
                    else:
                        self.structural_errors += 1
                agent.receive(result)
        self.datacollector.collect(self)
        if not any(agent.status == "pending" for agent in self.agents):
            self.running = False
