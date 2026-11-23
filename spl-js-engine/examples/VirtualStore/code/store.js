function openStore() {
  console.log("tienda: /*%= data.title %*/ (/*%= data.currency %*/)");

  /*% if (feature.clothing) { %*/
  console.log("departamento: ropa");
  /*% } if (feature.electronics) { %*/
  console.log("departamento: electronica");
  /*% } if (feature.home) { %*/
  console.log("departamento: hogar");
  /*% } if (feature.sports) { %*/
  console.log("departamento: deportes");
  /*% } if (feature.books) { %*/
  console.log("departamento: libros");
  /*% } if (feature.grocery) { %*/
  console.log("departamento: almacen");
  /*% } %*/

  /*% if (feature.search) { %*/
  console.log("listado: busqueda");
  /*% } if (feature.filters) { %*/
  console.log("listado: filtros");
  /*% } if (feature.sortByPrice) { %*/
  console.log("listado: orden por precio");
  /*% } if (feature.sortByRating) { %*/
  console.log("listado: orden por valoracion");
  /*% } if (feature.wishlist) { %*/
  console.log("listado: favoritos");
  /*% } if (feature.compare) { %*/
  console.log("listado: comparar");
  /*% } %*/

  /*% if (feature.cart) { %*/
  console.log("checkout: carrito");
  /*% } %*/

  /*% if (feature.cash) { %*/
  console.log("pago: efectivo");
  /*% } if (feature.card) { %*/
  console.log("pago: tarjeta");
  /*% } if (feature.transfer) { %*/
  console.log("pago: transferencia");
  /*% } if (feature.wallet) { %*/
  console.log("pago: billetera");
  /*% } %*/

  /*% if (feature.pickup) { %*/
  console.log("envio: retiro en local");
  /*% } if (feature.homeDelivery) { %*/
  console.log("envio: a domicilio");
  /*% } if (feature.express) { %*/
  console.log("envio: express");
  /*% } if (feature.locker) { %*/
  console.log("envio: locker");
  /*% } %*/

  /*% if (feature.guest) { %*/
  console.log("cuenta: invitado");
  /*% } if (feature.login) { %*/
  console.log("cuenta: login");
  /*% } if (feature.reviews) { %*/
  console.log("cuenta: resenas");
  /*% } if (feature.loyalty) { %*/
  console.log("cuenta: fidelizacion");
  /*% } %*/

  /*% if (feature.coupons) { %*/
  console.log("servicio: cupones");
  /*% } if (feature.recommendations) { %*/
  console.log("servicio: recomendaciones");
  /*% } if (feature.stockAlert) { %*/
  console.log("servicio: aviso de stock");
  /*% } if (feature.invoice) { %*/
  console.log("servicio: factura");
  /*% } if (feature.chat) { %*/
  console.log("servicio: chat");
  /*% } if (feature.newsletter) { %*/
  console.log("servicio: newsletter");
  /*% } %*/

  /*% if (feature.web) { %*/
  console.log("canal: web");
  /*% } if (feature.mobile) { %*/
  console.log("canal: mobile");
  /*% } %*/
}

openStore();
