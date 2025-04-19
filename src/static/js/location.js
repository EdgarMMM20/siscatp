/**
 * Inicializa los selects de países en los contenedores especificados.
 * @param {string|null} tabId - ID del contenedor (pestaña) a inicializar, o null para todos.
 */
function initSelects(tabId = null) {
    const containers = tabId ? [document.getElementById(tabId)] : [
        document.getElementById('datos-personales'),
        document.getElementById('datos-compania')
    ];

    containers.forEach(container => {
        if (!container) return;

        const paisesSelect = container.querySelector('select[name="paises"]');

        if (paisesSelect) {
            fetch("/get-paises", { method: "GET" })
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Error al cargar países: " + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Países cargados para", container.id, ":", data);
                    paisesSelect.innerHTML = '<option value="" selected>Selecciona el país</option>';

                    if (data && data.length > 0) {
                        data.forEach(pais => {
                            let option = document.createElement("option");
                            option.value = pais.id;
                            option.textContent = pais.nombre;
                            paisesSelect.appendChild(option);
                        });
                    } else {
                        console.warn("No se encontraron países");
                    }
                })
                .catch(error => {
                    console.error("Error al cargar países:", error);
                });
        }

        resetDependentSelects(container, 0);
    });
}

/**
 * Resetea los selects dependientes (estados, municipios, colonias) en un contenedor.
 * @param {HTMLElement} container - Contenedor donde están los selects.
 * @param {number} level - Nivel de reseteo (0: todos, 1: desde estados, 2: desde municipios, 3: solo colonias).
 */
function resetDependentSelects(container, level = 0) {
    if (!container) return;

    if (level <= 1) {
        const selectsEst = container.querySelector('select[name="estados"]');
        if (selectsEst) {
            selectsEst.innerHTML = '<option value="" selected>Selecciona el estado</option>';
            selectsEst.disabled = false;
        }
    }

    if (level <= 2) {
        const selectsMun = container.querySelector('select[name="municipios"]');
        if (selectsMun) {
            selectsMun.innerHTML = '<option value="" selected>Selecciona el municipio</option>';
            selectsMun.disabled = false;
        }
    }

    if (level <= 3) {
        const selectsCol = container.querySelector('select[name="idcolonia"]');
        if (selectsCol) {
            selectsCol.innerHTML = '<option value="" selected>Selecciona la colonia</option>';
            selectsCol.disabled = false;
        }
    }
}

/**
 * Carga estados según el país seleccionado.
 * @param {Event} event - Evento de cambio en el select de países.
 */
function selectPais(event) {
    const selectElement = event.target;
    const pais_id = selectElement.value;
    const container = findParentTab(selectElement);

    if (!container) {
        console.error("No se pudo encontrar el contenedor padre");
        return;
    }

    resetDependentSelects(container, 1);

    if (!pais_id) {
        console.warn("No se seleccionó ningún país");
        return;
    }

    fetch("/get-estados/" + pais_id, { method: "GET" })
        .then(response => {
            if (!response.ok) {
                throw new Error("Error al cargar estados: " + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("Estados cargados:", data);
            const selectEst = container.querySelector('select[name="estados"]');
            if (!selectEst) {
                console.error("No se encontró el select de estados en este contenedor");
                return;
            }

            selectEst.innerHTML = '<option value="" selected>Selecciona el estado</option>';

            if (data && data.length > 0) {
                data.forEach(estado => {
                    let option = document.createElement("option");
                    option.value = estado.id;
                    option.textContent = estado.nombre;
                    selectEst.appendChild(option);
                });
                selectEst.hidden = false;
            } else {
                console.warn("No se encontraron estados para el país seleccionado");
            }
        })
        .catch(error => {
            console.error("Error al cargar estados:", error);
        });
}

/**
 * Carga municipios según el estado seleccionado.
 * @param {Event} event - Evento de cambio en el select de estados.
 */
function selectEstado(event) {
    const selectElement = event.target;
    const estado_id = selectElement.value;
    const container = findParentTab(selectElement);

    if (!container) {
        console.error("No se pudo encontrar el contenedor padre");
        return;
    }

    resetDependentSelects(container, 2);

    if (!estado_id) {
        console.warn("No se seleccionó ningún estado");
        return;
    }

    fetch("/get-municipios/" + estado_id, { method: "GET" })
        .then(response => {
            if (!response.ok) {
                throw new Error("Error al cargar municipios: " + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("Municipios cargados:", data);
            const selectMun = container.querySelector('select[name="municipios"]');
            if (!selectMun) {
                console.error("No se encontró el select de municipios en este contenedor");
                return;
            }

            selectMun.innerHTML = '<option value="" disabled selected>Selecciona el municipio</option>';

            if (data && data.length > 0) {
                data.forEach(mun => {
                    let option = document.createElement("option");
                    option.value = mun.id;
                    option.textContent = mun.nombre;
                    selectMun.appendChild(option);
                });
                selectMun.hidden = false;
            } else {
                console.warn("No se encontraron municipios para el estado seleccionado");
            }
        })
        .catch(error => {
            console.error("Error al cargar municipios:", error);
        });
}

/**
 * Carga colonias según el municipio seleccionado.
 * @param {Event} event - Evento de cambio en el select de municipios.
 */
function selectMunicipio(event) {
    const selectElement = event.target;
    const mun_id = selectElement.value;
    const container = findParentTab(selectElement);

    if (!container) {
        console.error("No se pudo encontrar el contenedor padre");
        return;
    }

    resetDependentSelects(container, 3);

    if (!mun_id) {
        console.warn("No se seleccionó ningún municipio");
        return;
    }

    fetch("/get-colonias/" + mun_id, { method: "GET" })
        .then(response => {
            if (!response.ok) {
                throw new Error("Error al cargar colonias: " + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("Colonias cargadas:", data);
            const selectCol = container.querySelector('select[name="idcolonia"]');
            if (!selectCol) {
                console.error("No se encontró el select de colonias en este contenedor");
                return;
            }

            selectCol.innerHTML = '<option value="" disabled selected>Selecciona la colonia</option>';

            if (data && data.length > 0) {
                data.forEach(col => {
                    let option = document.createElement("option");
                    option.value = col.id;
                    option.textContent = col.nombre;
                    selectCol.appendChild(option);
                });
                selectCol.hidden = false;
            } else {
                console.warn("No se encontraron colonias para el municipio seleccionado");
            }
        })
        .catch(error => {
            console.error("Error al cargar colonias:", error);
        });
}

/**
 * Encuentra el contenedor padre (tab-pane) de un elemento.
 * @param {HTMLElement} element - Elemento del cual buscar el contenedor.
 * @returns {HTMLElement|null} - Contenedor padre o null si no se encuentra.
 */
function findParentTab(element) {
    let current = element;
    while (current && !current.classList.contains('tab-pane')) {
        current = current.parentElement;
    }
    return current;
}