/**
 * Módulo de manejo de formularios con SweetAlert2, persistencia en localStorage
 * y navegación por pestañas de Bootstrap.
 *
 * Este script facilita:
 *  - Validación y envío de formularios vía fetch con async/await.
 *  - Feedback visual con SweetAlert2 y spinners en botones.
 *  - Persistencia automática de datos de formulario en localStorage.
 *  - Control de un flujo de registro en dos pasos (owner → company).
 *  - Reutilización de funciones para proyectos similares.
 */

// -----------------------------
// CONFIGURACIÓN DE CLAVES
// -----------------------------
/** Clave para detectar flujo pendiente entre ownerForm y companyForm */
const REGISTRO_PENDIENTE_KEY = "registroDueñoPendiente";

/** Map de IDs de formulario a sus claves de localStorage */
const FORM_KEYS = {
  ownerForm: "ownerFormData",
  companyForm: "companyFormData"
};

// -----------------------------
// ENVÍO DE FORMULARIO
// -----------------------------

/**
 * Maneja el evento submit de un formulario:
 *  1) Valida el formulario (HTML5).
 *  2) Muestra spinner y deshabilita botón de envío.
 *  3) Hace fetch POST al endpoint con FormData.
 *  4) Muestra SweetAlert2 con éxito o error.
 *  5) Llama a onSuccess para continuar flujo.
 *
 * @param {SubmitEvent} event         Evento de submit del formulario
 * @param {string} formId             ID del formulario (p.ej. "ownerForm")
 * @param {string} endpoint           URL a la que enviar la petición
 * @param {string|null} nextTabSelector Selector CSS de la siguiente pestaña a mostrar (o null)
 */
async function handleSubmit(event, formId, endpoint, nextTabSelector) {
  event.preventDefault();
  const form = event.target;

  // 1) Validación nativa HTML5
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  // 2) Preparar spinner en el botón de submit
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnHTML = submitBtn?.innerHTML;
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Enviando...
    `;
  }

  // 3) Crear FormData a partir del formulario
  const formData = new FormData(form);

  try {
    // 4) Petición fetch con método POST
    const res = await fetch(endpoint, { method: "POST", body: formData });
    const data = await res.json();

    // Si la respuesta no indica éxito, lanzamos error
    if (!data.success) {
      throw new Error(data.error || "Ocurrió un error inesperado");
    }

    // 5) Modal de éxito
    await Swal.fire({
      title: "Registro exitoso",
      text: data.msg || "Operación completada con éxito",
      icon: "success",
      confirmButtonText: "Aceptar"
    });

    // 6) Continuar flujo según formId
    onSuccess(formId, nextTabSelector);

  } catch (err) {
    console.error("Error en handleSubmit:", err);

    // Determinar mensaje de conexión vs. otro tipo de error
    const isConnError = /failed|network|conexión/i.test(err.message);
    Swal.fire({
      title: isConnError ? "Error de conexión" : "Error",
      text: isConnError
        ? "No se pudo conectar con el servidor"
        : err.message,
      icon: "error",
      confirmButtonText: "Aceptar"
    });

  } finally {
    // Restaurar botón de envío original
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHTML;
    }
  }
}

/**
 * Asocia el handler de envío a un formulario determinado.
 *
 * @param {string} formId             ID del formulario en el DOM
 * @param {string} endpoint           URL del endpoint para el fetch
 * @param {string|null} nextTabSelector Selector CSS de la siguiente pestaña
 */
function setupFormHandler(formId, endpoint, nextTabSelector) {
  const form = document.getElementById(formId);
  if (!form) {
    console.error(`Formulario con ID "${formId}" no encontrado`);
    return;
  }
  form.addEventListener("submit", e =>
    handleSubmit(e, formId, endpoint, nextTabSelector)
  );
}

// -----------------------------
// LÓGICA POST-ENVÍO EXITOSO
// -----------------------------

/**
 * Ejecuta la lógica tras un envío exitoso:
 *  - OwnerForm: activa pestaña de company, guarda estado en localStorage.
 *  - CompanyForm: limpia flujo y formularios.
 *
 * @param {string} formId             ID del formulario enviado
 * @param {string|null} nextTabSelector Selector CSS de la siguiente pestaña
 */
function onSuccess(formId, nextTabSelector) {
  if (formId === "ownerForm") {
    // Paso 1 → Paso 2
    localStorage.setItem(REGISTRO_PENDIENTE_KEY, "1");
    localStorage.removeItem(FORM_KEYS.ownerForm);
    showTab(nextTabSelector, 100, "Paso 2 de 2");

  } else if (formId === "companyForm") {
    // Fin del flujo de registro
    localStorage.removeItem(REGISTRO_PENDIENTE_KEY);
    localStorage.removeItem(FORM_KEYS.companyForm);

    // Limpiar formularios
    clearForm("ownerForm");
    clearForm("companyForm");

    // Reiniciar barra de progreso al terminar todo
    const progressBar = DocumentFragment.getElementById("progress-bar");
    if (progressBar) {
      progressBar.style.width = "0%";
      progressBar.textContent = "Paso 1 de 2";
    }
  }
}

// -----------------------------
// NAVEGACIÓN DE PESTAÑAS Y PROGRESO
// -----------------------------

/**
 * Habilita y muestra una pestaña, y actualiza la barra de progreso.
 *
 * @param {string|null} selector      Selector CSS de la pestaña a mostrar
 * @param {number} widthPercent       Ancho de la barra de progreso (0–100)
 * @param {string} text               Texto a mostrar dentro de la barra
 */
function showTab(selector, widthPercent, text) {
  if (selector) {
    const tab = document.querySelector(selector);
    if (tab) {
      tab.removeAttribute("disabled");
      bootstrap.Tab.getOrCreateInstance(tab).show();
    }
  }
  const progressBar = document.getElementById("progress-bar");
  if (progressBar) {
    progressBar.style.width = `${widthPercent}%`;
    progressBar.textContent = text;
  }
}

// -----------------------------
// PERSISTENCIA AUTOMÁTICA
// -----------------------------

/**
 * Persiste los campos de un formulario en localStorage con debounce.
 * Permite recargar sus valores al volver a cargar la página.
 *
 * @param {string} formId             ID del formulario en el DOM
 * @param {string} storageKey         Clave de localStorage donde guardar JSON
 */
function persistFormData(formId, storageKey) {
  const form = document.getElementById(formId);
  if (!form) return;

  // Al cargar la página: rellenar campos guardados
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    try {
      const data = JSON.parse(saved);
      Object.keys(data).forEach(name => {
        const field = form.elements.namedItem(name);
        if (field) field.value = data[name];
      });
    } catch {
      // JSON inválido → ignorar
    }
  }

  // Al cambiar cualquier campo: guardar con debounce (300 ms)
  let timer;
  form.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const data = {};
      for (const el of form.elements) {
        // Solo guardar campos con name y no passwords
        if (el.name && el.type !== "password") {
          data[el.name] = el.value;
        }
      }
      localStorage.setItem(storageKey, JSON.stringify(data));
    }, 300);
  });
}

// -----------------------------
// LIMPIEZA DE FORMULARIOS
// -----------------------------

/**
 * Limpia un formulario reseteando valores a sus estados iniciales.
 *
 * @param {string} formId     ID del formulario a limpiar
 */
function clearForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  // reset() maneja inputs, selects y checkboxes
  form.reset();
}

// -----------------------------
// INICIALIZACIÓN AL CARGAR PÁGINA
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {
  // 1) Persistencia de ownerForm y companyForm
  persistFormData("ownerForm", FORM_KEYS.ownerForm);
  persistFormData("companyForm", FORM_KEYS.companyForm);

  // 2) Si quedó flujo pendiente, mostrar segundo paso
  if (localStorage.getItem(REGISTRO_PENDIENTE_KEY)) {
    showTab("#tab-compania", 100, "Paso 2 de 2");
  }

  // 3) Inicializar selects (función propia de tu proyecto)
  initSelects();

  // 4) Asociar manejadores de envío
  setupFormHandler("ownerForm", "/registerperson", "#tab-compania");
  setupFormHandler("companyForm", "/registrarcompany", null);

  // 5) Cuando cambian pestañas de Bootstrap, recargar selects del paso
  document
    .querySelectorAll('button[data-bs-toggle="pill"]')
    .forEach(tab => {
      tab.addEventListener("shown.bs.tab", e => {
        const targetId = e.target
          .getAttribute("data-bs-target")
          .substring(1);
        initSelects(targetId);
      });
    });
});
