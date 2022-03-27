
try {
  new Function("import('/hacsfiles/frontend/main-c486ac4b.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-c486ac4b.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  