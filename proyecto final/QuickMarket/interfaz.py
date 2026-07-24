"""Interfaz gráfica de QuickMarket desarrollada con Tkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from config import CONSUMIDOR_FINAL_ID
from dashboard import Dashboard
from gestor_csv import GestorCSV
from sistema_ventas import SistemaVentas


class CampoBusqueda(ttk.Frame):
    """Campo de texto con autocompletado para buscar por nombre.

    Reemplaza a un combobox: el usuario escribe parte del nombre y la
    lista de abajo se filtra en vivo. Internamente se guarda el ID
    correspondiente (producto o cliente), pero en pantalla solo se
    muestra el nombre.
    """

    def __init__(self, padre, ancho: int = 30, alto_lista: int = 4, on_seleccion=None):
        super().__init__(padre)
        self.on_seleccion = on_seleccion
        self._items: list[tuple[str, str]] = []  # (id, nombre)
        self._coincidencias: list[tuple[str, str]] = []
        self.id_seleccionado: str | None = None

        self.variable = tk.StringVar()
        self.entrada = ttk.Entry(self, textvariable=self.variable, width=ancho)
        self.entrada.pack(fill="x")

        marco_lista = ttk.Frame(self)
        marco_lista.pack(fill="x")
        self.lista = tk.Listbox(
            marco_lista, height=alto_lista, exportselection=False,
            relief="solid", borderwidth=1,
        )
        barra = ttk.Scrollbar(marco_lista, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.variable.trace_add("write", lambda *_: self._filtrar())
        self.entrada.bind("<FocusIn>", lambda _e: self._filtrar())
        self.entrada.bind("<Down>", self._ir_a_lista)
        self.entrada.bind("<Return>", self._seleccionar_primero)
        self.lista.bind("<<ListboxSelect>>", self._al_seleccionar)
        self.lista.bind("<Return>", self._al_seleccionar)

    def establecer_items(self, items: list[tuple[str, str]]) -> None:
        """items: lista de tuplas (id, nombre)."""
        anterior = self.id_seleccionado
        self._items = items
        if anterior and not any(i == anterior for i, _ in items):
            self.id_seleccionado = None
        self._filtrar()

    def obtener_id(self) -> str | None:
        return self.id_seleccionado

    def seleccionar_id(self, id_valor: str) -> bool:
        for identificador, nombre in self._items:
            if identificador == id_valor:
                self._asignar((identificador, nombre))
                return True
        return False

    def limpiar(self) -> None:
        self.variable.set("")
        self.id_seleccionado = None
        self._filtrar()

    def _filtrar(self) -> None:
        texto = self.variable.get().strip().lower()
        if texto:
            self._coincidencias = [(i, n) for i, n in self._items if texto in n.lower()]
        else:
            self._coincidencias = list(self._items)
        self.lista.delete(0, "end")
        for _identificador, nombre in self._coincidencias[:50]:
            self.lista.insert("end", nombre)
        if self.id_seleccionado:
            nombre_actual = next((n for i, n in self._items if i == self.id_seleccionado), None)
            if nombre_actual != self.variable.get():
                self.id_seleccionado = None

    def _ir_a_lista(self, _evento=None) -> None:
        if self.lista.size():
            self.lista.focus_set()
            self.lista.selection_clear(0, "end")
            self.lista.selection_set(0)
            self.lista.activate(0)

    def _seleccionar_primero(self, _evento=None) -> None:
        if self._coincidencias:
            self._asignar(self._coincidencias[0])

    def _al_seleccionar(self, _evento=None) -> None:
        seleccion = self.lista.curselection()
        if not seleccion:
            return
        indice = seleccion[0]
        if indice < len(self._coincidencias):
            self._asignar(self._coincidencias[indice])

    def _asignar(self, item: tuple[str, str]) -> None:
        identificador, nombre = item
        self.id_seleccionado = identificador
        self.variable.set(nombre)
        self.entrada.icursor("end")
        if self.on_seleccion:
            self.on_seleccion()


class InterfazQuickMarket:
    def __init__(self, gestor: GestorCSV, sistema: SistemaVentas):
        self.gestor = gestor
        self.sistema = sistema
        self.dashboard = Dashboard(gestor)
        self.ventana = tk.Tk()
        self.ventana.title("QuickMarket - Sistema integrado")
        self.ventana.geometry("1180x820")
        self.ventana.minsize(1050, 720)
        self.carrito: list[tuple[str, int]] = []
        self.canvas_dashboard = None
        self._crear_estilos()
        self._crear_pestanas()
        self.refrescar_todo()

    def iniciar(self) -> None:
        self.ventana.mainloop()

    def _crear_estilos(self) -> None:
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Titulo.TLabel", font=("Arial", 20, "bold"), foreground="#1f2937")
        estilo.configure("KPI.TLabel", font=("Arial", 13, "bold"), padding=8)
        estilo.configure("Accion.TButton", font=("Arial", 11, "bold"), padding=8)
        # Tarjetas de colores para los KPI del dashboard.
        for nombre_estilo, fondo, texto in [
            ("KPI1.TLabel", "#e7f0fd", "#1d4ed8"),
            ("KPI2.TLabel", "#e9f9ef", "#15803d"),
            ("KPI3.TLabel", "#fdf3e2", "#b45309"),
            ("KPI4.TLabel", "#fdeaea", "#b91c1c"),
        ]:
            estilo.configure(
                nombre_estilo, font=("Arial", 13, "bold"), padding=12,
                background=fondo, foreground=texto, relief="flat",
            )

    def _crear_pestanas(self) -> None:
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_inicio = ttk.Frame(self.notebook)
        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_clientes = ttk.Frame(self.notebook)
        self.tab_productos = ttk.Frame(self.notebook)
        self.tab_erp = ttk.Frame(self.notebook)
        self.tab_scm = ttk.Frame(self.notebook)
        self.tab_dashboard = ttk.Frame(self.notebook)
        for tab, nombre in [
            (self.tab_inicio, "Inicio"),
            (self.tab_ventas, "Ventas POS"),
            (self.tab_clientes, "Clientes"),
            (self.tab_productos, "Productos e inventario"),
            (self.tab_erp, "ERP financiero"),
            (self.tab_scm, "SCM / Órdenes"),
            (self.tab_dashboard, "Dashboard"),
        ]:
            self.notebook.add(tab, text=nombre)
        self._crear_inicio()
        self._crear_ventas()
        self._crear_clientes()
        self._crear_productos()
        self._crear_erp()
        self._crear_scm()
        self._crear_dashboard()

    def _crear_inicio(self) -> None:
        ttk.Label(self.tab_inicio, text="QUICKMARKET", style="Titulo.TLabel").pack(pady=(80, 10))
        ttk.Label(
            self.tab_inicio,
            text="Sistema integrado de ventas, inventario, finanzas y análisis de clientes",
            font=("Arial", 12),
        ).pack(pady=10)
        marco = ttk.Frame(self.tab_inicio)
        marco.pack(pady=30)
        botones = [
            ("Registrar venta", 1), ("Clientes", 2), ("Productos", 3),
            ("Módulo ERP", 4), ("Órdenes SCM", 5), ("Dashboard", 6),
        ]
        for texto, indice in botones:
            ttk.Button(
                marco, text=texto, style="Accion.TButton",
                command=lambda i=indice: self.notebook.select(i), width=24,
            ).pack(pady=6)

    def _crear_ventas(self) -> None:
        ttk.Label(self.tab_ventas, text="Registro de ventas POS", style="Titulo.TLabel").pack(pady=10)
        formulario = ttk.LabelFrame(self.tab_ventas, text="Datos de la venta")
        formulario.pack(fill="x", padx=15, pady=8)

        ttk.Label(formulario, text="Cliente:").grid(row=0, column=0, padx=8, pady=8, sticky="ne")
        self.buscador_cliente = CampoBusqueda(formulario, ancho=30)
        self.buscador_cliente.grid(row=0, column=1, padx=8, pady=8, sticky="nw")
        ttk.Label(formulario, text="Método de pago:").grid(row=0, column=2, padx=8, pady=8, sticky="ne")
        self.combo_pago = ttk.Combobox(
            formulario, state="readonly", values=self.sistema.METODOS_PAGO, width=24
        )
        self.combo_pago.grid(row=0, column=3, padx=8, pady=8, sticky="nw")
        self.combo_pago.set("Efectivo")

        ttk.Label(formulario, text="Producto:").grid(row=1, column=0, padx=8, pady=8, sticky="ne")
        self.buscador_producto = CampoBusqueda(formulario, ancho=30, on_seleccion=self._mostrar_stock)
        self.buscador_producto.grid(row=1, column=1, padx=8, pady=8, sticky="nw")
        ttk.Label(formulario, text="Cantidad:").grid(row=1, column=2, padx=8, pady=8, sticky="ne")
        self.entrada_cantidad = ttk.Entry(formulario, width=10)
        self.entrada_cantidad.grid(row=1, column=3, padx=8, pady=8, sticky="nw")
        self.entrada_cantidad.insert(0, "1")
        self.etiqueta_stock = ttk.Label(formulario, text="Stock disponible: -")
        self.etiqueta_stock.grid(row=2, column=1, padx=8, pady=5, sticky="w")
        ttk.Button(formulario, text="Agregar producto", command=self._agregar_carrito).grid(
            row=2, column=3, padx=8, pady=8, sticky="w"
        )
        ttk.Label(
            formulario,
            text="Escriba el nombre del cliente o del producto para buscarlo en la lista.",
            foreground="#6b7280", font=("Arial", 9, "italic"),
        ).grid(row=3, column=0, columnspan=4, padx=8, pady=(0, 6), sticky="w")

        # La barra inferior (Total / Confirmar venta) se ancla al fondo ANTES
        # de empacar la tabla del carrito, para que siempre quede visible sin
        # importar cuánto crezca el contenido de arriba.
        pie = ttk.Frame(self.tab_ventas)
        pie.pack(side="bottom", fill="x", padx=15, pady=8)
        ttk.Button(pie, text="Eliminar seleccionado", command=self._eliminar_carrito).pack(side="left")
        self.etiqueta_total = ttk.Label(pie, text="Total: $0.00", style="KPI.TLabel")
        self.etiqueta_total.pack(side="right", padx=10)
        ttk.Button(
            pie, text="CONFIRMAR VENTA", style="Accion.TButton", command=self._confirmar_venta
        ).pack(side="right", padx=10)

        columnas = ("producto", "cantidad", "precio", "subtotal")
        self.tabla_carrito = ttk.Treeview(self.tab_ventas, columns=columnas, show="headings", height=10)
        for columna, titulo, ancho in [
            ("producto", "Producto", 330), ("cantidad", "Cantidad", 100),
            ("precio", "Precio", 120), ("subtotal", "Subtotal", 120),
        ]:
            self.tabla_carrito.heading(columna, text=titulo)
            self.tabla_carrito.column(columna, width=ancho, anchor="center")
        self.tabla_carrito.pack(fill="both", expand=True, padx=15, pady=8)

    def _crear_clientes(self) -> None:
        ttk.Label(self.tab_clientes, text="Gestión de clientes", style="Titulo.TLabel").pack(pady=10)
        formulario = ttk.LabelFrame(self.tab_clientes, text="Nuevo cliente")
        formulario.pack(fill="x", padx=15, pady=8)
        ttk.Label(formulario, text="Nombre:").grid(row=0, column=0, padx=6, pady=8)
        self.cliente_nombre = ttk.Entry(formulario, width=28)
        self.cliente_nombre.grid(row=0, column=1, padx=6, pady=8)
        ttk.Label(formulario, text="Género:").grid(row=0, column=2, padx=6, pady=8)
        self.cliente_genero = ttk.Combobox(
            formulario, values=["Femenino", "Masculino", "No especificado"], state="readonly"
        )
        self.cliente_genero.grid(row=0, column=3, padx=6, pady=8)
        self.cliente_genero.set("No especificado")
        ttk.Label(formulario, text="Tipo:").grid(row=0, column=4, padx=6, pady=8)
        self.cliente_tipo = ttk.Combobox(
            formulario, values=["Normal", "Miembro"], state="readonly", width=12
        )
        self.cliente_tipo.grid(row=0, column=5, padx=6, pady=8)
        self.cliente_tipo.set("Normal")
        ttk.Button(formulario, text="Guardar cliente", command=self._guardar_cliente).grid(
            row=0, column=6, padx=12, pady=8
        )
        self.tabla_clientes = self._crear_tabla(
            self.tab_clientes,
            [("nombre", "Nombre", 260), ("tipo", "Tipo", 120), ("genero", "Género", 150),
             ("fecha", "Registro", 130), ("id", "Código interno", 110)],
        )

    def _crear_productos(self) -> None:
        ttk.Label(self.tab_productos, text="Productos e inventario", style="Titulo.TLabel").pack(pady=8)
        formulario = ttk.LabelFrame(self.tab_productos, text="Nuevo producto")
        formulario.pack(fill="x", padx=12, pady=5)
        campos = [
            ("Nombre", "producto_nombre"), ("Categoría", "producto_categoria"),
            ("Precio", "producto_precio"), ("Costo", "producto_costo"),
            ("Stock", "producto_stock"), ("Stock mínimo", "producto_minimo"),
        ]
        for i, (texto, atributo) in enumerate(campos):
            ttk.Label(formulario, text=f"{texto}:").grid(row=i // 3, column=(i % 3) * 2, padx=5, pady=6)
            entrada = ttk.Entry(formulario, width=20)
            entrada.grid(row=i // 3, column=(i % 3) * 2 + 1, padx=5, pady=6)
            setattr(self, atributo, entrada)
        ttk.Label(formulario, text="Proveedor:").grid(row=2, column=0, padx=5, pady=6)
        self.combo_proveedor = ttk.Combobox(formulario, state="readonly", width=28)
        self.combo_proveedor.grid(row=2, column=1, padx=5, pady=6)
        ttk.Button(formulario, text="Guardar producto", command=self._guardar_producto).grid(
            row=2, column=4, columnspan=2, padx=8, pady=6
        )
        self.tabla_productos = self._crear_tabla(
            self.tab_productos,
            [("id", "ID", 70), ("nombre", "Producto", 230), ("categoria", "Categoría", 200),
             ("precio", "Precio", 90), ("stock", "Stock", 80), ("minimo", "Mínimo", 80),
             ("estado", "Estado", 110)],
        )

    def _crear_erp(self) -> None:
        ttk.Label(self.tab_erp, text="Módulo financiero ERP", style="Titulo.TLabel").pack(pady=10)
        self.etiqueta_ingresos = ttk.Label(self.tab_erp, text="Ingresos: $0.00", style="KPI.TLabel")
        self.etiqueta_ingresos.pack()
        ttk.Button(self.tab_erp, text="Actualizar", command=self._refrescar_erp).pack(pady=5)
        self.tabla_erp = self._crear_tabla(
            self.tab_erp,
            [("id", "Código", 100), ("fecha", "Fecha", 170), ("tipo", "Tipo", 100),
             ("concepto", "Concepto", 240), ("monto", "Monto", 110), ("venta", "Venta", 100)],
        )

    def _crear_scm(self) -> None:
        ttk.Label(self.tab_scm, text="Órdenes de compra SCM", style="Titulo.TLabel").pack(pady=10)
        acciones = ttk.Frame(self.tab_scm)
        acciones.pack(fill="x", padx=15)
        ttk.Button(acciones, text="Actualizar", command=self._refrescar_scm).pack(side="left", padx=5)
        ttk.Button(acciones, text="Marcar como recibida", command=self._recibir_orden).pack(side="left", padx=5)
        self.tabla_scm = self._crear_tabla(
            self.tab_scm,
            [("id", "Orden", 90), ("fecha", "Fecha", 150), ("producto", "Producto agotado", 220),
             ("proveedor", "Proveedor", 150), ("estado", "Estado", 110), ("total", "Total estimado", 130)],
        )

    def _crear_dashboard(self) -> None:
        ttk.Label(self.tab_dashboard, text="Dashboard gerencial", style="Titulo.TLabel").pack(pady=5)
        self.marco_kpis = ttk.Frame(self.tab_dashboard)
        self.marco_kpis.pack(fill="x", padx=10)
        self.etiquetas_kpi = []
        for estilo_kpi in ("KPI1.TLabel", "KPI2.TLabel", "KPI3.TLabel", "KPI4.TLabel"):
            etiqueta = ttk.Label(self.marco_kpis, style=estilo_kpi, anchor="center", justify="center")
            etiqueta.pack(side="left", expand=True, fill="x", padx=6)
            self.etiquetas_kpi.append(etiqueta)
        ttk.Button(self.tab_dashboard, text="Actualizar dashboard", command=self._refrescar_dashboard).pack(pady=4)
        self.marco_graficos = ttk.Frame(self.tab_dashboard)
        self.marco_graficos.pack(fill="both", expand=True, padx=8, pady=5)
        self.canvas_dashboard = tk.Canvas(
            self.marco_graficos, background="white", highlightthickness=0
        )
        self.canvas_dashboard.pack(fill="both", expand=True)
        self.canvas_dashboard.bind(
            "<Configure>", lambda _evento: self.dashboard.dibujar_en_canvas(self.canvas_dashboard)
        )

    def _crear_tabla(self, padre, columnas):
        tabla = ttk.Treeview(padre, columns=[c[0] for c in columnas], show="headings")
        for codigo, titulo, ancho in columnas:
            tabla.heading(codigo, text=titulo)
            tabla.column(codigo, width=ancho, anchor="center")
        tabla.pack(fill="both", expand=True, padx=15, pady=10)
        return tabla

    def refrescar_todo(self) -> None:
        self._refrescar_listas()
        self._refrescar_clientes()
        self._refrescar_productos()
        self._refrescar_erp()
        self._refrescar_scm()
        self._refrescar_dashboard()

    def _refrescar_listas(self) -> None:
        clientes = self.sistema.listar_clientes()
        productos = self.sistema.listar_productos()
        proveedores = self.sistema.listar_proveedores()
        self.buscador_cliente.establecer_items([(c.id_cliente, c.nombre) for c in clientes])
        self.buscador_producto.establecer_items([(p.id_producto, p.nombre) for p in productos])
        self.combo_proveedor["values"] = [f"{p.id_proveedor} - {p.nombre}" for p in proveedores]
        if not self.buscador_cliente.obtener_id() and clientes:
            if not self.buscador_cliente.seleccionar_id(CONSUMIDOR_FINAL_ID):
                self.buscador_cliente.seleccionar_id(clientes[0].id_cliente)
        if not self.buscador_producto.obtener_id() and productos:
            self.buscador_producto.seleccionar_id(productos[0].id_producto)
        if proveedores and not self.combo_proveedor.get():
            self.combo_proveedor.current(0)
        self._mostrar_stock()

    def _mostrar_stock(self) -> None:
        id_producto = self.buscador_producto.obtener_id()
        if not id_producto:
            self.etiqueta_stock.config(text="Stock disponible: -")
            return
        producto = next((p for p in self.sistema.listar_productos() if p.id_producto == id_producto), None)
        if producto:
            self.etiqueta_stock.config(
                text=f"Precio: ${producto.precio_venta:.2f} | Stock disponible: {producto.stock_actual}"
            )

    def _agregar_carrito(self) -> None:
        try:
            id_producto = self.buscador_producto.obtener_id()
            if not id_producto:
                raise ValueError("Busque y seleccione un producto de la lista.")
            cantidad = int(self.entrada_cantidad.get())
            producto = next(p for p in self.sistema.listar_productos() if p.id_producto == id_producto)
            acumulada = sum(c for pid, c in self.carrito if pid == id_producto) + cantidad
            if cantidad <= 0 or acumulada > producto.stock_actual:
                raise ValueError(f"Cantidad inválida. Stock disponible: {producto.stock_actual}.")
            self.carrito.append((id_producto, cantidad))
            self._refrescar_carrito()
        except (ValueError, StopIteration) as error:
            messagebox.showerror("Producto", str(error))

    def _refrescar_carrito(self) -> None:
        for item in self.tabla_carrito.get_children(): self.tabla_carrito.delete(item)
        productos = {p.id_producto: p for p in self.sistema.listar_productos()}
        total_subtotal = 0.0
        for indice, (id_producto, cantidad) in enumerate(self.carrito):
            producto = productos[id_producto]
            subtotal = producto.precio_venta * cantidad
            total_subtotal += subtotal
            self.tabla_carrito.insert(
                "", "end", iid=str(indice),
                values=(producto.nombre, cantidad, f"${producto.precio_venta:.2f}", f"${subtotal:.2f}")
            )
        total = total_subtotal * 1.05
        self.etiqueta_total.config(text=f"Total: ${total:.2f}")

    def _eliminar_carrito(self) -> None:
        seleccion = self.tabla_carrito.selection()
        if seleccion:
            self.carrito.pop(int(seleccion[0]))
            self._refrescar_carrito()

    def _confirmar_venta(self) -> None:
        try:
            id_cliente = self.buscador_cliente.obtener_id()
            if not id_cliente:
                raise ValueError("Busque y seleccione un cliente de la lista.")
            if not self.carrito:
                raise ValueError("Agregue al menos un producto al carrito.")
            if not messagebox.askyesno("Confirmar", "¿Registrar esta venta?"):
                return
            venta, ordenes = self.sistema.registrar_venta(
                id_cliente, self.combo_pago.get(), self.carrito
            )
            mensaje = f"Venta {venta.id_venta} registrada.\nTotal: ${venta.total:.2f}"
            if ordenes:
                mensaje += f"\nSe generaron {len(ordenes)} órdenes de compra."
            messagebox.showinfo("Venta completada", mensaje)
            self.carrito.clear()
            self._refrescar_carrito()
            self.refrescar_todo()
        except Exception as error:
            messagebox.showerror("No se pudo registrar", str(error))

    def _guardar_cliente(self) -> None:
        try:
            cliente = self.sistema.registrar_cliente(
                self.cliente_nombre.get(), self.cliente_genero.get(), self.cliente_tipo.get()
            )
            messagebox.showinfo("Cliente", f"Cliente {cliente.id_cliente} guardado.")
            self.cliente_nombre.delete(0, "end")
            self.refrescar_todo()
        except Exception as error:
            messagebox.showerror("Cliente", str(error))

    def _guardar_producto(self) -> None:
        try:
            id_proveedor = self.combo_proveedor.get().split(" - ", 1)[0]
            producto = self.sistema.registrar_producto(
                self.producto_nombre.get(), self.producto_categoria.get(),
                float(self.producto_precio.get()), float(self.producto_costo.get()),
                int(self.producto_stock.get()), int(self.producto_minimo.get()), id_proveedor,
            )
            messagebox.showinfo("Producto", f"Producto {producto.id_producto} guardado.")
            for atributo in ["producto_nombre", "producto_categoria", "producto_precio", "producto_costo", "producto_stock", "producto_minimo"]:
                getattr(self, atributo).delete(0, "end")
            self.refrescar_todo()
        except Exception as error:
            messagebox.showerror("Producto", str(error))

    def _refrescar_clientes(self) -> None:
        for item in self.tabla_clientes.get_children(): self.tabla_clientes.delete(item)
        clientes_ordenados = sorted(self.sistema.listar_clientes(), key=lambda c: c.nombre.lower())
        for c in clientes_ordenados:
            self.tabla_clientes.insert(
                "", "end",
                values=(c.nombre, c.tipo_cliente, c.genero, c.fecha_registro, c.id_cliente),
            )

    def _refrescar_productos(self) -> None:
        for item in self.tabla_productos.get_children(): self.tabla_productos.delete(item)
        for p in self.sistema.listar_productos():
            estado = "Agotado" if p.stock_actual == 0 else ("Stock bajo" if p.verificar_stock_bajo() else "Normal")
            self.tabla_productos.insert("", "end", values=(p.id_producto, p.nombre, p.categoria, f"${p.precio_venta:.2f}", p.stock_actual, p.stock_minimo, estado))

    def _refrescar_erp(self) -> None:
        for item in self.tabla_erp.get_children(): self.tabla_erp.delete(item)
        movimientos = self.sistema.modulo_erp.consultar_movimientos()[-200:]
        for m in reversed(movimientos):
            self.tabla_erp.insert("", "end", values=(m["id_movimiento"], m["fecha"], m["tipo"], m["concepto"], f"${float(m['monto']):.2f}", m["id_venta"]))
        self.etiqueta_ingresos.config(text=f"Ingresos acumulados: ${self.sistema.modulo_erp.calcular_ingresos_totales():,.2f}")

    def _refrescar_scm(self) -> None:
        for item in self.tabla_scm.get_children(): self.tabla_scm.delete(item)
        proveedores = {p.id_proveedor: p.nombre for p in self.sistema.listar_proveedores()}
        for o in reversed(self.sistema.modulo_scm.consultar_ordenes_detalladas()):
            nombre_proveedor = proveedores.get(o["id_proveedor"], o["id_proveedor"])
            self.tabla_scm.insert(
                "", "end", iid=o["id_orden"],
                values=(
                    o["id_orden"], o["fecha"], o["productos"], nombre_proveedor,
                    o["estado"], f"${float(o['total_estimado']):.2f}",
                ),
            )

    def _recibir_orden(self) -> None:
        seleccion = self.tabla_scm.selection()
        if not seleccion:
            messagebox.showwarning("Orden", "Seleccione una orden.")
            return
        try:
            self.sistema.modulo_scm.marcar_orden_recibida(seleccion[0])
            messagebox.showinfo("Orden", "Orden recibida e inventario actualizado.")
            self.refrescar_todo()
        except Exception as error:
            messagebox.showerror("Orden", str(error))

    def _refrescar_dashboard(self) -> None:
        kpis = self.dashboard.calcular_kpis()
        textos = [
            f"Ventas totales\n${kpis['ventas_totales']:,.2f}",
            f"Transacciones\n{kpis['numero_ventas']}",
            f"Ticket promedio\n${kpis['ticket_promedio']:,.2f}",
            f"Stock bajo\n{kpis['stock_bajo']}",
        ]
        for etiqueta, texto in zip(self.etiquetas_kpi, textos): etiqueta.config(text=texto)
        if self.canvas_dashboard:
            self.dashboard.dibujar_en_canvas(self.canvas_dashboard)
