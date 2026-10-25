// Script para la gestión de tareas y actualización dinámica de porcentajes

document.addEventListener('DOMContentLoaded', function() {
  // Configurar círculo de progreso con el valor exacto (96%)
  const progressCircle = document.querySelector('.progress-circle');
  if (progressCircle) {
    const progress = progressCircle.dataset.progress || '96';
    const degrees = (parseInt(progress) / 100) * 360;
    progressCircle.style.background = `conic-gradient(#2f7bff 0deg ${degrees}deg, #e6edf6 ${degrees}deg 360deg)`;
  }

  // Elementos de tareas para posible interacción futura
  const taskItems = document.querySelectorAll('.task-item');
  
  // Función para cambiar estado (ejemplo educativo)
  window.marcarCompletada = function(taskElement) {
    const statusSpan = taskElement.querySelector('.task-status');
    if (statusSpan) {
      statusSpan.className = 'task-status status-completed';
      statusSpan.textContent = 'completada';
      taskElement.dataset.status = 'completada';
      
      // Cambiar icono
      const icon = taskElement.querySelector('i');
      if (icon) {
        icon.className = 'fas fa-check-circle';
        icon.style.color = '#1f8b4c';
      }
    }
  };

  // Simulación de carga de tareas (ejemplo dinámico)
  console.log('Learnify Asignaciones cargado correctamente');
  
  // Actualizar el texto de 12 tareas si es necesario
  const appFooter = document.querySelector('.app-widget .widget-footer');
  if (appFooter) {
    // Podría venir desde backend, dejamos el texto estático, pero verificamos
    const tareasCount = appFooter.textContent.trim(); // "12 tareas"
    if (tareasCount !== '12 tareas') {
      appFooter.textContent = '12 tareas';
    }
  }

  // Opcional: añadir interacción a los equipos
  const teamItems = document.querySelectorAll('.team-item');
  teamItems.forEach(item => {
    item.addEventListener('click', function() {
      // feedback visual simple
      this.style.backgroundColor = '#eaf0fd';
      setTimeout(() => {
        this.style.backgroundColor = '';
      }, 200);
    });
  });
});

// Exportación simbólica (si se usara módulos, pero aquí no es necesario)