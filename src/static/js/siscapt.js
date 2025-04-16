function getCookie(nombre) {
    let cookies = document.cookie.split("; "); // Divide todas las cookies
    for (let cookie of cookies) {
        let [clave, valor] = cookie.split("="); // Separa clave=valor
        if (clave === nombre) {
            return decodeURIComponent(valor); // Decodifica el valor
        }
    }
    return null; // Retorna null si no existe la cookie
}

// Uso
let token = getCookie("token");

let intervalo = setInterval(() => {
    
    if(token == null){
        clearInterval(intervalo); // Detiene el contador
        return;
    }

    let timeRes = getCookie("timeRes");


    timeRes--;

    //console.log(`Tiempo restante: ${timeRes}s`); // Muestra el tiempo en la consola
    document.cookie = "timeRes="+timeRes+"; path=/;";

    if (timeRes <= 0) {
        clearInterval(intervalo); // Detiene el contador
        document.cookie = "timeRes=; path=/; expires=Tue, 1 Jan 2000 03:14:07 GMT"
        cerrarSesion(); // Ejecuta la acción cuando llega a 0
    }
}, 1000);

function cerrarSesion() {
    Swal.fire({
        title: "Sesión expirada",
        text: "Tu sesión ha expirado, vuelve a iniciar sesión.",
        icon: "info",
        confirmButtonText: "Aceptar"
    }).then(() => {
        document.cookie = "token=; path=/; expires=Tue, 1 Jan 2000 03:14:07 GMT"
        window.location.href = "/";  // Redirige después del alert
    });
}
