
try {
  new Function("import('/hacsfiles/frontend/main-150a7578.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-150a7578.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  