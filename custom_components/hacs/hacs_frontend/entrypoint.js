
try {
  new Function("import('/hacsfiles/frontend/main-a0d7432d.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-a0d7432d.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  