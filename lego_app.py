# ============================================================
# TAB 2: ADMINISTRAR CATÁLOGO
# ============================================================
with tab2:
    accion = st.radio("Acción", ["Alta", "Baja", "Actualización"], horizontal=True)
    st.divider()

    set_number = st.text_input("Número de set")
    name = st.text_input("Nombre")
    theme = st.selectbox("Tema", ["Star Wars", "Technic", "Ideas", "F1"])
    year = st.number_input("Año", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("Piezas", min_value=0, step=10)
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", min_value=0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])
    image_url = st.text_input("URL imagen", placeholder="https://drive.google.com/...")
    lego_web_url = st.text_input("URL página LEGO (opcional)", placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (formato: nombre|número por línea)")
    tags = st.text_area("Tags (separados por comas)", placeholder="nave, star wars, exclusivo")

    if st.button("Enviar"):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]

            # 🔹 Dividir minifigs en dos listas separadas
            minifig_names = []
            minifigs_numbers = []
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split("|")]
                if len(p) == 2:
                    minifig_names.append(p[0])
                    minifigs_numbers.append(p[1])

            tags_list = [t.strip() for t in tags.split(",") if t.strip()]

            payload = {"accion": accion.lower()}

            if accion == "Alta":
                payload["lego"] = {
                    "set_number": set_number_int,
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "image_url": convertir_enlace_drive(image_url),
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifig_names": minifig_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                }

            elif accion == "Baja":
                payload["set_number"] = set_number_int

            else:  # Actualización
                campos = {
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "image_url": convertir_enlace_drive(image_url),
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifig_names": minifig_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                }
                # Eliminar campos vacíos o sin cambios
                campos_filtrados = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}
                payload["set_number"] = set_number_int
                payload["campos"] = campos_filtrados

            # 🔹 Enviar solicitud a Lambda
            r = requests.post(LAMBDA_ADMIN, json=payload, timeout=30)
            if r.status_code == 200:
                st.success(r.json().get("mensaje", "Operación completada."))
            else:
                st.error(f"Error {r.status_code}: {r.text}")

        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")
