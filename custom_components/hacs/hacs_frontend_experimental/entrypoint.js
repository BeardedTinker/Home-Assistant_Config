
try {
  new Function("import('/hacsfiles/frontend/main-22e4648c.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-22e4648c.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  