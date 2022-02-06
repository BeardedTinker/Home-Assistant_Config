
try {
  new Function("import('/hacsfiles/frontend/main-c4420e0b.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-c4420e0b.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  