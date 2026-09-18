(function () {
  'use strict';

  var toggleButtons = document.querySelectorAll('.toggle-visibility');

  toggleButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var targetId = button.getAttribute('data-target');
      var input = document.getElementById(targetId);
      if (!input) return;

      var isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      button.setAttribute('aria-pressed', String(isHidden));
      button.setAttribute('aria-label', isHidden ? 'Ocultar senha' : 'Mostrar senha');

      button.querySelector('.icon--eye').hidden = isHidden;
      button.querySelector('.icon--eye-off').hidden = !isHidden;
    });
  });

  var form = document.querySelector('.form');
  var status = document.querySelector('.form__status');

  if (form && status) {
    form.addEventListener('submit', function (event) {
      event.preventDefault();

      var email = form.querySelector('#email');
      var password = form.querySelector('#password');
      var valid = email.checkValidity() && password.checkValidity();

      if (!valid) {
        status.dataset.state = 'error';
        status.textContent = 'ERRO: PREENCHA EMAIL E SENHA VÁLIDOS.';
        return;
      }

      status.dataset.state = 'success';
      status.textContent = 'CREDENCIAIS RECEBIDAS. AUTENTICANDO...';
    });
  }
})();
