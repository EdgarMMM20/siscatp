document.addEventListener("DOMContentLoaded", function () {
    const cvproInput = document.getElementById("cvpro");
    const cvcajaInput = document.getElementById("cvcaja");
    const codigoSi = document.getElementById("codigoSi");
    const codigoNo = document.getElementById("codigoNo");
    const barcodeContainer = document.getElementById("barcode-container");
    const idzonalmacenInput = document.getElementById("idzonalmacen");
    const fcaducidadInput = document.getElementById("fcaducidad");
    const barcodeSvg = document.getElementById("barcode");

    // Cargar productos para el select
    fetch("/get-productos")
      .then(response => response.json())
      .then(data => {
        const selectProducto = document.getElementById("cvpro");
        selectProducto.innerHTML = '<option value="" disabled selected>Seleccionar producto o escanear</option>';
        
        data.forEach(producto => {
          const option = document.createElement("option");
          option.value = producto.cvpro; // Asignamos el código del producto como valor
          option.textContent = producto.nombre; // Nombre del producto
          selectProducto.appendChild(option);
        });
        
        // Inicializar select2 para que se pueda escribir en el campo
        $(selectProducto).select2({
          placeholder: 'Seleccionar producto o escanear',
          allowClear: true
        });
      })
      .catch(error => {
        console.error("Error al cargar productos:", error);
      });

    // Cuando se seleccione un producto, actualizar la zona y habilitar la fecha de caducidad si corresponde
    cvproInput.addEventListener("change", function () {
      const cvpro = this.value;
      fetch(`/get-producto-info/${cvpro}`)
        .then(response => response.json())
        .then(data => {
          // Asignar la zona del almacén al input correspondiente
          idzonalmacenInput.value = data.zona;

          // Habilitar o deshabilitar la fecha de caducidad dependiendo de si el producto requiere caducidad
          if (data.requiere_caducidad === "requiere" || data.requiere_caducidad === "opcional") {
            fcaducidadInput.disabled = false;
          } else {
            fcaducidadInput.disabled = true;
          }
        })
        .catch(error => {
          console.error("Error al obtener la información del producto:", error);
        });
    });

    // Función para manejar el escaneo de códigos de barras
    const beepSound = new Audio('beep.mp3'); // Asegúrate de tener un archivo de sonido 'beep.mp3' en tu proyecto
    let lastDetectedCode = null;
    let lastDetectionTime = 0;
    const detectionCooldown = 2000;

    // Lógica para detectar códigos de barras con la cámara
    if (window.innerWidth <= 768) {
        document.getElementById("barcode-section").style.display = "block"; // Mostrar la cámara
        startScanner(); // Iniciar la cámara para detectar códigos de barras
    }

    async function startScanner() {
        if (!('BarcodeDetector' in window)) {
            console.error('Barcode Detector no soportado por este navegador.');
            return;
        }

        try {
            const constraints = {
                video: {
                    facingMode: 'environment', // Usar la cámara trasera
                    width: 640,
                    height: 480
                }
            };

            // Acceder a la cámara
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            const video = document.getElementById('camera');
            video.srcObject = stream;
            video.play();

            video.addEventListener('loadeddata', () => {
                detectBarcode(); // Iniciar la detección de códigos de barras cuando el video se haya cargado
            });
        } catch (err) {
            console.error('Error al acceder a la cámara: ', err);
        }
    }

    async function detectBarcode() {
        const video = document.getElementById('camera');
        const barcodeDetector = new BarcodeDetector({ formats: ['code_128', 'ean_13', 'ean_8', 'qr_code'] });

        try {
            const barcodes = await barcodeDetector.detect(video);
            const currentTime = Date.now(); // Obtener el tiempo actual

            if (barcodes.length > 0) {
                const detectedCode = barcodes[0].rawValue;

                // Verificar si el código detectado es el mismo que el anterior y si ha pasado el tiempo de espera
                if (detectedCode !== lastDetectedCode || (currentTime - lastDetectionTime) > detectionCooldown) {
                    lastDetectedCode = detectedCode;
                    lastDetectionTime = currentTime;

                    // Actualiza el input de "Código del producto" con el valor detectado
                    document.getElementById('cvpro').value = detectedCode;
                    beepSound.play(); // Reproducir sonido

                    // Actualizamos la zona y la fecha de caducidad
                    fetch(`/get-producto-info/${detectedCode}`)
                        .then(response => response.json())
                        .then(data => {
                            idzonalmacenInput.value = data.zona;

                            if (data.requiere_caducidad === "requiere" || data.requiere_caducidad === "opcional") {
                                fcaducidadInput.disabled = false;
                            } else {
                                fcaducidadInput.disabled = true;
                            }
                        })
                        .catch(error => {
                            console.error("Error al obtener la información del producto:", error);
                        });
                }
            }
        } catch (err) {
            console.error('Error al detectar el código de barras: ', err);
        }

        // Continuar detectando
        requestAnimationFrame(detectBarcode);
    }

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

    // Registrar la caja
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