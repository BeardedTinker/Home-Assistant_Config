
try {
  new Function("import('/hacsfiles/frontend/main-50818363.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-50818363.js';
  document.body.appendChild(el);
}
  