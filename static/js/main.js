'use strict';

/* =========================================================
   RestaurApp — main.js
   ========================================================= */

/* ---------------------------------------------------------
   1. Toggle modo oscuro / claro
      El tema se aplica antes de renderizar (ver <head> en base.html).
      Aquí solo manejamos el botón y sincronizamos el ícono.
   --------------------------------------------------------- */
function syncThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
}

(function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    syncThemeIcon(saved);
})();

document.addEventListener('DOMContentLoaded', function () {

    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            const html    = document.documentElement;
            const current = html.getAttribute('data-bs-theme') || 'light';
            const next    = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-bs-theme', next);
            localStorage.setItem('theme', next);
            syncThemeIcon(next);
        });
    }

    /* ---------------------------------------------------------
       2. Auto-close de alertas a los 4 segundos
       --------------------------------------------------------- */
    document.querySelectorAll('[data-auto-close]').forEach(function (alertEl) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (bsAlert) bsAlert.close();
        }, 4000);
    });

    /* ---------------------------------------------------------
       3. Modal de confirmación de eliminación
          Activa con: data-confirm-url, data-confirm-title (opc.),
                      data-confirm-message (opc.), data-confirm-btn (opc.)
       --------------------------------------------------------- */
    const confirmModal = document.getElementById('confirmModal');
    if (confirmModal) {
        confirmModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            if (!trigger) return;

            const url     = trigger.dataset.confirmUrl     || '#';
            const title   = trigger.dataset.confirmTitle   || 'Confirmar eliminación';
            const message = trigger.dataset.confirmMessage || '¿Estás seguro de que deseas eliminar este elemento? Esta acción no se puede deshacer.';
            const btnText = trigger.dataset.confirmBtn     || 'Eliminar';

            const labelEl   = confirmModal.querySelector('#confirmModalLabel');
            const messageEl = confirmModal.querySelector('#confirmModalMessage');
            const formEl    = confirmModal.querySelector('#confirmForm');
            const btnTextEl = confirmModal.querySelector('#confirmBtnText');

            if (labelEl)   labelEl.textContent   = title;
            if (messageEl) messageEl.textContent = message;
            if (formEl)    formEl.action         = url;
            if (btnTextEl) btnTextEl.textContent = btnText;
        });
    }

    /* ---------------------------------------------------------
       4. Preview de imagen para cualquier input[type="file"]
       --------------------------------------------------------- */
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
        input.addEventListener('change', function () {
            const file = this.files && this.files[0];
            if (!file || !file.type.startsWith('image/')) return;

            let preview = this.parentElement.querySelector('.preview-img');
            if (!preview) {
                preview = document.createElement('img');
                preview.className = 'preview-img';
                preview.alt       = 'Vista previa';
                this.after(preview);
            }

            const prevUrl = preview.dataset.prevObjectUrl;
            if (prevUrl) URL.revokeObjectURL(prevUrl);

            const objectUrl = URL.createObjectURL(file);
            preview.src     = objectUrl;
            preview.dataset.prevObjectUrl = objectUrl;
        });
    });

    /* ---------------------------------------------------------
       5. Spinner de carga al enviar formularios
          Marca el botón submit con la clase .btn-loading.
          Ignora formularios con data-no-spinner.
       --------------------------------------------------------- */
    document.querySelectorAll('form:not([data-no-spinner])').forEach(function (form) {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('[type="submit"]');
            if (!submitBtn || submitBtn.disabled) return;

            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;

            // Salvaguarda: restaura el botón si la navegación no ocurre en 12s
            setTimeout(function () {
                submitBtn.classList.remove('btn-loading');
                submitBtn.disabled = false;
            }, 12000);
        });
    });

});
