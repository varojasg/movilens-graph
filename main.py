import os
from collections import defaultdict
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, PathPatch
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import Affine2D

CARPETA_DATASET = os.path.join("data", "ml-1m")
CARPETA_RESULTADOS = "resultados"

usuarios_movielens = {}
peliculas_movielens = {}
lista_adyacencia = defaultdict(list)


def registrar_nodo(nombre_nodo):
    if nombre_nodo not in lista_adyacencia:
        lista_adyacencia[nombre_nodo] = []


def conectar_usuario_pelicula(usuario, pelicula, calificacion):
    lista_adyacencia[usuario].append((pelicula, calificacion))
    lista_adyacencia[pelicula].append((usuario, calificacion))


def cargar_usuarios():
    ruta_usuarios = os.path.join(CARPETA_DATASET, "users.dat")

    # Primero cargamos todos los usuarios del dataset y los registramos como nodos.
    with open(ruta_usuarios, "r", encoding="latin-1") as archivo_usuarios:
        for linea in archivo_usuarios:
            datos_usuario = linea.strip().split("::")
            id_usuario = datos_usuario[0]
            usuarios_movielens[id_usuario] = datos_usuario[1:]
            registrar_nodo("U" + id_usuario)


def cargar_peliculas():
    ruta_peliculas = os.path.join(CARPETA_DATASET, "movies.dat")

    # A continuacion cargamos las peliculas para poder mostrar sus titulos reales.
    with open(ruta_peliculas, "r", encoding="latin-1") as archivo_peliculas:
        for linea in archivo_peliculas:
            datos_pelicula = linea.strip().split("::")
            id_pelicula = datos_pelicula[0]
            titulo_pelicula = datos_pelicula[1]
            peliculas_movielens[id_pelicula] = titulo_pelicula
            registrar_nodo("M" + id_pelicula)


def cargar_calificaciones():
    ruta_calificaciones = os.path.join(CARPETA_DATASET, "ratings.dat")
    total_calificaciones = 0

    # Aqui relacionamos cada usuario con la pelicula que califico y guardamos el rating.
    with open(ruta_calificaciones, "r", encoding="latin-1") as archivo_calificaciones:
        for linea in archivo_calificaciones:
            datos_calificacion = linea.strip().split("::")
            nodo_usuario = "U" + datos_calificacion[0]
            nodo_pelicula = "M" + datos_calificacion[1]
            calificacion = int(datos_calificacion[2])

            conectar_usuario_pelicula(nodo_usuario, nodo_pelicula, calificacion)
            total_calificaciones += 1

    return total_calificaciones


def guardar_resumen_grafo(total_calificaciones):
    peliculas_calificadas = 0

    # Primero contamos cuantas peliculas tienen al menos una conexion dentro del grafo.
    for id_pelicula in peliculas_movielens:
        nodo_pelicula = "M" + id_pelicula
        if len(lista_adyacencia[nodo_pelicula]) > 0:
            peliculas_calificadas += 1

    total_usuarios = len(usuarios_movielens)
    total_peliculas = len(peliculas_movielens)
    total_nodos = len(usuarios_movielens) + len(peliculas_movielens)
    total_nodos_conectados = total_usuarios + peliculas_calificadas

    print("Cantidad de usuarios:", total_usuarios)
    print("Cantidad de peliculas:", total_peliculas)
    print("Peliculas con calificaciones:", peliculas_calificadas)
    print("Cantidad total de nodos:", total_nodos)
    print("Nodos conectados:", total_nodos_conectados)
    print("Cantidad de aristas:", total_calificaciones)

    ruta_resumen = os.path.join(CARPETA_RESULTADOS, "resumen_grafo_movielens.txt")

    # Finalmente guardamos estos datos para utilizarlos despues en el informe.
    with open(ruta_resumen, "w", encoding="utf-8") as archivo_resumen:
        archivo_resumen.write(f"Cantidad de usuarios: {total_usuarios}\n")
        archivo_resumen.write(f"Cantidad de peliculas: {total_peliculas}\n")
        archivo_resumen.write(f"Peliculas con calificaciones: {peliculas_calificadas}\n")
        archivo_resumen.write(f"Cantidad total de nodos: {total_nodos}\n")
        archivo_resumen.write(f"Nodos conectados: {total_nodos_conectados}\n")
        archivo_resumen.write(f"Cantidad de aristas: {total_calificaciones}\n")


def elegir_subgrafo_bipartito(inicio_usuario, fin_usuario, cantidad_usuarios_objetivo=8, cantidad_peliculas_objetivo=4):
    usuarios_candidatos = [str(i) for i in range(inicio_usuario, fin_usuario + 1)]

    ratings_altos = []
    apariciones_pelicula = defaultdict(int)

    # Primero reunimos calificaciones altas de un bloque pequeno de usuarios.
    for id_usuario in usuarios_candidatos:
        for pelicula, rating in lista_adyacencia["U" + id_usuario]:
            if rating >= 4:
                id_pelicula = pelicula[1:]
                ratings_altos.append((id_usuario, id_pelicula, rating))
                apariciones_pelicula[id_pelicula] += 1

    # A continuacion elegimos peliculas compartidas para que el dibujo quede limpio.
    peliculas_ordenadas = sorted(
        apariciones_pelicula.items(),
        key=lambda elemento: (-elemento[1], int(elemento[0]))
    )

    peliculas_seleccionadas = []
    for id_pelicula, repeticiones in peliculas_ordenadas:
        if repeticiones >= 2:
            peliculas_seleccionadas.append(id_pelicula)
        if len(peliculas_seleccionadas) == cantidad_peliculas_objetivo:
            break

    aristas_seleccionadas = []
    conteo_usuario = defaultdict(int)
    conteo_pelicula = defaultdict(int)
    usuarios_seleccionados = set()

    # Luego elegimos pocas relaciones por pelicula y maximo dos por usuario.
    for id_pelicula in peliculas_seleccionadas:
        conexiones_pelicula = [
            (id_usuario, rating)
            for id_usuario, pelicula, rating in ratings_altos
            if pelicula == id_pelicula
        ]
        conexiones_pelicula = sorted(conexiones_pelicula, key=lambda x: (conteo_usuario[x[0]], int(x[0]), -x[1]))

        for id_usuario, rating in conexiones_pelicula:
            if conteo_pelicula[id_pelicula] >= 2:
                break
            if conteo_usuario[id_usuario] >= 2:
                continue

            aristas_seleccionadas.append((id_usuario, id_pelicula, rating))
            conteo_usuario[id_usuario] += 1
            conteo_pelicula[id_pelicula] += 1
            usuarios_seleccionados.add(id_usuario)

    # Si faltan usuarios, agregamos una sola conexion limpia por usuario nuevo.
    for id_pelicula in peliculas_seleccionadas:
        if len(usuarios_seleccionados) >= cantidad_usuarios_objetivo:
            break

        conexiones_pelicula = [
            (id_usuario, rating)
            for id_usuario, pelicula, rating in ratings_altos
            if pelicula == id_pelicula
        ]
        conexiones_pelicula = sorted(conexiones_pelicula, key=lambda x: (int(x[0]), -x[1]))

        for id_usuario, rating in conexiones_pelicula:
            if len(usuarios_seleccionados) >= cantidad_usuarios_objetivo:
                break
            if id_usuario in usuarios_seleccionados:
                continue
            if conteo_pelicula[id_pelicula] >= 3:
                break

            aristas_seleccionadas.append((id_usuario, id_pelicula, rating))
            conteo_usuario[id_usuario] += 1
            conteo_pelicula[id_pelicula] += 1
            usuarios_seleccionados.add(id_usuario)

    usuarios_finales = sorted(list(usuarios_seleccionados), key=int)[:cantidad_usuarios_objetivo]
    usuarios_validos = set(usuarios_finales)

    aristas_filtradas = []
    peliculas_finales = set()
    for id_usuario, id_pelicula, rating in aristas_seleccionadas:
        if id_usuario in usuarios_validos:
            aristas_filtradas.append((id_usuario, id_pelicula, rating))
            peliculas_finales.add(id_pelicula)

    peliculas_finales = sorted(list(peliculas_finales), key=int)
    return usuarios_finales, peliculas_finales, aristas_filtradas


def ordenar_para_menos_cruces(usuarios, peliculas, aristas):
    indice_usuario = {id_usuario: i for i, id_usuario in enumerate(sorted(usuarios, key=int))}

    for _ in range(4):
        promedio_pelicula = {}
        for id_pelicula in peliculas:
            usuarios_conectados = [indice_usuario[id_usuario] for id_usuario, pelicula, rating in aristas if pelicula == id_pelicula]
            promedio_pelicula[id_pelicula] = sum(usuarios_conectados) / len(usuarios_conectados)

        peliculas = sorted(peliculas, key=lambda id_pelicula: (promedio_pelicula[id_pelicula], int(id_pelicula)))
        indice_pelicula = {id_pelicula: i for i, id_pelicula in enumerate(peliculas)}

        promedio_usuario = {}
        for id_usuario in usuarios:
            peliculas_conectadas = [indice_pelicula[id_pelicula] for usuario, id_pelicula, rating in aristas if usuario == id_usuario]
            promedio_usuario[id_usuario] = sum(peliculas_conectadas) / len(peliculas_conectadas)

        usuarios = sorted(usuarios, key=lambda id_usuario: (promedio_usuario[id_usuario], int(id_usuario)))
        indice_usuario = {id_usuario: i for i, id_usuario in enumerate(usuarios)}

    return usuarios, peliculas


def partir_titulo(titulo, ancho=14):
    return "\n".join(textwrap.wrap(titulo, width=ancho))


def dibujar_icono_usuario(ax, x, y):
    # Primero dibujamos la cabeza del usuario.
    cabeza = Circle((x, y + 0.23), 0.11, facecolor="black", edgecolor="black", zorder=4)
    ax.add_patch(cabeza)

    # A continuacion dibujamos el cuerpo como una forma redondeada.
    cuerpo = FancyBboxPatch(
        (x - 0.18, y - 0.18),
        0.36,
        0.30,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor="black",
        edgecolor="black",
        zorder=4
    )
    ax.add_patch(cuerpo)


def dibujar_icono_pelicula(ax, x, y, titulo):
    # Aqui dibujamos una claqueta sencilla para representar la pelicula.
    base = FancyBboxPatch(
        (x - 0.60, y - 0.28),
        1.20,
        0.56,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor="black",
        edgecolor="black",
        zorder=4
    )
    ax.add_patch(base)

    parte_superior = Rectangle(
        (x - 0.62, y + 0.22),
        1.24,
        0.17,
        angle=8,
        facecolor="black",
        edgecolor="black",
        zorder=4
    )
    ax.add_patch(parte_superior)

    for desplazamiento in [-0.45, -0.20, 0.05, 0.30]:
        raya = Rectangle(
            (x + desplazamiento, y + 0.235),
            0.12,
            0.12,
            angle=8,
            facecolor="white",
            edgecolor="white",
            zorder=5
        )
        ax.add_patch(raya)

    ax.text(
        x,
        y - 0.01,
        partir_titulo(titulo, 14),
        ha="center",
        va="center",
        fontsize=8.0,
        color="white",
        fontweight="bold",
        zorder=5
    )


def dibujar_estrella_rating(ax, x, y, rating):
    # Primero dibujamos una sola estrella gris como fondo.
    fuente = FontProperties(weight="bold")
    estrella = TextPath((0, 0), "★", size=1, prop=fuente)
    bbox = estrella.get_extents()

    ancho_objetivo = 0.56
    alto_objetivo = 0.56
    escala_x = ancho_objetivo / bbox.width
    escala_y = alto_objetivo / bbox.height

    transformacion = (
        Affine2D()
        .scale(escala_x, escala_y)
        .translate(x - ancho_objetivo / 2, y - alto_objetivo / 2)
    )

    estrella_gris = PathPatch(
        estrella,
        transform=transformacion + ax.transData,
        facecolor="#d9d9d9",
        edgecolor="none",
        lw=0.0,
        zorder=2
    )
    ax.add_patch(estrella_gris)

    # Luego pintamos solo el porcentaje correspondiente al rating.
    fraccion = rating / 5.0
    estrella_amarilla = PathPatch(
        estrella,
        transform=transformacion + ax.transData,
        facecolor="#f4d21f",
        edgecolor="none",
        lw=0.0,
        zorder=3
    )

    clip = Rectangle(
        (x - ancho_objetivo / 2, y - alto_objetivo / 2),
        ancho_objetivo * fraccion,
        alto_objetivo,
        transform=ax.transData
    )
    estrella_amarilla.set_clip_path(clip.get_path(), clip.get_transform())
    ax.add_patch(estrella_amarilla)

    ax.text(
        x,
        y + 0.01,
        str(rating),
        ha="center",
        va="center",
        fontsize=10.0,
        fontweight="bold",
        color="black",
        zorder=5
    )


def generar_visualizacion_bipartita(indice_subgrafo, inicio_usuario, fin_usuario):
    usuarios, peliculas, aristas = elegir_subgrafo_bipartito(
        inicio_usuario,
        fin_usuario,
        cantidad_usuarios_objetivo=8,
        cantidad_peliculas_objetivo=4
    )

    if len(usuarios) < 4 or len(peliculas) < 2:
        print(f"No se pudo generar el subgrafo {indice_subgrafo} con suficientes datos.")
        return

    usuarios, peliculas = ordenar_para_menos_cruces(usuarios, peliculas, aristas)

    fig, ax = plt.subplots(figsize=(14, 8.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    x_usuario = 1.7
    x_pelicula = 12.0

    espacio_vertical_usuarios = 0.95
    espacio_vertical_peliculas = 1.55

    y_inicio_usuarios = len(usuarios) * espacio_vertical_usuarios + 0.9
    y_inicio_peliculas = len(peliculas) * espacio_vertical_peliculas + 1.0

    posiciones_usuarios = {}
    posiciones_peliculas = {}

    # Primero colocamos los usuarios en el lado izquierdo.
    for indice, id_usuario in enumerate(usuarios):
        y = y_inicio_usuarios - indice * espacio_vertical_usuarios
        posiciones_usuarios[id_usuario] = (x_usuario, y)

    # A continuacion colocamos las peliculas en el lado derecho.
    for indice, id_pelicula in enumerate(peliculas):
        y = y_inicio_peliculas - indice * espacio_vertical_peliculas
        posiciones_peliculas[id_pelicula] = (x_pelicula, y)

    # Preparamos una regla para que las estrellas no se superpongan.
    conexiones_por_usuario = defaultdict(list)
    for id_usuario, id_pelicula, rating in aristas:
        conexiones_por_usuario[id_usuario].append((id_pelicula, rating))

    offset_marcador = {}
    for id_usuario, conexiones in conexiones_por_usuario.items():
        conexiones_ordenadas = sorted(
            conexiones,
            key=lambda elemento: posiciones_peliculas[elemento[0]][1],
            reverse=True
        )

        if len(conexiones_ordenadas) == 1:
            offsets = [0.0]
        else:
            offsets = [-0.18, 0.18]

        for indice, (id_pelicula, rating) in enumerate(conexiones_ordenadas):
            offset_marcador[(id_usuario, id_pelicula, rating)] = offsets[indice]

    # Dibujamos primero las aristas y su estrella correspondiente.
    for id_usuario, id_pelicula, rating in aristas:
        if id_usuario not in posiciones_usuarios or id_pelicula not in posiciones_peliculas:
            continue

        x1, y1 = posiciones_usuarios[id_usuario]
        x2, y2 = posiciones_peliculas[id_pelicula]

        x_inicio = x1 + 0.65
        x_fin = x2 - 0.95

        ax.plot(
            [x_inicio, x_fin],
            [y1, y2],
            color="black",
            linewidth=1.15,
            zorder=1
        )

        # A continuacion ubicamos la estrella sobre la linea, pero cerca del usuario.
        t = 0.27
        xm = x_inicio + t * (x_fin - x_inicio)
        ym = y1 + t * (y2 - y1)
        ym += offset_marcador.get((id_usuario, id_pelicula, rating), 0.0)

        dibujar_estrella_rating(ax, xm, ym, rating)

    # Luego dibujamos los usuarios.
    for id_usuario in usuarios:
        x, y = posiciones_usuarios[id_usuario]
        dibujar_icono_usuario(ax, x, y + 0.02)

        ax.text(
            x,
            y - 0.46,
            f"Usuario {id_usuario}",
            ha="center",
            va="top",
            fontsize=11.0,
            fontweight="bold",
            color="black",
            zorder=5
        )

    # Finalmente dibujamos las peliculas.
    for id_pelicula in peliculas:
        x, y = posiciones_peliculas[id_pelicula]
        dibujar_icono_pelicula(ax, x, y, peliculas_movielens[id_pelicula])

    ax.set_xlim(0.8, 13.5)
    ax.set_ylim(0.6, max(y_inicio_usuarios, y_inicio_peliculas) + 0.8)
    ax.axis("off")
    plt.tight_layout()

    ruta_resultados = os.path.abspath(CARPETA_RESULTADOS)
    os.makedirs(ruta_resultados, exist_ok=True)
    ruta_imagen = os.path.join(ruta_resultados, f"grafo_bipartito_movielens_{indice_subgrafo}.png")

    figura_actual = plt.gcf()
    figura_actual.savefig(
        ruta_imagen,
        dpi=220,
        bbox_inches="tight",
        format="png"
    )
    plt.close(figura_actual)

    print(f"Imagen generada en: {ruta_imagen}")


def main():
    os.makedirs(CARPETA_RESULTADOS, exist_ok=True)

    # Primero cargamos el dataset original de MovieLens 1M.
    cargar_usuarios()
    cargar_peliculas()
    total_calificaciones = cargar_calificaciones()

    # A continuacion guardamos los datos basicos del grafo completo.
    guardar_resumen_grafo(total_calificaciones)

    # Finalmente generamos tres subgrafos distintos para el informe.
    rangos = [(1, 40), (41, 80), (81, 120)]
    for indice, (inicio_usuario, fin_usuario) in enumerate(rangos, start=1):
        generar_visualizacion_bipartita(indice, inicio_usuario, fin_usuario)


if __name__ == "__main__":
    main()
