function toggleCamposPorRol(rol) {
    const campos = {
        puesto: document.getElementById("emp_puesto"),
        compania: document.getElementById("empresa"),
        sucursal: document.getElementById("sucursal"),
        turno: document.getElementById("emp_turno"),
        sueldo: document.getElementById("emp_sueldo")
    };

    const mostrar = (keys) => {
        Object.entries(campos).forEach(([key, el]) => {
            const container = el.closest(".col-md-4");
            const activo = keys.includes(key);
            if (container) container.style.display = activo ? "block" : "none";
            el.required = activo;
            if (!activo) el.value = ""; // limpiar valor
        });
    };

    if (rol === "2") {
        mostrar(["puesto", "compania", "sucursal", "turno", "sueldo"]);
    } else if (rol === "1") {
        mostrar(["compania"]);
    } else {
        mostrar([]);
    }
}

// Aplicar al cargar
window.addEventListener("DOMContentLoaded", () => {
    toggleCamposPorRol("");
});

// Cambiar al seleccionar rol
document.getElementById("user_rol").addEventListener("change", function () {
    toggleCamposPorRol(this.value);
});

// Cargar roles
fetch('/get-roles')
    .then(res => res.json())
    .then(data => {
        const select = document.getElementById('user_rol');
        data.forEach(r => {
            const option = document.createElement('option');
            option.value = r.id;
            option.textContent = r.nombre;
            select.appendChild(option);
        });
    });

// Compañías
fetch('/get-companias')
    .then(res => res.json())
    .then(data => {
        const select = document.getElementById('empresa');
        data.forEach(c => {
            const option = document.createElement('option');
            option.value = c.rfccomp;
            option.textContent = c.nombre;
            select.appendChild(option);
        });
    });

// Sucursales por compañía
document.getElementById('empresa').addEventListener('change', function () {
    const rfccomp = this.value;
    fetch(`/get-sucursales-by-compania/${rfccomp}`)
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('sucursal');
            select.innerHTML = '<option value="">Selecciona una sucursal</option>';
            data.forEach(s => {
                const option = document.createElement('option');
                option.value = s.id;
                option.textContent = s.nombre;
                select.appendChild(option);
            });
        });
});

// Al seleccionar una sucursal, cargar sus puestos
document.getElementById('sucursal').addEventListener('change', function () {
    const idsucursal = this.value;
    const puestoSelect = document.getElementById('emp_puesto');
    const turnoSelect = document.getElementById('emp_turno');

    // Limpiar opciones anteriores
    puestoSelect.innerHTML = '<option value="" disabled selected>Seleccionar</option>';
    turnoSelect.innerHTML = '<option value="" disabled selected>Selecciona un turno</option>';

    if (!idsucursal) return;

    fetch(`/get-puestos-by-sucursal/${idsucursal}`)
        .then(res => res.json())
        .then(data => {
            data.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = p.nombre;
                puestoSelect.appendChild(option);
            });
        });
});

// Al seleccionar un puesto, cargar turnos disponibles para ese puesto y sucursal
document.getElementById('emp_puesto').addEventListener('change', function () {
    const idpuesto = this.value;
    const idsucursal = document.getElementById('sucursal').value;
    const turnoSelect = document.getElementById('emp_turno');

    turnoSelect.innerHTML = '<option value="" disabled selected>Selecciona un turno</option>';

    if (!idpuesto || !idsucursal) return;

    fetch(`/get-turnos-by-puesto-sucursal/${idpuesto}/${idsucursal}`)
        .then(res => res.json())
        .then(data => {
            data.forEach(t => {
                const option = document.createElement('option');
                option.value = t.id;
                option.textContent = t.nombre;
                turnoSelect.appendChild(option);
            });
        });
});

// Enviar formulario con fetch y mostrar alertas
document.getElementById("datos-usuario").addEventListener("submit", function (e) {
    e.preventDefault();
    const form = e.target;
    const data = new FormData(form);

    fetch('/registerUser', {
        method: 'POST',
        body: data
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.error,
                confirmButtonColor: '#dc3545'
            });
        } else {
            Swal.fire({
                icon: 'success',
                title: 'Usuario registrado',
                text: data.message || 'El usuario fue guardado correctamente.',
                confirmButtonColor: '#ffc107'
            });
            form.reset();
            toggleCamposPorRol(""); // Oculta campos condicionales
        }
    })
    .catch(error => {
        console.error("Error al registrar usuario:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo registrar el usuario.',
            confirmButtonColor: '#dc3545'
        });
    });
});