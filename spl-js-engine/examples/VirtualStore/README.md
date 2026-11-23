# VirtualStore

Tienda virtual de ejemplo para `spl-js-engine`. Tiene 33 características concretas y reglas que rechazan un pedido incompleto. El código generado solo escribe logs.

Desde esta carpeta:

```bash
node ../../src/cli.js --featureModel model.json --product product.json --config config.json --extra extra.js --code code --output output --verbose
node output/store.js
```

`product.json` es una tienda válida: ropa, libros, electrónica, búsqueda, pago en efectivo, envío a domicilio, login y canal web.

## Qué es obligatorio en cualquier pedido

- Al menos un departamento: `clothing`, `electronics`, `home`, `sports`, `books`, `grocery`.
- Exactamente un pago: `cash`, `card`, `transfer` o `wallet`.
- Exactamente un canal: `web` o `mobile`.
- El carrito entra solo, porque es obligatorio.

El envío es opcional. Si se elige, tiene que ser uno solo: `pickup`, `homeDelivery`, `express` o `locker`.

## Pedidos que fallan

Estas reglas no se completan solas. El motor rechaza el pedido. Sirven para que un agente reciba el error, agregue lo que falta o suelte lo que choca, y vuelva a intentar.

| Pedido | Qué manda | Por qué falla | Cómo se repara |
| --- | --- | --- | --- |
| `product-fail-card.json` | `card` | tarjeta exige `invoice` y `login` | agregar las dos |
| `product-fail-express.json` | `express` | express exige `stockAlert` y `login` | agregar las dos |
| `product-fail-two-payments.json` | `cash` y `card` | el pago es uno u otro | soltar uno |
| `product-fail-channels.json` | `web` y `mobile` | el canal es uno u otro | soltar uno |
| `product-fail-coupons-guest.json` | `coupons` y `guest` | los cupones no van con invitado | soltar `guest` o `coupons` |

Otras reglas del mismo tipo, en `model.json`:

- `transfer` exige `login` e `invoice`.
- `wallet` exige `loyalty` y `login`.
- `locker` exige `card` e `invoice`.
- `recommendations` exige `login` y `reviews`.
- `chat` y `newsletter` exigen `login` y `web`.
- `invoice` exige `login` y `web`.
- `reviews` exige `login` y no puede ir con `guest`.
- `grocery` no puede ir con `coupons`.

Para probar un fallo, cambiá `--product` por el archivo correspondiente. El comando termina con error y no deja una tienda en `output`.
