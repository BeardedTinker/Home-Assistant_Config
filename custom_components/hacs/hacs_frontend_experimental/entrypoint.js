
try {
  new Function("import('/hacsfiles/frontend/main-e6d3fb5e.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-e6d3fb5e.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  