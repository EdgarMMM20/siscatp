document.addEventListener("DOMContentLoaded", function () {
    const cvproInput = document.getElementById("cvpro");
    const cvcajaInput = document.getElementById("cvcaja");
    const codigoSi = document.getElementById("codigoSi");
    const codigoNo = document.getElementById("codigoNo");
    const barcodeContainer = document.getElementById("barcode-container");
    const barcodeSvg = document.getElementById("barcode");

    // Cargar zonas
    fetch("/get-zonalma")
      .then(response => response.json())
      .then(data => {
        const selectZona = document.getElementById("idzonalmacen");
        selectZona.innerHTML = '<option value="" disabled selected>Seleccionar zona</option>';
        data.forEach(zona => {
          const option = document.createElement("option");
          option.value = zona.idzonalma;
          option.textContent = zona.nombre;
          selectZona.appendChild(option);
        });
      })
      .catch(error => console.error("Error al cargar zonas:", error));

    function actualizarEstadoCodigo() {
      const tieneCodigo = codigoSi.checked;
      cvcajaInput.readOnly = !tieneCodigo;

      if (tieneCodigo) {
        cvcajaInput.value = "";
        barcodeContainer.style.display = "none";
      } else {
        generarCodigoCaja();
      }
    }

    function generarCodigoCaja() {
      const cvpro = cvproInput.value.trim();
      if (cvpro.length >= 4) {
        const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
        const ultimos4 = cvpro.slice(-4).toUpperCase();
        const codigo = `CXA${ultimos4}${timestamp}`;
        cvcajaInput.value = codigo;

        JsBarcode("#barcode", codigo, { format: "CODE128", width: 2, height: 50 });
        barcodeContainer.style.display = "block";
      } else {
        cvcajaInput.value = "";
        barcodeContainer.style.display = "none";
      }
    }

    // Listeners
    codigoSi.addEventListener("change", actualizarEstadoCodigo);
    codigoNo.addEventListener("change", actualizarEstadoCodigo);
    cvproInput.addEventListener("input", function () {
      if (!codigoSi.checked) generarCodigoCaja();
    });

    actualizarEstadoCodigo(); // inicial

    const form = document.getElementById("formCaja");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(form);

      fetch("/registrarcaja", {
        method: "POST",
        body: formData
      })
        .then(response => {
          if (!response.ok) throw new Error("Error en el servidor");
          return response.json();
        })
        .then(data => {
          Swal.fire({
            icon: 'success',
            title: 'Caja registrada',
            text: data.msg || 'La caja fue guardada correctamente.',
            confirmButtonColor: '#ffc107'
          });
          form.reset();
          barcodeContainer.style.display = "none";
        })
        .catch(error => {
          console.error("Error al registrar caja:", error);
          Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo registrar la caja.',
            confirmButtonColor: '#dc3545'
          });
        });
    });
  });