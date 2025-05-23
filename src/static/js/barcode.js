  let currentStream = null;
  let beepSound = new Audio('beep.mp3'); // Asegúrate de tener un archivo de sonido 'beep.mp3' en tu proyecto
  let lastDetectedCode = null; // Variable para almacenar el último código detectado
  let lastDetectionTime = 0; // Variable para almacenar el tiempo de la última detección
  const detectionCooldown = 2000; // Tiempo de espera entre detecciones en milisegundos (2 segundos)

  // Solo iniciar la cámara en dispositivos móviles
  if (window.innerWidth <= 768) {
    document.getElementById("barcode-section").style.display = "block"; // Mostrar la sección de la cámara
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
      currentStream = await navigator.mediaDevices.getUserMedia(constraints);
      const video = document.getElementById('camera');
      video.srcObject = currentStream;
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

          // Reproducir sonido
          beepSound.play();

          // Puedes realizar otras acciones como agregar el producto automáticamente si es necesario
          // agregarProducto(detectedCode, 1); // Ejemplo de acción
        }
      }
    } catch (err) {
      console.error('Error al detectar el código de barras: ', err);
    }

    // Continuar la detección de códigos de barras
    requestAnimationFrame(detectBarcode);
  }