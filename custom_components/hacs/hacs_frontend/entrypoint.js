
try {
  new Function("import('/hacsfiles/frontend/main-10cdb7d6.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-10cdb7d6.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  