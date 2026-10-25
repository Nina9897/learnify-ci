// ============================================
// CHAT DEL EQUIPO - VERSIÓN MONGODB CON ICONOS
// ============================================

const usuario = JSON.parse(localStorage.getItem('usuario'));

if (!usuario) {
    window.location.href = '../iniciar_sesion.html';
}

const urlParams = new URLSearchParams(window.location.search);
const equipoId = urlParams.get('equipo_id');

if (!equipoId) {
    window.location.href = 'mis_equipos.html';
}

// ============================================
// REGISTRAR ACTIVIDAD DEL USUARIO
// ============================================
async function registrarActividad(tipo, descripcion = '') {
    try {
        const usuario = JSON.parse(localStorage.getItem('usuario'));
        if (!usuario) return;
        
        await fetch('/api/registrar-actividad', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                usuario_id: usuario._id,
                tipo: tipo,
                descripcion: descripcion
            })
        });
    } catch (error) {
        console.error('Error al registrar actividad:', error);
    }
}

// ============================================
// ESCAPAR HTML
// ============================================
function escapeHtml(texto) {
    if (!texto) return '';
    const div = document.createElement('div');
    div.textContent = texto;
    return div.innerHTML;
}

// ============================================
// CARGAR MENSAJES
// ============================================
async function cargarMensajes() {
    const container = document.getElementById('chatMensajes');
    
    if (!container) {
        console.error('ERROR: No se encontró el contenedor chatMensajes');
        return;
    }
    
    console.log('Cargando mensajes...');
        
    try {
        const respuesta = await fetch(`/api/chat/${equipoId}`);
        const resultado = await respuesta.json();
        
        console.log('Respuesta recibida:', resultado);
        
        if (!resultado.exito) {
            container.innerHTML = '<div class="empty-message"><i class="fas fa-exclamation-triangle"></i> Error al cargar mensajes</div>';
            return;
        }
        
        const mensajes = resultado.mensajes;
        console.log('Número de mensajes:', mensajes ? mensajes.length : 0);
        
        if (!mensajes || mensajes.length === 0) {
            container.innerHTML = '<div class="empty-message"><i class="fas fa-comment-slash"></i> No hay mensajes. ¡Escribe el primero!</div>';
            return;
        }
        
        // Construir HTML manualmente con iconos
        let html = '';
        for (let i = 0; i < mensajes.length; i++) {
            const msg = mensajes[i];
            const esPropio = msg.usuario_id === usuario._id;
            const fecha = new Date(msg.fecha_envio);
            const hora = fecha.toLocaleTimeString('es-MX', {hour: '2-digit', minute:'2-digit'});
            
            html += '<div class="mensaje ' + (esPropio ? 'mensaje-propio' : 'mensaje-otro') + '">';
            
            // Autor con icono
            html += '<div class="mensaje-autor">';
            if (esPropio) {
                html += '<i class="fas fa-user-circle"></i> Tú';
            } else {
                html += '<i class="fas fa-user-astronaut"></i> ' + escapeHtml(msg.usuario_nombre);
            }
            html += '</div>';
            
            // Mensaje con icono de comentario
            html += '<div class="mensaje-texto"><i class="fas fa-comment-dots"></i> ' + escapeHtml(msg.mensaje) + '</div>';
            
            // Fecha con icono de reloj
            html += '<div class="mensaje-fecha"><i class="fas fa-clock"></i> ' + hora + '</div>';
            
            html += '</div>';
        }
        
        console.log('HTML generado:', html);
        container.innerHTML = html;
        container.scrollTop = container.scrollHeight;
        
    } catch (error) {
        console.error('Error en fetch:', error);
        container.innerHTML = '<div class="empty-message"><i class="fas fa-wifi"></i> Error de conexión</div>';
    }
}

// ============================================
// ENVIAR MENSAJE
// ============================================
async function enviarMensaje() {
    const input = document.getElementById('mensajeInput');
    const mensaje = input.value.trim();
    
    if (!mensaje) return;
    
    console.log('Enviando:', mensaje);
    
    try {
        const respuesta = await fetch('/api/chat/enviar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                equipo_id: equipoId,
                usuario_id: usuario._id,
                mensaje: mensaje
            })
        });
        
        const resultado = await respuesta.json();
        console.log('Respuesta enviar:', resultado);
        
        if (resultado.exito) {
            input.value = '';
            cargarMensajes();
        } else {
            alert('❌ Error: ' + resultado.mensaje);
        }
    } catch (error) {
        console.error('Error al enviar:', error);
        alert('❌ Error de conexión');
    }
    // Registrar actividad
    registrarActividad('chat', `Envió mensaje en el chat del equipo ${equipoId}`);
}

// ============================================
// INICIALIZAR
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando chat...');
    console.log('equipoId:', equipoId);
    console.log('usuario:', usuario);
    
    cargarMensajes();
    
    const btnEnviar = document.getElementById('btnEnviar');
    const inputMensaje = document.getElementById('mensajeInput');
    
    console.log('btnEnviar encontrado:', btnEnviar);
    console.log('inputMensaje encontrado:', inputMensaje);
    
    if (btnEnviar) {
        btnEnviar.onclick = enviarMensaje;
    }
    
    if (inputMensaje) {
        inputMensaje.onkeypress = function(e) {
            if (e.key === 'Enter') enviarMensaje();
        };
    }
    
    // Actualizar cada 5 segundos
    setInterval(cargarMensajes, 5000);
});