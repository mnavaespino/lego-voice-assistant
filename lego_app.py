# ============================================================
# TAB 1: BUSCAR EN CATÁLOGO
# ============================================================
with tab1:
    # Creamos una función interna que ejecuta la búsqueda
    def ejecutar_busqueda():
        if not st.session_state.pregunta.strip():
            st.warning("Escribe una pregunta.")
            return

        with st.spinner("Buscando..."):
            try:
                resp = requests.post(LAMBDA_SEARCH, json={"pregunta": st.session_state.pregunta}, timeout=40)
                if resp.status_code != 200:
                    st.error(f"Error {resp.status_code}: {resp.text}")
                else:
                    data = resp.json()
                    body = data.get("body")
                    if isinstance(body, str):
                        data = json.loads(body)

                    respuesta = re.sub(r"!\[.*?\]\(\s*\)", "", data.get("respuesta", ""))
                    st.markdown(f"**{respuesta}**")

                    resultados = data.get("resultados", [])
                    for item in resultados:
                        nombre = item.get("name", "Sin nombre")
                        set_number = item.get("set_number", "")
                        year = item.get("year", "")
                        theme = item.get("theme", "")
                        piezas = item.get("pieces", "")
                        storage = item.get("storage", "")
                        storage_box = item.get("storage_box", "")
                        condition = item.get("condition", "")
                        image_url = convertir_enlace_drive(item.get("image_url", ""))
                        manuals = item.get("manuals", [])
                        minifig_names = item.get("minifig_names", [])
                        minifigs_numbers = item.get("minifigs_numbers", [])
                        lego_web_url = item.get("lego_web_url", "")

                        with st.container(border=True):
                            st.markdown(f"### {set_number} · {nombre}")
                            st.caption(f"{theme} · {year}")

                            linea_detalle = f"🧩 {piezas} piezas · 🏠 {storage}"
                            if storage_box and int(storage_box) != 0:
                                linea_detalle += f" · 📦 Caja {storage_box}"
                            linea_detalle += f" · 🎁 {condition}"
                            st.caption(linea_detalle)

                            if image_url:
                                st.markdown(f"[🖼️ Imagen del set]({image_url})")
                            if lego_web_url:
                                st.markdown(f"[🌐 Página oficial LEGO]({lego_web_url})")

                            if manuals:
                                links = [f"[{i+1} · Ver]({m})" for i, m in enumerate(manuals)]
                                st.markdown("**📘 Manuales:** " + " · ".join(links))

                            if minifig_names and minifigs_numbers:
                                figs = ", ".join(
                                    [f"{n} ({num})" for n, num in zip(minifig_names, minifigs_numbers)]
                                )
                                st.markdown(f"**🧍 Minifigs:** {figs}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Campo de texto con ENTER automático
    st.text_input(
        "🔍 Pregunta",
        placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?",
        key="pregunta",
        on_change=ejecutar_busqueda,
    )

    # Botón adicional (por si el usuario prefiere clic)
    st.button("Buscar", on_click=ejecutar_busqueda)
