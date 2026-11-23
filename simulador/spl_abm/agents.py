"""Clientes que piden un producto de la familia VirtualStore."""

from mesa import Agent

STORE_CONCRETE = {
    "clothing",
    "electronics",
    "home",
    "sports",
    "books",
    "grocery",
    "search",
    "filters",
    "sortByPrice",
    "sortByRating",
    "wishlist",
    "compare",
    "cart",
    "cash",
    "card",
    "transfer",
    "wallet",
    "pickup",
    "homeDelivery",
    "express",
    "locker",
    "guest",
    "login",
    "reviews",
    "loyalty",
    "coupons",
    "recommendations",
    "stockAlert",
    "invoice",
    "chat",
    "newsletter",
    "web",
    "mobile",
}
STORE_PAYMENT = {"cash", "card", "transfer", "wallet"}
STORE_CHANNEL = {"web", "mobile"}
STORE_SHIPPING = {"pickup", "homeDelivery", "express", "locker"}
STORE_DEPARTMENT = {"clothing", "electronics", "home", "sports", "books", "grocery"}


class StoreClient(Agent):
    """Creencia: features que cree necesitar. Deseo: pedido aceptado.
    Intención: enviar el pedido y, si falla, corregir una sola cosa.
    El motor agrega el carrito si falta. Pago, envío y cuenta los corrige el cliente.
    """

    def __init__(
        self,
        model,
        desired: list[str],
        patience: int = 30,
        random_search: bool = False,
    ):
        super().__init__(model)
        self.concrete = STORE_CONCRETE
        self.desired = set(desired)
        self.must_have = set(desired)
        self.beliefs = set(desired)
        self.proposal = set(self.beliefs)
        self.initial_order = tuple(sorted(self.proposal))
        self.patience = patience
        self.attempts = 0
        self.reworks = 0
        self.status = "pending"
        self.product: tuple[str, ...] | None = None
        self.last_error: str | None = None
        self.trace: list[dict] = []
        self.random_search = random_search

    def propose(self) -> list[str]:
        return sorted(self.proposal)

    def receive(self, result: dict) -> None:
        """Un paso del ciclo BDI. La creencia es el pedido que acaba de enviar.
        Si el motor lo acepta, el deseo se cumple o incorpora lo que faltaba.
        Si lo rechaza, la intención del tick siguiente es corregir una sola feature.
        """
        if self.status != "pending":
            return
        sent = self.propose()
        before = set(sent)
        self.attempts += 1
        if result["ok"]:
            self._accept_or_repair(set(result["features"]))
        else:
            self.last_error = result["error"]
            self._repair_or_abandon()
        after = set(self.proposal)
        self.trace.append(
            {
                "attempt": self.attempts,
                "sent": sent,
                "ok": bool(result["ok"]),
                "added": sorted(after - before),
                "removed": sorted(before - after),
                "error": None if result["ok"] else result.get("error"),
                "status": self.status,
                "product": list(self.product) if self.product else None,
            }
        )

    def _accept_or_repair(self, completed: set[str]) -> None:
        added = (completed & self.concrete) - self.proposal - {"cart"}
        if added and self.attempts < self.patience:
            self.reworks += 1
            self.beliefs |= added
            self.proposal |= added
            return
        if added:
            self.reworks += 1
            self.proposal |= added
        self.status = "accepted"
        self.product = tuple(sorted(completed & self.concrete))

    def _repair_or_abandon(self) -> None:
        if self.attempts >= self.patience:
            self.status = "abandoned"
            return
        if self.random_search:
            self._try_random()
            return
        if self._repair(self.last_error or ""):
            self.reworks += 1
            return
        optional = self.proposal - self.must_have
        if not optional:
            self.status = "abandoned"
            return
        self.proposal.remove(sorted(optional)[0])
        self.reworks += 1

    def _try_random(self) -> None:
        moves = self._random_moves(self.last_error or "")
        menu = STORE_CONCRETE - {"cart"}
        absent = sorted(menu - self.proposal)
        present = sorted(self.proposal & menu)
        if absent:
            moves.append(("add", self.model.random.choice(absent)))
        if present:
            moves.append(("remove", self.model.random.choice(present)))
        if not moves:
            self.status = "abandoned"
            return
        kind, name = self.model.random.choice(moves)
        if kind == "add":
            self.proposal.add(name)
        else:
            self.proposal.discard(name)
        self.reworks += 1

    def _random_moves(self, error: str) -> list[tuple[str, str]]:
        moves: list[tuple[str, str]] = []

        def missing(names: tuple[str, ...]) -> None:
            moves.extend(("add", name) for name in names if name not in self.proposal)

        def group_moves(group: set[str]) -> None:
            chosen = sorted(self.proposal & group)
            if len(chosen) > 1:
                moves.extend(("remove", name) for name in chosen)
            elif not chosen:
                missing(tuple(sorted(group)))

        if "feature channel" in error:
            group_moves(STORE_CHANNEL)
        if "feature payments" in error:
            group_moves(STORE_PAYMENT)
        if "feature shipping" in error:
            group_moves(STORE_SHIPPING)
        if "feature departments" in error and not (self.proposal & STORE_DEPARTMENT):
            missing(tuple(sorted(STORE_DEPARTMENT)))
        if "card =>" in error or "transfer =>" in error or "locker =>" in error:
            missing(("invoice", "login", "card"))
        if "wallet =>" in error:
            missing(("loyalty", "login"))
        if "express =>" in error:
            missing(("stockAlert", "login"))
        if "recommendations =>" in error or "reviews =>" in error:
            missing(("login", "reviews"))
            if "guest" in self.proposal:
                moves.append(("remove", "guest"))
        if "chat =>" in error or "newsletter =>" in error or "invoice =>" in error:
            missing(("login", "web"))
            if "mobile" in self.proposal:
                moves.append(("remove", "mobile"))
        if "coupons =>" in error and "guest" in self.proposal:
            moves.append(("remove", "guest"))
        if "grocery =>" in error and "coupons" in self.proposal:
            moves.append(("remove", "coupons"))
        return moves

    def _repair(self, error: str) -> bool:
        """Corrección dirigida por la regla que rompió el pedido.
        En un grupo (canal, pago, envío o rubro) deja un solo miembro.
        Ante un implies, agrega la feature que la regla exige o saca la que la contradice.
        """
        if "feature channel" in error:
            return self._fix_group(STORE_CHANNEL, "web")
        if "feature payments" in error:
            return self._fix_group(STORE_PAYMENT, "cash")
        if "feature shipping" in error:
            return self._fix_group(STORE_SHIPPING, "pickup")
        if "feature departments" in error and not (self.proposal & STORE_DEPARTMENT):
            self.proposal.add("clothing")
            return True
        if "card =>" in error or "transfer =>" in error:
            self.proposal.update(("invoice", "login"))
            return True
        if "wallet =>" in error:
            self.proposal.update(("loyalty", "login"))
            return True
        if "express =>" in error:
            self.proposal.update(("stockAlert", "login"))
            return True
        if "locker =>" in error:
            self._use_only(STORE_PAYMENT, "card")
            self.proposal.add("invoice")
            return True
        if "recommendations =>" in error or "reviews =>" in error:
            self.proposal.discard("guest")
            self.proposal.update(("login", "reviews"))
            return True
        if "chat =>" in error or "newsletter =>" in error or "invoice =>" in error:
            self._use_only(STORE_CHANNEL, "web")
            self.proposal.add("login")
            return True
        if "coupons =>" in error:
            self.proposal.discard("guest")
            return "guest" not in self.proposal
        if "grocery =>" in error:
            self.proposal.discard("coupons")
            return "coupons" not in self.proposal
        return False

    def _use_only(self, group: set[str], name: str) -> None:
        for other in group:
            if other != name:
                self.proposal.discard(other)
        self.proposal.add(name)

    def _fix_group(self, group: set[str], default: str) -> bool:
        chosen = self.proposal & group
        if len(chosen) > 1:
            self.proposal.remove(sorted(chosen)[0])
            return True
        if not chosen:
            self.proposal.add(default)
            return True
        return False
