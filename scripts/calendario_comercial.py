#!/usr/bin/env python3
"""
Calendario comercial HORECA: que compra el hostelero en cada momento del año.

Esta es la fuente de ideas del planificador. NO sale del historico — sale del ciclo
de compra del cliente, que es lo que un comercial tiene en la cabeza.

Cada ocasion lleva:
  tema     - el asunto tal como iria en la newsletter (tono de usted)
  meses    - meses en los que TOCA ENVIAR, ya descontada la antelacion de compra
  razon    - el argumento comercial: por que vende ahora
  cliente  - a quien le vende
  claves   - palabras para localizar la URL de categoria en el historico de enlaces
  propia   - True si es papel/carton de fabricacion propia (prioridad alta)

La antelacion de compra es la clave del calendario: el hostelero compra la Navidad en
octubre y la terraza en marzo. Enviar en diciembre la mantelería de Navidad es tarde.

AMBITO INTERNACIONAL. Las newsletters salen en cuatro idiomas y llegan a unos 60 paises,
con Francia, Portugal, Italia y Alemania como mercados de exportacion consolidados. Las
ocasiones tienen que funcionar en todos: nada de Feria de Abril, San Juan, torrijas,
panellets ni romerias. Se usan los motores universales del ciclo HORECA (temporada de
terraza, de helado, de sopa, campana de Navidad, vuelta al trabajo) y solo las fechas
que se celebran en todo el continente (Navidad, Fin de Ano, San Valentin, Carnaval,
Pascua, Halloween, Black Friday). Cuando una fecha varia de un pais a otro se nombra
sin atarla al calendario espanol.
"""

# (tema, meses_de_envio, razon_comercial, cliente, claves_url, fabricacion_propia)
OCASIONES = [

# ─────────────── ENERO ───────────────
("Sopas y cremas para llevar: tarrinas con tapa y envases microondables", [1, 2],
 "Enero es el mes de la comida caliente de mediodía y del menú de oficina. La sopa para "
 "llevar exige tarrina estanca con tapa, y el cliente la repone justo ahora.",
 "Menú diario, take away, comida de oficina", ["tarrinas-para-sopas", "tarrinas"], True),

("Dulces de Epifanía: la caja del roscón, la galette y el bolo-rei", [12],
 "El dulce de Reyes se vende del 28 de diciembre al 6 de enero en media Europa, con otro "
 "nombre en cada país. La caja se compra en la primera quincena de diciembre, no en enero.",
 "Pastelería, panadería, obrador", ["cajas-para-pasteleria", "pasteleria"], True),

("Bebidas calientes para llevar: vasos de doble pared, tapas y paletinas", [1, 10, 11],
 "Con el frío se dispara el café para llevar. Es consumo diario y reposición constante: "
 "el cliente que compra vasos en enero vuelve a comprar en marzo.",
 "Cafetería, panadería, gasolinera, take away", ["vasos-de-carton-bebidas-calientes"], False),

("Empiece el año con la mesa nueva: servilletas y mantelería de diario", [1],
 "Después de Navidad el almacén está vacío y el hostelero rehace el stock básico. Es la "
 "compra de reposición más grande del año en papelería de mesa.",
 "Restaurante de menú, bar, cafetería", ["servilletas-de-papel", "manteles-de-papel"], True),

("La carta ligera de enero: envases y boles para ensaladas y poke", [1],
 "En enero la demanda se vuelve saludable y el take away de ensalada sube. Envase con "
 "cierre y tapa transparente, que la ensalada se vende con la vista.",
 "Take away, delivery, poke y healthy food", ["ensaladeras", "take-away"], False),

("Bolsas de papel para la campaña de rebajas: kraft, con asa y personalizables", [12, 6],
 "Las rebajas de invierno y de verano mueven volumen de bolsa en todos los mercados, "
 "aunque cada país tenga sus fechas. Es cuando el comercio se plantea personalizarla.",
 "Comercio, panadería, pastelería, take away", ["bolsas-kraft", "bolsas-de-papel"], True),

("Mantelines individuales: cambie la imagen del menú del día", [1, 9],
 "El mantelín es el soporte más barato para renovar la mesa, y el arranque de año es "
 "cuando el hostelero se replantea la carta y la imagen.",
 "Restaurante de menú, cafetería", ["manteles-individuales", "mantelines"], True),

("Servilletas Canguro: agilidad en mesa cuando la plantilla es corta", [1, 8],
 "En enero y en agosto se trabaja con menos personal. La servilleta con el cubierto "
 "dentro ahorra un gesto por comensal, y eso se nota en el servicio.",
 "Restaurante, cafetería, colectividades", ["servilletas-kangaroo"], True),

("Papel antigrasa: proteger, presentar y no traspasar", [1, 7],
 "Producto de consumo continuo y de fabricación propia. Quien lo prueba lo repone todo "
 "el año, y en enero entra en la compra de reposición.",
 "Fast food, bar de tapas, take away", ["papel-antigrasa"], True),

("Temporada de montaña: bebidas calientes y comida de pista", [12, 1],
 "De diciembre a marzo las estaciones de esquí de los Alpes y los Pirineos trabajan a "
 "tope y todo se sirve para llevar, con guantes puestos. Vaso resistente, tapa segura y "
 "envase que aguante el frío.",
 "Estación de esquí, refugio, hotel de montaña", ["vasos-de-carton-bebidas-calientes"], False),

("Delivery de invierno: cuando el consumo se va a casa", [1, 11],
 "En los meses fríos el pedido a domicilio sube en todos los mercados. El envase tiene "
 "que llegar caliente, cerrado y presentable: es donde se juega la repetición del cliente.",
 "Delivery, dark kitchen, restaurante", ["take-away", "recipientes-take-away-microondables"], False),

# ─────────────── FEBRERO ───────────────
("San Valentín: la mesa que se recuerda. Tête-à-Tête, Like-Linen y mantelería decorada", [1],
 "San Valentín se prepara en la última semana de enero. Es la primera ocasión del año "
 "para vender mantelería de gama alta, y el hostelero sube el ticket ese día.",
 "Restaurante de mantel, hotel", ["tete-a-tete", "like-linen"], True),

("Cajas de bombones y pastelería fina para San Valentín", [1],
 "Pastelería y bombonería trabajan San Valentín con caja pequeña y de presentación. "
 "Compra corta pero de margen alto.",
 "Pastelería, bombonería, chocolatería", ["cajas-para-pasteleria", "pasteleria"], True),

("Carnaval: masas fritas y dulces de temporada. Cucuruchos y papelinas de punta", [2],
 "Carnaval se celebra en toda Europa y en todas partes se traduce en fritura dulce para "
 "comer de pie. El cucurucho y la papelina se agotan, y son de fabricación propia.",
 "Obrador, feria, food truck, panadería", ["cucuruchos-de-papel", "papelinas"], True),

("Bolsas y papel de regalo para San Valentín", [1],
 "Comercio y pastelería necesitan envolver bonito una semana concreta. Bolsa pequeña, "
 "papel y lazo: pedido rápido y repetible cada año.",
 "Comercio, pastelería, floristería", ["papel-y-bolsas-para-regalos"], True),

("Mantelería Airlaid: efecto tela sin lavandería", [2, 4],
 "El argumento es el coste: el Airlaid da la sensación de mantel de tela sin el gasto "
 "de lavandería ni el riesgo de manchas. Cambia la conversación de precio a coste total.",
 "Restaurante de mantel, hotel, catering", ["airlaid", "manteles-de-papel"], True),

("Servilletas personalizadas: su logo en cada mesa, también en tirada corta", [2, 9],
 "La personalización es lo que ningún competidor de precio puede igualar, y se puede "
 "hacer en tirada corta. Febrero y septiembre son los meses en que hay tiempo de producir.",
 "Restaurante, cadena, hotel, franquicia", ["personalizados"], True),

("Menú de pescado: envolver y presentar producto graso y húmedo", [2, 3],
 "Las semanas previas a Pascua desplazan la carta hacia el pescado en buena parte de "
 "Europa. Papel antigrasa, bandeja y bolsa específicos para producto que traspasa.",
 "Pescadería, restaurante, take away", ["papel-antigrasa", "bandejas"], True),

("Envases para el menú de oficina: microondables y estancos", [2, 9],
 "El menú de mediodía para llevar es negocio recurrente los doce meses, y se refuerza "
 "cuando pasa el frío y la gente vuelve a la calle.",
 "Restaurante de menú, take away, delivery", ["recipientes-take-away-microondables"], False),

("Bolsas para panadería y bollería: el desayuno fuera de casa", [2, 6],
 "Consumo diario, reposición constante y fabricación propia. La bolsa de croissant se "
 "compra en cajas grandes y se repite todo el año.",
 "Panadería, cafetería, hotel", ["bolsas-para-pan", "bolsas-para-croissant"], True),

("Guisos y platos de cuchara para llevar", [2],
 "Febrero es el mes de más consumo de guiso y legumbre. El take away de plato de cuchara "
 "necesita envase hondo, estanco y que se pueda calentar.",
 "Restaurante de menú, take away, charcutería", ["tarrinas-para-sopas", "recipientes-take-away-microondables"], True),

("Temporada hotelera: el desayuno que recuerda el cliente", [3, 5],
 "El hotel prepara la temporada en primavera. El desayuno es donde el huésped juzga la "
 "casa, y la bolsa de bollería y la servilleta salen en cada servicio.",
 "Hotel, apartamento turístico, hostal", ["bolsas-para-croissant", "servilletas-de-papel"], True),

("Servilletas Double Point: la calidad que se nota en la mano", [2, 5],
 "Subir del tisú al Double Point cuesta muy poco por comensal y el cliente lo percibe al "
 "instante. Es la venta de gama más fácil del catálogo, y es fabricación propia.",
 "Restaurante, cafetería, bar", ["servilletas-de-papel"], True),

("Posavasos y presentación de barra para el aperitivo de invierno", [2],
 "El aperitivo de fin de semana no para en invierno. Posavasos personalizable y "
 "presentación en papel: producto pequeño, propio y de reposición continua.",
 "Bar, cervecería, cafetería, hotel", ["posavasos"], True),

("Brunch de fin de semana: la mesa que se fotografía", [2, 9],
 "El brunch se ha instalado en toda Europa y es un servicio de margen alto donde la "
 "presentación lo es todo. Mantelería de gama, servilleta de calidad y papel decorado.",
 "Cafetería, brunch, hotel, panadería", ["like-linen", "manteles-individuales"], True),

# ─────────────── MARZO ───────────────
("Prepare la terraza antes de que llegue el sol: mantelería Spunbond y mantelines", [3],
 "LA COMPRA SE ADELANTA: la terraza se equipa en marzo y se usa en mayo. El Spunbond "
 "aguanta el viento y no se levanta, que es el problema real de la terraza.",
 "Terraza, chiringuito, cafetería", ["manteles-spunbond", "manteles-individuales"], True),

("Las heladerías abren: tarrinas, conos y cucharillas", [3],
 "La heladería abre en marzo y hace la compra de temporada de golpe. Quien no está en "
 "marzo no entra hasta septiembre.",
 "Heladería, pastelería, chiringuito", ["tarrinas-para-helados"], True),

("Dulces de Pascua: cajas, blondas y bandejas para producto delicado", [3],
 "Temporada corta y de mucho volumen en pastelería, sea cual sea el dulce de cada país. "
 "Necesita bandeja, blonda y caja que aguanten producto húmedo o con almíbar.",
 "Pastelería, panadería, restaurante", ["pasteleria", "blondas"], True),

("Pastelería de regalo: cajas con ventana y bolsas de presentación", [3],
 "Marzo concentra fechas de regalo distintas en cada país. Lo común es la caja pequeña "
 "con ventana y la bolsa de presentación: pedido corto y de margen alto.",
 "Pastelería, comercio, obrador", ["cajas-para-pasteleria", "papel-y-bolsas-para-regalos"], True),

("Pascua: take away en los días de más afluencia del primer semestre", [3],
 "El puente de Pascua mueve turismo en toda Europa y concentra el consumo en la calle. "
 "Todo se vende en envase de un solo uso y se agota en cuatro días.",
 "Bar, take away, food truck, hotel", ["take-away", "bolsas-de-papel"], True),

("Servilletas de color: vista la mesa de primavera", [3],
 "Cambio de temporada: el hostelero renueva la gama de color cuando cambia la carta. "
 "Ocasión natural para subir de calidad, del tisú al Double Point.",
 "Restaurante, cafetería, bar", ["servilletas-de-papel"], True),

("Bolsas abiertas a dos lados: bocadillos para llevar y comer de pie", [3, 6],
 "La bolsa abierta a dos lados es el formato del bocadillo de calle. Ferias, mercados y "
 "eventos al aire libre: consumo de pie que no admite plato.",
 "Bar, panadería, food truck, evento", ["bolsas-de-papel"], True),

("Papel antigrasa decorado: presente el frito como se merece", [3, 5],
 "Mismo producto, presentación distinta: el papel decorado permite cobrar más por el "
 "mismo frito. Argumento de ticket medio, no de coste.",
 "Bar de tapas, fast food, chiringuito", ["papel-antigrasa"], True),

("Tête-à-Tête: el camino de mesa que cambia el ticket medio", [3, 11],
 "Producto de fabricación propia poco conocido por el cliente pequeño. Viste la mesa con "
 "muy poco material y sube la percepción de precio.",
 "Restaurante de mantel, hotel, catering", ["tete-a-tete"], True),

# ─────────────── ABRIL ───────────────
("Ferias y mercados de primavera: fritos para consumo de pie", [4],
 "Con el buen tiempo arrancan las ferias, los mercados y los eventos al aire libre. "
 "Papelina, cucurucho y cajetilla: fabricación propia y consumo de un solo uso.",
 "Caseta, feria, food truck, evento", ["cucuruchos-de-papel", "recipientes-para-fritas"], True),

("Banquetes de primavera: se contratan ahora. Mantelería coordinada", [4],
 "LA COMPRA SE ADELANTA: los banquetes de primavera se cierran con dos meses de "
 "antelación. En abril el restaurante ya sabe cuántos servicios tiene y compra el conjunto.",
 "Restaurante de celebraciones, catering, hotel", ["conjuntos-decorados", "manteles-de-papel"], True),

("Catering de exterior: bandejas traiteur y cajas de transporte", [4, 5],
 "Empieza la temporada de eventos al aire libre. El problema del catering es transportar "
 "sin que se mueva ni se enfríe: bandeja con funda y caja rígida.",
 "Catering, traiteur, colectividades", ["bandejas-traiteur"], True),

("Bebidas frías: vasos, tapas y portavasos para la terraza", [4, 5],
 "La terraza arranca y con ella el refresco, el batido y el granizado para llevar. "
 "Compra de temporada que se repone en junio y julio.",
 "Terraza, chiringuito, heladería", ["vasos-de-carton-bebidas-frias"], False),

("Mantelines para la carta de primavera", [4],
 "Cambio de carta, cambio de mantelín. Es la ocasión de vender diseño de temporada en "
 "lugar de blanco liso.",
 "Restaurante de menú, cafetería, terraza", ["manteles-individuales"], True),

("Fritura de temporada: envolver sin que traspase", [4, 7],
 "El frito es el producto más exigente con el papel. Antigrasa de fabricación propia y "
 "cucurucho: el cliente lo nota en la primera bandeja.",
 "Bar de playa, freiduría, food truck", ["papel-antigrasa", "cucuruchos-de-papel"], True),

("Bolsas y cajas de pastelería para tartas de celebración", [4, 5],
 "Bodas, cumpleaños y banquetes. La tarta sale del obrador en caja y bolsa, y en "
 "temporada de celebraciones se multiplica el consumo.",
 "Pastelería, obrador, panadería", ["cajas-para-pasteleria"], True),

("Airlaid Natural: la mesa de temporada en tono crudo", [4],
 "El tono natural es el que más se vende en primavera y verano. Producto de fabricación "
 "propia y de gama media-alta.",
 "Restaurante, hotel, catering", ["airlaid"], True),

("Envases para ensaladas y platos fríos", [4, 6],
 "Sube la temperatura y la carta se vuelve fría. Envase con tapa transparente y cierre "
 "estanco para llevar y para expositor.",
 "Take away, delivery, supermercado, cafetería", ["ensaladeras"], False),

# ─────────────── MAYO ───────────────
("Temporada de banquetes: la mesa de la celebración", [5],
 "Mayo abre la temporada de celebraciones en toda Europa. Servicio de mantel completo y "
 "volumen concentrado en pocos fines de semana.",
 "Restaurante de celebraciones, catering, hotel", ["conjuntos-decorados", "manteles-de-papel"], True),

("Bodas y catering: presentar, transportar y servir fuera de casa", [5],
 "Arranca la temporada de bodas y no para hasta septiembre. El catering compra bandeja, "
 "caja de transporte y mantelería de golpe para toda la temporada.",
 "Catering, traiteur, finca de eventos", ["bandejas-traiteur", "take-away"], True),

("Terrazas a pleno: mantelería que aguanta viento y sol", [5],
 "En mayo la terraza ya está llena y el problema es que el mantel se levanta y se mancha. "
 "Spunbond y mantelín precortado resuelven las dos cosas.",
 "Terraza, chiringuito, cafetería", ["manteles-spunbond", "manteles-individuales"], True),

("Helados y granizados: tarrinas, vasos y cucharillas", [5, 6],
 "Reposición de temporada de la heladería, ahora en firme. Quien vendió en marzo vuelve "
 "a comprar en mayo con las cifras reales.",
 "Heladería, chiringuito, cafetería", ["tarrinas-para-helados"], True),

("Día de la Madre: pastelería y regalo (mayo en casi toda Europa)", [4],
 "Cae en mayo en la mayoría de mercados, así que se prepara a finales de abril. Caja, "
 "bolsa y papel de presentación para pastelería y comercio.",
 "Pastelería, comercio, floristería", ["cajas-para-pasteleria", "papel-y-bolsas-para-regalos"], True),

("Bolsas de papel para heladería y pastelería de temporada", [5],
 "Con la temporada abierta, la bolsa pasa a ser consumo diario. Kraft, con asa y "
 "personalizable en tirada corta.",
 "Heladería, pastelería, panadería", ["bolsas-kraft"], True),

("Servilletas Canguro: servicio rápido con la terraza llena", [5],
 "Con lleno total, cada gesto ahorrado cuenta. La servilleta con cubierto dentro es el "
 "producto que más agiliza la mesa.",
 "Terraza, restaurante, cafetería", ["servilletas-kangaroo"], True),

("Papelinas y cucuruchos para ferias y mercados", [5, 6],
 "Mayo y junio concentran ferias, mercados y eventos al aire libre. Consumo de pie, "
 "producto frito y envase de fabricación propia.",
 "Caseta, feria, food truck", ["cucuruchos-de-papel"], True),

("Envases para picnic y comida al aire libre", [5],
 "La comida se va al exterior: parques, playa, excursión. Envase ligero, cerrado y que "
 "aguante el traslado.",
 "Take away, supermercado, catering", ["take-away"], False),

# ─────────────── JUNIO ───────────────
("Fiestas de verano y eventos de calle: volumen alto en pocas horas", [6],
 "Junio abre la temporada de fiestas al aire libre en toda Europa. Consumo de pie, "
 "servicio rápido y todo de un solo uso.",
 "Bar, chiringuito, caseta, food truck", ["recipientes-para-fritas", "cucuruchos-de-papel"], True),

("Fin de curso y celebraciones: mantelería y servilletas", [6],
 "Junio cierra el curso: comidas de grupo, cenas de despedida y celebraciones escolares. "
 "Servicio de mantel para grupos grandes.",
 "Restaurante, colectividades, catering", ["manteles-de-papel", "servilletas-de-papel"], True),

("Festivales de verano: envases y vasos que aguantan", [6],
 "El festival exige envase que no se rompa de pie y sin mesa. Volumen enorme concentrado "
 "en tres días y pedido cerrado con semanas de antelación.",
 "Festival, food truck, catering de evento", ["take-away", "vasos-de-carton-bebidas-frias"], False),

("Heladería en temporada alta: reposición de tarrinas y conos", [6, 7],
 "Segunda compra de la temporada, la de volumen. El cliente ya sabe qué formato le "
 "funciona y pide en cantidad.",
 "Heladería, chiringuito", ["tarrinas-para-helados"], True),

("Chiringuitos: el take away de playa", [6],
 "El chiringuito vende para llevar todo el día. Bolsa, envase y papel que aguanten "
 "humedad, arena y calor.",
 "Chiringuito, bar de playa, food truck", ["bolsas-de-papel", "take-away"], True),

("Just in Time: servilletas dispensadas para alto volumen", [6, 7],
 "Con la temporada alta la servilleta se gasta el doble y se desperdicia el triple. El "
 "dispensador reduce consumo por comensal: argumento de coste medible.",
 "Fast food, autoservicio, colectividades", ["servilletas-de-papel"], True),

("Mantelería reciclada: el argumento sostenible en plena temporada", [6],
 "El turista europeo pregunta por el material. La línea reciclada permite responder sin "
 "subir el coste, y es de fabricación propia.",
 "Restaurante turístico, hotel, cafetería", ["manteles-de-papel"], True),

("Bolsas para pan y bollería en volumen de verano", [6],
 "El desayuno de verano se hace fuera y en terraza. La panadería multiplica el consumo "
 "de bolsa pequeña.",
 "Panadería, hotel, cafetería", ["bolsas-para-pan"], True),

("Bocadillos, wraps y comida de mano para el verano", [6],
 "El bocadillo es el plato del verano: playa, excursión y evento. Bolsa abierta a dos "
 "lados y envoltorio antigrasa.",
 "Bar, panadería, food truck", ["bolsas-de-papel", "papel-antigrasa"], True),

# ─────────────── JULIO ───────────────
("Take away de playa: bolsas y envases que aguantan el calor", [7],
 "Julio es el pico de consumo fuera. El envase tiene que aguantar temperatura, humedad y "
 "transporte sin perder forma.",
 "Chiringuito, take away, delivery", ["take-away", "bolsas-de-papel"], True),

("Fritos y aperitivos de barra: cajetillas, cucuruchos y vasos abiertos", [7],
 "El aperitivo de verano se sirve en formato individual y de pie. Producto de fabricación "
 "propia, margen bueno y reposición semanal.",
 "Bar de tapas, chiringuito, cervecería", ["recipientes-para-fritas"], True),

("Hamburguesas y bocadillos: el papel que no traspasa", [7],
 "En julio el volumen de hamburguesa se dispara y el papel malo se nota enseguida. "
 "Antigrasa de fabricación propia, con o sin diseño.",
 "Fast food, hamburguesería, food truck", ["papel-antigrasa"], True),

("Servilletas dispensadas: máximo volumen con mínimo desperdicio", [7],
 "Cuando la sala va a tope el consumo de servilleta se descontrola. El dispensador es la "
 "única forma de acotarlo.",
 "Fast food, autoservicio, colectividades", ["servilletas-de-papel"], True),

("Mantelines: cambiar la mesa en segundos con lleno total", [7],
 "Con rotación alta, el mantelín es lo que permite dejar la mesa lista sin limpiar. "
 "Precortado, en paquete, y con diseño de temporada.",
 "Terraza, restaurante de menú, cafetería", ["manteles-individuales"], True),

("Granizados y bebidas frías: el vaso adecuado para cada bebida", [7],
 "Cada bebida pide su vaso: granizado, batido, smoothie y refresco tienen tapa y pajita "
 "distintas. Es una venta de surtido, no de referencia.",
 "Heladería, chiringuito, cafetería", ["vasos-de-carton-bebidas-frias"], False),

("Reposición de julio: lo que no puede faltarle en agosto", [7],
 "El argumento más nuestro: stock permanente y entrega rápida. En agosto no hay margen "
 "para esperar un pedido, y el cliente lo sabe.",
 "Todos", ["servilletas-de-papel", "manteles-de-papel"], True),

("Posavasos: la barra en temporada alta", [7],
 "Producto pequeño, de fabricación propia y personalizable, que se consume sin parar en "
 "temporada de terraza.",
 "Bar, cervecería, chiringuito, hotel", ["posavasos"], True),

("Bolsas de papel para el comercio de temporada", [7],
 "Julio es rebajas y turismo. El comercio de zona turística necesita bolsa con imagen y "
 "en cantidad.",
 "Comercio, souvenir, panadería", ["bolsas-kraft"], True),

# ─────────────── AGOSTO ───────────────
("Reposición de agosto: 6.000 referencias en stock y entrega rápida", [8],
 "En agosto el hostelero no planifica, apaga fuegos. Lo que vende es disponibilidad "
 "inmediata, y es exactamente nuestra ventaja.",
 "Todos", ["manteles-de-papel", "servilletas-de-papel"], True),

("Canguro y Mini Servis: rapidez con personal de refuerzo", [8],
 "En agosto la plantilla es nueva y no conoce la casa. El producto que simplifica el "
 "gesto reduce el error del camarero de temporada.",
 "Restaurante, terraza, colectividades", ["servilletas-kangaroo"], True),

("Aperitivos de barra: presentación rápida en papel", [8],
 "El aperitivo de agosto se sirve sin parar. Papelina, cucurucho y antigrasa: se prepara "
 "antes, se sirve en un gesto.",
 "Bar de tapas, cervecería, chiringuito", ["papelinas", "papel-antigrasa"], True),

("Comida para llevar en pleno agosto: envases para todo el día", [8],
 "El take away de agosto no tiene hora punta, tiene todo el día. Envase que aguante "
 "espera en expositor y traslado.",
 "Take away, delivery, supermercado", ["take-away"], False),

("Mantelería de diario en formato de volumen", [8],
 "En agosto se consume mantelería como en ningún otro mes. Formato en rollo y en "
 "paquete grande, para no reponer cada dos días.",
 "Restaurante, terraza, colectividades", ["manteles-de-papel"], True),

("Bolsas para bollería y desayunos de verano", [8],
 "El desayuno de agosto es en terraza y para llevar. Consumo diario de bolsa pequeña en "
 "panadería y hotel.",
 "Panadería, hotel, cafetería", ["bolsas-para-croissant"], True),

("Tarrinas de helado: la punta de la temporada", [8],
 "Agosto es el techo del año en helado. Última reposición fuerte antes de que baje "
 "en septiembre.",
 "Heladería, chiringuito", ["tarrinas-para-helados"], True),

("Prepare septiembre: la mesa para la vuelta al menú del día", [8],
 "LA COMPRA SE ADELANTA: en septiembre vuelve el menú diario y la mantelería de sala. "
 "Quien lo plantea en agosto llega antes que el pedido de urgencia.",
 "Restaurante de menú, cafetería", ["manteles-individuales", "servilletas-de-papel"], True),

("Papel antigrasa para la fritura de temporada alta", [8],
 "Consumo continuo en agosto y producto donde la calidad se nota. Reposición segura.",
 "Freiduría, chiringuito, fast food", ["papel-antigrasa"], True),

# ─────────────── SEPTIEMBRE ───────────────
("Vuelta al menú del día: mantelines y servilletas de diario", [9],
 "Septiembre reabre el menú de mediodía y la sala de diario. Es la segunda compra de "
 "reposición más grande del año, después de enero.",
 "Restaurante de menú, cafetería, colectividades", ["manteles-individuales", "servilletas-de-papel"], True),

("Catering de empresa y coffee break: vasos, bandejas y servilleta", [9],
 "Vuelven las reuniones, las formaciones y los desayunos de trabajo. Consumo recurrente "
 "y cliente que pide siempre lo mismo.",
 "Catering, hotel, colectividades, empresa", ["vasos-de-carton-bebidas-calientes", "bandejas-traiteur"], False),

("Comida de oficina: envases microondables para llevar", [9],
 "El menú de oficina vuelve en septiembre. Envase que se pueda calentar sin trasvasar "
 "es lo que decide la compra.",
 "Take away, delivery, restaurante de menú", ["recipientes-take-away-microondables"], False),

("Vendimia y enoturismo: vestir la mesa del vino", [9],
 "Septiembre y octubre son temporada de bodega y visita. Mantelería, posavasos y "
 "presentación para una mesa que se fotografía.",
 "Bodega, restaurante, enoturismo, hotel", ["manteles-de-papel", "posavasos"], True),

("Panadería: la nueva temporada de bollería", [9],
 "Con el frío vuelve el bollo y el desayuno sentado. Bolsa, papel y bandeja para una "
 "temporada que va de septiembre a marzo.",
 "Panadería, pastelería, cafetería", ["bolsas-para-croissant", "pasteleria"], True),

("Personalice con su logo: pídalo ahora para tenerlo en Navidad", [9],
 "LA COMPRA SE ADELANTA: la personalización necesita plazo de producción. Quien lo "
 "quiere para Navidad tiene que pedirlo en septiembre.",
 "Restaurante, cadena, hotel, franquicia", ["personalizados"], True),

("Like-Linen: la mesa de otoño con efecto tela", [9, 10],
 "Cambio de temporada a tonos cálidos y gama alta. Fabricación propia y el producto que "
 "mejor sube la percepción de la mesa.",
 "Restaurante de mantel, hotel, catering", ["like-linen"], True),

("Bolsas de papel: vuelta al comercio de barrio", [9],
 "Septiembre reactiva el comercio de proximidad. Bolsa kraft, con asa, y la posibilidad "
 "de personalizarla en tirada corta.",
 "Comercio, panadería, take away", ["bolsas-kraft"], True),

("PFAS Free: la normativa de envases, al día", [9, 3],
 "El cliente profesional pregunta por la normativa y no quiere quedarse con stock no "
 "conforme. Es una venta por tranquilidad, no por precio.",
 "Todos, especialmente cadenas y colectividades", ["pfas-free"], True),

("Comedores escolares y colectividades: vuelta al curso", [8, 9],
 "Septiembre reabre comedores escolares, hospitales y empresas en todos los mercados. "
 "Son contratos de volumen que se cierran de una vez para todo el curso.",
 "Colectividades, catering social, comedor escolar", ["manteles-individuales", "servilletas-de-papel"], True),

("Fiestas de la cerveza: servicio de pie y volumen concentrado", [9],
 "De septiembre a octubre las fiestas cerveceras mueven cifras enormes en Alemania y "
 "cada vez más en el resto de Europa. Posavasos, papel antigrasa y envase de frito.",
 "Cervecería, carpa, festival, food truck", ["posavasos", "papel-antigrasa"], True),

# ─────────────── OCTUBRE ───────────────
("La Navidad se compra ahora: mantelería y servilletas de Navidad", [10],
 "LA COMPRA SE ADELANTA DOS MESES: el hostelero cierra la mantelería de Navidad en "
 "octubre. En diciembre ya solo repone lo que le falta.",
 "Restaurante, hotel, catering, colectividades", ["servilletas-de-navidad", "manteles-de-navidad"], True),

("Street food de otoño: cucuruchos y papelinas para fritos y frutos secos", [10],
 "En octubre vuelve el puesto de calle y el mercado de invierno en toda Europa. Envase "
 "de fabricación propia, temporada corta y consumo intenso.",
 "Puesto de calle, feria, mercado, food truck", ["cucuruchos-de-papel", "papelinas"], True),

("Halloween: mantelería y bolsas decoradas", [10],
 "Fecha cada vez más comercial en hostelería y comercio en toda Europa. Producto "
 "decorado, temporada de una semana y pedido que se repite cada año.",
 "Bar, cafetería, comercio, pastelería", ["conjuntos-decorados"], True),

("Pastelería de otoño: formato pequeño, cápsulas y blondas", [10],
 "Cada mercado tiene su dulce de otoño, y todos comparten el mismo problema: formato "
 "pequeño, presentación cuidada y temporada muy corta.",
 "Pastelería, obrador, panadería", ["pasteleria", "blondas"], True),

("Vuelven las sopas y las cremas: tarrinas con tapa estanca", [10],
 "Con el frío la sopa vuelve a la carta y al take away. El problema es que no se derrame: "
 "tapa con cierre y material que aguante el caliente.",
 "Restaurante de menú, take away, delivery", ["tarrinas-para-sopas"], True),

("La mesa de otoño: setas, caza y cocido", [10, 11],
 "Cambio de carta a producto de temporada y de más ticket. Ocasión para subir de calidad "
 "en mantelería y servilleta.",
 "Restaurante, asador, hotel", ["like-linen", "airlaid"], True),

("Bebidas calientes: el vaso de cartón para la temporada", [10],
 "El café para llevar sube con el frío y no baja hasta abril. Compra de temporada con "
 "reposición mensual.",
 "Cafetería, panadería, gasolinera", ["vasos-de-carton-bebidas-calientes"], False),

("Cenas de empresa: reserve la mantelería antes de que se agote", [10],
 "LA COMPRA SE ADELANTA: la cena de empresa se contrata en octubre y noviembre. El "
 "restaurante que espera a diciembre no encuentra el diseño que quiere.",
 "Restaurante de grupos, hotel, catering", ["conjuntos-decorados", "manteles-de-papel"], True),

("Bolsas de papel para el comercio de otoño", [10],
 "Arranca la campaña larga que va de octubre a Reyes. El comercio hace la compra grande "
 "de bolsa ahora.",
 "Comercio, panadería, pastelería", ["bolsas-kraft"], True),

# ─────────────── NOVIEMBRE ───────────────
("Cenas de empresa: la mesa que justifica el precio del menú", [11],
 "El menú de empresa se vende por la puesta en escena. Mantelería coordinada y "
 "Tête-à-Tête cambian la percepción del mismo menú.",
 "Restaurante de grupos, hotel, catering", ["conjuntos-decorados", "tete-a-tete"], True),

("Black Friday: bolsas de papel para el comercio", [11],
 "Semana de volumen máximo en comercio. La bolsa se pide con dos semanas de antelación "
 "y se agota en tres días.",
 "Comercio, take away, pastelería", ["bolsas-kraft", "papel-y-bolsas-para-regalos"], True),

("Menús de Navidad: mantelería coordinada de principio a fin", [11],
 "El conjunto decorado vende porque resuelve la mesa entera de una vez: mantel, "
 "servilleta, camino y detalle, todo del mismo diseño.",
 "Restaurante, hotel, catering", ["conjuntos-decorados"], True),

("Catering navideño: bandejas, cajas y transporte", [11],
 "El catering de Navidad se cierra en noviembre. Transporte y presentación son el "
 "cuello de botella, no el producto.",
 "Catering, traiteur, colectividades", ["bandejas-traiteur", "take-away"], True),

("Lotes y regalos de empresa: papel, bolsas y cajas de botella", [11],
 "La cesta de empresa se monta en noviembre. Es venta de presentación pura, con margen "
 "y con fecha límite muy clara.",
 "Comercio gourmet, bodega, empresa, cesta", ["cajas-para-botellas-y-lotes", "papel-y-bolsas-para-regalos"], True),

("Pastelería de Navidad: cajas, blondas y cápsulas", [11],
 "El obrador prepara turrón, tronco y polvorones en noviembre. Compra de envase "
 "concentrada y muy anticipada al consumo.",
 "Pastelería, obrador, panadería", ["pasteleria", "blondas"], True),

("Últimos días para personalizar con su logo antes de Navidad", [11],
 "Cierre de plazo de producción. Es un argumento de urgencia real, no inventado, y "
 "funciona muy bien en noviembre.",
 "Restaurante, hotel, cadena, comercio", ["personalizados"], True),

("Fin de Año: bolsas y complementos de fiesta", [11],
 "LA COMPRA SE ADELANTA: se compra en noviembre porque en diciembre ya no llega. "
 "Producto para una sola noche y de margen alto.",
 "Discoteca, restaurante, hotel, comercio", ["bolsas-de-cotillon", "cotillon"], True),

("Servilletas de Navidad: todas las calidades, del tisú al Like-Linen", [11],
 "Misma ocasión, cuatro niveles de precio. Permite entrar en cualquier cliente y subir "
 "la gama al año siguiente.",
 "Todos", ["servilletas-de-navidad"], True),

("Mercados de Navidad: consumo en la calle con frío", [10, 11],
 "Los mercados navideños de Alemania, Francia y Austria son seis semanas de consumo de "
 "pie y a la intemperie. Vaso caliente, cucurucho y papel antigrasa, en volumen.",
 "Puesto de mercado, caseta, food truck, hostelería de calle",
 ["vasos-de-carton-bebidas-calientes", "cucuruchos-de-papel"], True),

# ─────────────── DICIEMBRE ───────────────
("La mesa de Navidad: servilletas, manteles y Tête-à-Tête", [12],
 "Reposición de diciembre: el que se quedó corto compra ahora y sin discutir precio. "
 "Entrega rápida es lo único que importa.",
 "Restaurante, hotel, catering", ["manteles-de-navidad", "servilletas-de-navidad"], True),

("Fin de Año: última llamada para la noche del 31", [12],
 "Pedido corto, urgente y de margen alto. Aquí no se compite por precio, se compite "
 "por llegar a tiempo.",
 "Discoteca, restaurante, hotel", ["bolsas-de-cotillon"], True),

("Lotes y regalos: papel, bolsas y cajas de botella", [12],
 "Las dos primeras semanas de diciembre son el pico de la cesta de empresa y del regalo "
 "gourmet.",
 "Comercio gourmet, bodega, cesta, empresa", ["cajas-para-botellas-y-lotes"], True),

("Pastelería de Navidad: presentar el turrón y el tronco", [12],
 "El obrador vende del 1 al 24 y necesita reponer envase a mitad de campaña. Caja, "
 "bandeja y blonda de presentación.",
 "Pastelería, obrador, panadería", ["pasteleria"], True),

("Comida para llevar en festivos: envases y bolsas para los días grandes", [12],
 "Nochebuena, Navidad y Fin de Año se comen cada vez más en casa con comida encargada. "
 "Envase de transporte y presentación.",
 "Restaurante, take away, catering, charcutería", ["take-away", "bolsas-de-papel"], True),

("Reposición de última hora: entrega rápida antes de Nochebuena", [12],
 "El argumento del stock permanente en su momento de máximo valor. Aquí no se compite "
 "por precio, se compite por llegar.",
 "Todos", ["servilletas-de-navidad", "manteles-de-navidad"], True),

("La mesa de Fin de Año: mantelería de gala", [12],
 "La cena del 31 es el servicio de más ticket del año. El cliente acepta subir de gama "
 "en mantelería para esa noche.",
 "Restaurante, hotel", ["like-linen", "conjuntos-decorados"], True),

("Dulce de Reyes: prepare la caja antes de que empiece a venderse", [11],
 "LA COMPRA SE ADELANTA: el roscón se vende del 28 de diciembre al 6 de enero, y la caja "
 "hay que tenerla antes. Es el último pedido del año y el primero del siguiente.",
 "Pastelería, panadería, obrador", ["cajas-para-pasteleria"], True),

("Take away de Navidad: transportar el plato preparado", [12],
 "La charcutería y el restaurante venden platos para casa. Bandeja con funda, caja "
 "rígida y bolsa que aguante el peso.",
 "Charcutería, restaurante, catering", ["bandejas-traiteur"], True),
]

def como_diccionarios():
    return [{'tema': t, 'meses': m, 'razon': r, 'cliente': c, 'claves': k, 'propia': p}
            for t, m, r, c, k, p in OCASIONES]

if __name__ == '__main__':
    import json, collections
    ocas = como_diccionarios()
    print(f'{len(ocas)} ocasiones comerciales')
    porme = collections.Counter()
    for o in ocas:
        for m in o['meses']:
            porme[m] += 1
    print('disponibles por mes:', {m: porme[m] for m in range(1, 13)})
    print('de fabricacion propia:', sum(1 for o in ocas if o['propia']), '/', len(ocas))
    json.dump({'ocasiones': ocas}, open('data/calendario-comercial.json', 'w'),
              ensure_ascii=False, indent=1)
    print('-> data/calendario-comercial.json')
