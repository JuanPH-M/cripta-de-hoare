"""
Aplicación pygame: bucle principal, máquina de estados de pantallas, entrada,
y traducción de los eventos de la simulación en sonido y efectos.
"""

import math

import pygame

from juego.core import config
from juego.datos import persistencia, tablas
from juego.sistemas import economia
from juego.sistemas.partida import Entrada, Evento
from juego.sistemas.progresion import nombre_nivel
from juego.sistemas.run import Run
from juego.ui import pantallas, paleta, textos
from juego.ui.audio import Audio
from juego.ui.efectos import Efectos
from juego.ui.escena import Escena
from juego.ui.hud import Hud
from juego.ui.tween import ease_in_out, ease_out_cubic

W, H = config.ANCHO_VENTANA, config.ALTO_VENTANA
E = config.ESCALA

TECLAS_ARRIBA = (pygame.K_w, pygame.K_UP)
TECLAS_ABAJO = (pygame.K_s, pygame.K_DOWN)
TECLAS_IZQ = (pygame.K_a, pygame.K_LEFT)
TECLAS_DER = (pygame.K_d, pygame.K_RIGHT)
TECLAS_ATAQUE = (pygame.K_SPACE, pygame.K_j)
TECLAS_DASH = (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k)
TECLAS_OK = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BUFFER = 0.15  # segundos que se "recuerda" una pulsación hecha un poco antes de tiempo


def _vineta(color: tuple, fuerza: float) -> pygame.Surface:
    """Viñeta radial en resolución de lienzo (se escala junto con el mundo)."""
    peq = pygame.Surface((160, 90), pygame.SRCALPHA)
    for y in range(90):
        for x in range(160):
            dx = (x - 80) / 80
            dy = (y - 45) / 45
            d = min(1.0, math.sqrt(dx * dx + dy * dy) / 1.25)
            peq.set_at((x, y), (*color, int(255 * fuerza * d ** 2.4)))
    return pygame.transform.smoothscale(peq, (config.ANCHO_LIENZO, config.ALTO_LIENZO)).convert_alpha()


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(config.TITULO)
        self.pantalla = pygame.display.set_mode((W, H), pygame.SCALED)
        self.lienzo = pygame.Surface((config.ANCHO_LIENZO, config.ALTO_LIENZO))
        self.reloj = pygame.time.Clock()
        self.audio = Audio()
        self.efectos = Efectos()
        self.escena = Escena(self.efectos)
        self.hud = Hud()
        self.vineta_negra = _vineta(paleta.NOCHE, 0.75)
        self.vineta_roja = _vineta(paleta.ROJO, 0.8)
        self.capa_flash = pygame.Surface((config.ANCHO_LIENZO, config.ALTO_LIENZO))
        self.ranking = persistencia.cargar_ranking()

        self.ejecutando = True
        self.t = 0.0
        self.estado = "menu"
        self.t_estado = 0.0
        self.seleccion = 0
        self.zonas: list = []
        self.run: Run | None = None
        self.partida = None
        self.puesto = -1

        self.escala_tiempo = 1.0
        self.t_secuencia = 0.0          # cuenta atrás de muerte / victoria
        self.secuencia = ""
        self.panel_verificacion = False
        self.buffer_ataque = 0.0
        self.buffer_dash = 0.0
        self.pulso_pocion = False
        self.pulso_bomba = False
        self.apuntar_raton = False
        self.banner: tuple[str, str] | None = None
        self.t_banner = 0.0
        self.t_latido = 0.0
        self.t_sonido_moneda = 0.0
        self.t_jefe_barra = 0.0

        self.mejoras_opciones: list[str] = []
        self.curado = 0
        self.oferta: list[str] = []
        self.vendidos: set[int] = set()
        self.nivel_tienda = 1
        self.mensaje = ""
        self.t_mensaje = 0.0

        self.transicion = None  # dict(t, fase, accion)
        self.audio.musica("exploracion")

    # ======================================================================
    # Bucle
    # ======================================================================
    def ejecutar(self) -> None:
        while self.ejecutando:
            dt = min(self.reloj.tick(config.FPS) / 1000.0, 0.05)
            self.frame(dt, pygame.event.get())
            pygame.display.flip()
        pygame.quit()

    def frame(self, dt: float, eventos: list) -> None:
        self.t += dt
        self.t_estado += dt
        self.audio.actualizar()
        self._actualizar_transicion(dt)
        for ev in eventos:
            self._manejar_evento(ev)
        if self.estado == "juego":
            self._actualizar_juego(dt)
        self.t_mensaje = max(0.0, self.t_mensaje - dt)
        self._dibujar()

    def cambiar_estado(self, estado: str) -> None:
        self.estado = estado
        self.t_estado = 0.0
        self.seleccion = 0

    def transicionar(self, accion) -> None:
        if self.transicion is None:
            self.transicion = {"t": 0.0, "fase": "cerrar", "accion": accion}

    def _actualizar_transicion(self, dt: float) -> None:
        tr = self.transicion
        if tr is None:
            return
        tr["t"] += dt
        if tr["fase"] == "cerrar" and tr["t"] >= 0.38:
            tr["accion"]()
            tr["fase"], tr["t"] = "abrir", 0.0
        elif tr["fase"] == "abrir" and tr["t"] >= 0.42:
            self.transicion = None

    # ======================================================================
    # Flujo de la run
    # ======================================================================
    def nueva_run(self, semilla: int | None = None) -> None:
        self.run = Run(semilla)
        self._entrar_nivel()

    def _entrar_nivel(self) -> None:
        self.partida = self.run.crear_partida()
        self.efectos.limpiar()
        self.hud.reiniciar(self.partida)
        self.escala_tiempo = 1.0
        self.secuencia = ""
        self.buffer_ataque = self.buffer_dash = 0.0
        self.cambiar_estado("juego")
        n = self.run.nivel
        self.banner = (f"NIVEL {n}" if n != config.NIVEL_JEFE else "NIVEL FINAL", nombre_nivel(n))
        self.t_banner = 0.0
        self.t_jefe_barra = 0.0
        self.audio.musica("jefe" if n == config.NIVEL_JEFE else "exploracion")

    def _nivel_completado(self) -> None:
        self.curado = self.run.completar_nivel()
        self.mejoras_opciones = self.run.opciones_mejora()
        self.cambiar_estado("mejora")
        self.seleccion = 1

    def _elegir_mejora(self, i: int) -> None:
        self.run.elegir_mejora(self.mejoras_opciones[i])
        self.audio.reproducir("ui_ok")
        self.oferta = economia.generar_oferta(self.run.semilla, self.run.nivel)
        self.vendidos = set()
        self.nivel_tienda = economia.nivel_de_tienda(self.run.nivel)
        self.mensaje = ""
        self.cambiar_estado("tienda")

    def _comprar(self, i: int) -> None:
        if i in self.vendidos:
            return
        objeto = self.oferta[i]
        motivo = self.run.comprar_objeto(objeto, self.nivel_tienda)
        if motivo:
            self.audio.reproducir("ui_error")
            self.mensaje = motivo
        else:
            self.audio.reproducir("compra")
            self.mensaje = f"¡{tablas.OBJETOS_TIENDA[objeto]['nombre']} adquirido!"
            if not tablas.OBJETOS_TIENDA[objeto]["consumible"]:
                self.vendidos.add(i)
        self.t_mensaje = 1.6

    def _salir_tienda(self) -> None:
        self.audio.reproducir("ui_ok")

        def siguiente():
            self.run.avanzar_nivel()
            self._entrar_nivel()
        self.transicionar(siguiente)

    def _terminar_run(self, victoria: bool) -> None:
        if victoria:
            self.run.ganar()
        self.puesto = persistencia.insertar_puntaje(self.ranking, self.run.puntaje_total())
        persistencia.guardar_ranking(self.ranking)
        self.cambiar_estado("victoria" if victoria else "derrota")
        self.audio.musica("exploracion" if victoria else "")

    # ======================================================================
    # Entrada
    # ======================================================================
    def _manejar_evento(self, ev) -> None:
        if ev.type == pygame.QUIT:
            self.ejecutando = False
            return
        if ev.type == pygame.WINDOWFOCUSLOST and self.estado == "juego" and not self.secuencia:
            self.cambiar_estado("pausa")
            return
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_m:
                self.audio.alternar_silencio()
                return
            if ev.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                return
        if self.transicion is not None:
            return

        manejador = getattr(self, f"_entrada_{self.estado}")
        manejador(ev)

    def _navegar_lista(self, ev, cantidad: int, horizontal: bool = False) -> int | None:
        """Navegación común con teclado y ratón. Devuelve el índice confirmado o None."""
        menos = TECLAS_IZQ if horizontal else TECLAS_ARRIBA
        mas = TECLAS_DER if horizontal else TECLAS_ABAJO
        if ev.type == pygame.KEYDOWN:
            if ev.key in menos:
                self.seleccion = (self.seleccion - 1) % cantidad
                self.audio.reproducir("ui_mover")
            elif ev.key in mas:
                self.seleccion = (self.seleccion + 1) % cantidad
                self.audio.reproducir("ui_mover")
            elif ev.key in TECLAS_OK:
                return self.seleccion
        elif ev.type == pygame.MOUSEMOTION:
            for rect, accion in self.zonas:
                if isinstance(accion, int) and rect.collidepoint(ev.pos) and accion != self.seleccion:
                    self.seleccion = accion
                    self.audio.reproducir("ui_mover")
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for rect, accion in self.zonas:
                if rect.collidepoint(ev.pos) and isinstance(accion, int):
                    self.seleccion = accion
                    return accion
        return None

    def _entrada_menu(self, ev) -> None:
        elegido = self._navegar_lista(ev, len(pantallas.OPCIONES_MENU))
        if elegido is None:
            return
        self.audio.reproducir("ui_ok")
        if elegido == 0:
            self.transicionar(self.nueva_run)
        elif elegido == 1:
            self.cambiar_estado("ayuda")
        elif elegido == 2:
            self.puesto = -1
            self.cambiar_estado("ranking")
        else:
            self.ejecutando = False

    def _entrada_ayuda(self, ev) -> None:
        volver = (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, *TECLAS_OK)) or (
            ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
            and any(r.collidepoint(ev.pos) for r, _ in self.zonas))
        if volver:
            self.audio.reproducir("ui_ok")
            self.cambiar_estado("menu")

    _entrada_ranking = _entrada_ayuda

    def _entrada_juego(self, ev) -> None:
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_ESCAPE, pygame.K_p):
                if self.secuencia == "":
                    self.audio.reproducir("ui_mover")
                    self.cambiar_estado("pausa")
            elif ev.key == pygame.K_F1:
                self.panel_verificacion = not self.panel_verificacion
            elif ev.key in TECLAS_ATAQUE:
                self.buffer_ataque = BUFFER
                self.apuntar_raton = False
            elif ev.key in TECLAS_DASH:
                self.buffer_dash = BUFFER
            elif ev.key == pygame.K_q:
                self.pulso_pocion = True
            elif ev.key == pygame.K_e:
                self.pulso_bomba = True
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                self.buffer_ataque = BUFFER
                self.apuntar_raton = True
            elif ev.button == 3:
                self.buffer_dash = BUFFER

    def _entrada_pausa(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_p):
            self.cambiar_estado("juego")
            return
        elegido = self._navegar_lista(ev, len(pantallas.OPCIONES_PAUSA))
        if elegido is None:
            return
        self.audio.reproducir("ui_ok")
        if elegido == 0:
            self.cambiar_estado("juego")
        elif elegido == 1:
            self.transicionar(self.nueva_run)
        else:
            self.audio.musica("exploracion")
            self.transicionar(lambda: self.cambiar_estado("menu"))

    def _entrada_mejora(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self._elegir_mejora(ev.key - pygame.K_1)
            return
        if self.t_estado < 0.5:   # evita elegir sin querer al aparecer las cartas
            return
        elegido = self._navegar_lista(ev, len(self.mejoras_opciones), horizontal=True)
        if elegido is not None:
            self._elegir_mejora(elegido)

    def _entrada_tienda(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and pygame.K_1 <= ev.key <= pygame.K_4:
            self._comprar(ev.key - pygame.K_1)
            return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._salir_tienda()
            return
        elegido = self._navegar_lista(ev, len(self.oferta) + 1, horizontal=True)
        if elegido is None:
            return
        if elegido == len(self.oferta):
            self._salir_tienda()
        else:
            self._comprar(elegido)

    def _entrada_fin(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.transicionar(self.nueva_run)
            return
        if self.t_estado < 1.0:
            return
        elegido = self._navegar_lista(ev, len(pantallas.OPCIONES_FIN))
        if elegido == 0:
            self.audio.reproducir("ui_ok")
            self.transicionar(self.nueva_run)
        elif elegido == 1:
            self.audio.reproducir("ui_ok")
            self.audio.musica("exploracion")
            self.transicionar(lambda: self.cambiar_estado("menu"))

    _entrada_derrota = _entrada_fin
    _entrada_victoria = _entrada_fin

    def _entrada_actual(self) -> Entrada:
        teclas = pygame.key.get_pressed()
        mx = (any(teclas[k] for k in TECLAS_DER)) - (any(teclas[k] for k in TECLAS_IZQ))
        my = (any(teclas[k] for k in TECLAS_ABAJO)) - (any(teclas[k] for k in TECLAS_ARRIBA))
        boton_raton = pygame.mouse.get_pressed()[0]
        sostener = any(teclas[k] for k in TECLAS_ATAQUE) or boton_raton
        if boton_raton:
            self.apuntar_raton = True
        apuntar = None
        if self.apuntar_raton:
            px, py = pygame.mouse.get_pos()
            j = self.partida.jugador
            apuntar = (px / E - j.x, py / E - config.MAPA_Y - j.y)
        entrada = Entrada(float(mx), float(my), sostener or self.buffer_ataque > 0, apuntar,
                          self.buffer_dash > 0, self.pulso_pocion, self.pulso_bomba)
        self.pulso_pocion = self.pulso_bomba = False
        return entrada

    # ======================================================================
    # Juego
    # ======================================================================
    def _actualizar_juego(self, dt: float) -> None:
        p = self.partida
        self.efectos.actualizar(dt)
        self.buffer_ataque = max(0.0, self.buffer_ataque - dt)
        self.buffer_dash = max(0.0, self.buffer_dash - dt)
        self.t_banner += dt
        self.t_sonido_moneda = max(0.0, self.t_sonido_moneda - dt)

        entrada = self._entrada_actual()
        if self.efectos.hitstop <= 0:
            dt_juego = dt * self.escala_tiempo
            p.actualizar(dt_juego, entrada)
            if p.jugador.vivo and not p.completada:
                self.run.tiempo += dt_juego
        for ev in p.tomar_eventos():
            self._efecto_de(ev)

        self.escena.actualizar(dt, p)
        self.hud.actualizar(dt, p)
        if p.jefe is not None and p.jefe.estado != "alerta":
            self.t_jefe_barra = min(1.0, self.t_jefe_barra + dt * 1.5)

        j = p.jugador
        if j.vivo and j.vida / j.vida_max <= 0.25:
            self.t_latido -= dt
            if self.t_latido <= 0:
                self.t_latido = 0.95
                self.audio.reproducir("latido", 0.8)

        if self.secuencia:
            self.t_secuencia -= dt
            self.escala_tiempo = min(1.0, self.escala_tiempo + dt * 0.25)
            if self.t_secuencia <= 0 and self.transicion is None:
                victoria = self.secuencia == "victoria"
                self.secuencia = "fin"
                self.transicionar(lambda: self._terminar_run(victoria))

    def _efecto_de(self, ev: Evento) -> None:
        ef, au = self.efectos, self.audio
        j = self.partida.jugador
        tipo = ev.tipo
        if tipo == "tajo":
            ef.tajo(j.x, j.y, ev.valor, j.alcance)
            self.escena.t_tajo = 0.13
            self.buffer_ataque = 0.0
            au.reproducir("tajo", 0.7)
        elif tipo == "golpe_enemigo":
            angulo = math.atan2(ev.y - j.y, ev.x - j.x)
            if ev.critico:
                ef.texto(f"{int(ev.valor)}!", ev.x, ev.y, paleta.ORO, 30)
                ef.chispas(ev.x, ev.y, angulo, paleta.ORO, 12)
                ef.congelar(0.085)
                ef.sacudir(0.32)
                au.reproducir("critico")
            else:
                ef.texto(str(int(ev.valor)), ev.x, ev.y, paleta.TEXTO, 22)
                ef.chispas(ev.x, ev.y, angulo, paleta.BLANCO, 7)
                ef.congelar(0.045)
                ef.sacudir(0.14)
                au.reproducir("golpe", 0.8)
        elif tipo == "esquiva_enemigo":
            ef.texto("esquiva", ev.x, ev.y, paleta.TEXTO_SUAVE, 16)
        elif tipo == "bloqueo":
            ef.texto("bloqueo", ev.x, ev.y, paleta.CIAN, 16)
            ef.chispas(ev.x, ev.y, -math.pi / 2, paleta.CIAN, 6, 1.6)
            au.reproducir("bloqueo")
        elif tipo == "muerte_enemigo":
            cuerpo, detalle = paleta.COLOR_ENEMIGO.get(ev.texto, (paleta.BLANCO, paleta.BLANCO))
            grande = ev.texto == "jefe"
            ef.estallido(ev.x, ev.y, cuerpo, 40 if grande else 16, 140 if grande else 95, 2.6, 0.6)
            ef.estallido(ev.x, ev.y, detalle, 10, 60, 2.0, 0.5)
            ef.onda(ev.x, ev.y, 22, cuerpo)
            ef.sacudir(0.22)
            ef.congelar(0.06)
            au.reproducir("muerte", 0.9)
        elif tipo == "jugador_herido":
            ef.texto(f"-{int(ev.valor)}", ev.x, ev.y, paleta.ROJO, 26)
            ef.estallido(ev.x, ev.y + 8, paleta.ROJO, 10, 80, 2.0, 0.4)
            ef.dano_vineta = 1.0
            ef.destello(paleta.ROJO, 0.35)
            ef.sacudir(0.45)
            ef.congelar(0.08)
            au.reproducir("herido")
        elif tipo == "jugador_esquiva":
            ef.texto("¡esquivado!", ev.x, ev.y, paleta.VERDE, 18)
        elif tipo == "jugador_bloquea":
            ef.texto("¡bloqueado!", ev.x, ev.y, paleta.CIAN, 18)
            au.reproducir("bloqueo")
        elif tipo == "jugador_muere":
            ef.estallido(ev.x, ev.y, paleta.CIAN, 40, 130, 2.6, 0.9)
            ef.sacudir(0.9)
            ef.destello(paleta.ROJO, 0.7)
            self.escala_tiempo = 0.25
            self.secuencia, self.t_secuencia = "derrota", 1.5
            au.musica("")
            au.reproducir("derrota")
        elif tipo == "dash":
            ef.estallido(ev.x, ev.y + 4, paleta.CIAN, 8, 50, 2.0, 0.3)
            self.buffer_dash = 0.0
            au.reproducir("dash", 0.7)
        elif tipo == "moneda":
            ef.estallido(ev.x, ev.y, paleta.ORO, 4, 40, 1.5, 0.25, brillo=True)
            if self.t_sonido_moneda <= 0:
                au.reproducir("moneda", 0.6)
                self.t_sonido_moneda = 0.05
        elif tipo == "pocion":
            ef.texto(f"+{int(ev.valor)}", ev.x, ev.y, paleta.VERDE, 26)
            ef.ascenso(j.x, j.y, paleta.VERDE, 18)
            au.reproducir("pocion")
        elif tipo == "sin_consumible":
            ef.texto(ev.texto, ev.x, ev.y, paleta.TEXTO_SUAVE, 16)
            au.reproducir("ui_error", 0.6)
        elif tipo == "bomba":
            ef.onda(ev.x, ev.y, tablas.RADIO_BOMBA, paleta.NARANJA, 0.45, 4)
            ef.estallido(ev.x, ev.y, paleta.NARANJA, 40, 170, 3.0, 0.6)
            ef.estallido(ev.x, ev.y, paleta.ORO, 20, 120, 2.0, 0.5, brillo=True)
            ef.sacudir(0.65)
            ef.congelar(0.09)
            ef.destello(paleta.NARANJA, 0.45)
            au.reproducir("bomba")
        elif tipo == "flecha":
            au.reproducir("flecha", 0.5)
        elif tipo == "parada":
            ef.chispas(ev.x, ev.y, math.atan2(ev.y - j.y, ev.x - j.x), paleta.BLANCO, 10, 1.2)
            ef.texto("¡parada!", ev.x, ev.y - 6, paleta.CIAN, 16)
            ef.congelar(0.04)
            au.reproducir("parada")
        elif tipo == "proyectil_muro":
            ef.estallido(ev.x, ev.y, paleta.TEXTO_APAGADO, 3, 30, 1.2, 0.2)
        elif tipo == "portal_abierto":
            ef.onda(ev.x, ev.y, 40, paleta.CIAN, 0.7, 3)
            ef.ascenso(ev.x, ev.y, paleta.CIAN, 24)
            self.banner = ("PORTAL ABIERTO", "Ve hacia la luz cian")
            self.t_banner = 0.0
            au.reproducir("portal")
        elif tipo == "nivel_completado":
            au.reproducir("nivel")
            self.transicionar(self._nivel_completado)
        elif tipo == "jefe_fase":
            ef.onda(ev.x, ev.y, 60, paleta.MAGENTA, 0.6, 4)
            ef.sacudir(0.75)
            ef.destello(paleta.MAGENTA, 0.4)
            self.banner = (f"FASE {int(ev.valor)}", "El Guardián se enfurece")
            self.t_banner = 0.0
            au.reproducir("rugido")
        elif tipo == "jefe_telegrafia":
            au.reproducir("alerta", 0.5)
        elif tipo == "jefe_derrotado":
            ef.destello(paleta.BLANCO, 1.0)
            ef.sacudir(1.0)
            ef.estallido(ev.x, ev.y, paleta.ORO, 60, 200, 3.0, 1.2, brillo=True)
            for k in range(3):
                ef.onda(ev.x, ev.y, 50 + k * 30, paleta.ORO, 0.6 + k * 0.2, 3)
            self.escala_tiempo = 0.2
            self.secuencia, self.t_secuencia = "victoria", 2.4
            au.reproducir("rugido")
            au.reproducir("victoria")
        elif tipo == "impacto_muro":
            ef.sacudir(0.35)
            ef.estallido(ev.x, ev.y, paleta.MURO_TOPE_LUZ, 10, 70, 2.2, 0.4)
            au.reproducir("impacto", 0.8)
        elif tipo == "invocar":
            ef.estallido(ev.x, ev.y, paleta.VERDE, 12, 60, 2.0, 0.4)
            ef.onda(ev.x, ev.y, 14, paleta.VERDE)
        elif tipo == "alerta":
            au.reproducir("alerta", 0.35)

    # ======================================================================
    # Dibujo
    # ======================================================================
    def _dibujar(self) -> None:
        s = self.pantalla
        estado = self.estado
        if estado in ("juego", "pausa"):
            self._dibujar_juego()
            if estado == "pausa":
                self.zonas = pantallas.pausa(s, self.t, self.seleccion, self.t_estado, self.run)
        elif estado == "menu":
            mejor = self.ranking[0] if self.ranking else 0
            self.zonas = pantallas.menu(s, self.t, self.seleccion, self.t_estado, mejor)
        elif estado == "ayuda":
            self.zonas = pantallas.ayuda(s, self.t, self.t_estado)
        elif estado == "ranking":
            self.zonas = pantallas.ranking(s, self.t, self.t_estado, self.ranking, self.puesto)
        elif estado == "mejora":
            self.zonas = pantallas.mejoras(s, self.t, self.seleccion, self.t_estado, self.mejoras_opciones,
                                           self.run.nivel, self.curado)
        elif estado == "tienda":
            self.zonas = pantallas.tienda(s, self.t, self.seleccion, self.t_estado, self.run, self.oferta,
                                          self.vendidos, self.nivel_tienda, self.mensaje, self.t_mensaje)
        elif estado == "derrota":
            self.zonas = pantallas.derrota(s, self.t, self.seleccion, self.t_estado, self.run, self.puesto)
        elif estado == "victoria":
            self.zonas = pantallas.victoria(s, self.t, self.seleccion, self.t_estado, self.run, self.puesto)
        self._dibujar_transicion()

    def _dibujar_juego(self) -> None:
        s, p, ef = self.pantalla, self.partida, self.efectos
        lienzo = self.lienzo
        lienzo.fill(paleta.NOCHE)
        mundo = self.escena.dibujar(p, self.t)
        ox, oy = ef.offset if self.estado == "juego" else (0, 0)
        lienzo.blit(mundo, (ox, config.MAPA_Y + oy))

        # Capas de postproceso en baja resolución (más baratas que a 1280x720).
        lienzo.blit(self.vineta_negra, (0, 0))
        j = p.jugador
        rojo = ef.dano_vineta
        if j.vivo and j.vida / j.vida_max <= 0.25:
            rojo = max(rojo, 0.35 + 0.25 * math.sin(self.t * 6.5))
        if rojo > 0:
            self.vineta_roja.set_alpha(int(255 * min(1.0, rojo)))
            lienzo.blit(self.vineta_roja, (0, 0))
        if ef.flash > 0:
            self.capa_flash.fill(ef.flash_color)
            self.capa_flash.set_alpha(int(110 * ef.flash))
            lienzo.blit(self.capa_flash, (0, 0))
        self._dibujar_franja_banner()
        pygame.transform.scale(lienzo, (W, H), s)

        ef.dibujar_textos(s, ox, config.MAPA_Y + oy)
        self.hud.dibujar(s, p, self.t)
        self.hud.dibujar_jefe(s, p, self.t, ease_out_cubic(self.t_jefe_barra))
        self._dibujar_banner()
        if self.panel_verificacion:
            pantallas.panel_verificacion(s)

    def _alfa_banner(self) -> tuple[float, float]:
        t = self.t_banner
        entrada = ease_out_cubic(t / 0.45)
        salida = 1 - ease_out_cubic((t - 2.0) / 0.6) if t > 2.0 else 1.0
        return entrada, salida

    def _dibujar_franja_banner(self) -> None:
        if self.banner is None or self.t_banner > 2.6:
            return
        entrada, salida = self._alfa_banner()
        franja = pygame.Surface((config.ANCHO_LIENZO, 55))
        franja.fill(paleta.NOCHE)
        franja.set_alpha(int(150 * min(entrada, salida)))
        self.lienzo.blit(franja, (0, 115))

    def _dibujar_banner(self) -> None:
        if self.banner is None or self.t_banner > 2.6:
            return
        entrada, salida = self._alfa_banner()
        alfa = int(255 * min(entrada, salida))
        x = W / 2 + (1 - entrada) * -300 + (1 - salida) * 300
        titulo, sub = self.banner
        textos.dibujar(self.pantalla, titulo, x, 268, 46, paleta.ORO, True, "center", 3, alfa)
        textos.dibujar(self.pantalla, sub, x, 312, 22, paleta.TEXTO_SUAVE, False, "center", 2, alfa)

    def _dibujar_transicion(self) -> None:
        tr = self.transicion
        if tr is None:
            return
        k = ease_in_out(tr["t"] / 0.38) if tr["fase"] == "cerrar" else 1 - ease_in_out(tr["t"] / 0.42)
        if self.partida is not None and self.estado in ("juego", "pausa"):
            cx = self.partida.jugador.x * E
            cy = (self.partida.jugador.y + config.MAPA_Y) * E
        else:
            cx, cy = W / 2, H / 2
        radio_max = math.hypot(W, H)
        radio = int(radio_max * (1 - k))
        capa = pygame.Surface((W, H))
        capa.fill(paleta.NOCHE)
        capa.set_colorkey((255, 0, 255))
        if radio > 0:
            pygame.draw.circle(capa, (255, 0, 255), (int(cx), int(cy)), radio)
        self.pantalla.blit(capa, (0, 0))
