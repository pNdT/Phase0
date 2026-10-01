const form = document.getElementById('login-form');
const errorBox = document.getElementById('error');
form.onsubmit = async event => {
  event.preventDefault();
  const button = document.getElementById('login-button');
  button.disabled = true; errorBox.hidden = true;
  try {
    const response = await fetch('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({password: document.getElementById('password').value})});
    if (response.ok) { window.location.replace('/'); return; }
    const result = await response.json().catch(() => ({}));
    errorBox.textContent = result.error || 'Could not sign in.'; errorBox.hidden = false;
  } catch { errorBox.textContent = 'Could not reach the server.'; errorBox.hidden = false; }
  finally { button.disabled = false; }
};
