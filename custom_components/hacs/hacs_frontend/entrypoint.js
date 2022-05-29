
try {
  new Function("import('/hacsfiles/frontend/main-4ba31b39.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-4ba31b39.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  