document.addEventListener("DOMContentLoaded", function() {
    let hEntrada = "{{ session['h_entrada'] }}";
    let hSalida = "{{ session['h_salida'] }}";
    let ahora = new Date();
    
    let [entradaHora, entradaMinuto] = hEntrada.split(":");
    let [salidaHora, salidaMinuto] = hSalida.split(":");

    // Crear un objeto Date para la entrada y salida
    let entradaActivaDesde = new Date();
    entradaActivaDesde.setHours(entradaHora, entradaMinuto - 30, 0, 0);  // 30 minutos antes

    let entradaActivaHasta = new Date();
    entradaActivaHasta.setHours(entradaHora, parseInt(entradaMinuto) + 16, 0, 0);  // 16 minutos después

    let salidaActivaDesde = new Date();
    salidaActivaDesde.setHours(salidaHora, parseInt(salidaMinuto) - 5, 0, 0);  // 5 minutos antes

    // Verificar la asistencia desde el backend
    fetch("/verificar_asistencia")
    .then(response => response.json())
    .then(data => {
        console.log("Respuesta de verificar_asistencia:", data);  // Verifica la respuesta

        // Si la entrada ya fue registrada, desactiva el botón de entrada
        if (data.entrada_registrada) {
            document.getElementById("btnEntrada").disabled = true;
        } else if (ahora >= entradaActivaDesde && ahora <= entradaActivaHasta) {
            document.getElementById("btnEntrada").disabled = false;
        }

        // Si la salida ya fue registrada, desactiva el botón de salida
        if (data.salida_registrada) {
            document.getElementById("btnSalida").disabled = true;
        } else if (data.entrada_registrada && ahora >= salidaActivaDesde) {
            document.getElementById("btnSalida").disabled = false;
        }
    });
});

// Función para registrar asistencia
function registrarAsistencia(tipo) {
    fetch("/registrar_asistencia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tipo: tipo })
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
          if (tipo === "entrada") {
              document.getElementById("btnEntrada").disabled = true;
              document.getElementById("btnSalida").disabled = false;
          } else if (tipo === "salida") {
              document.getElementById("btnSalida").disabled = true;
          }
      });
}
