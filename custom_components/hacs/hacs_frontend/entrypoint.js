
try {
  new Function("import('/hacsfiles/frontend/main-def8a0ab.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-def8a0ab.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  