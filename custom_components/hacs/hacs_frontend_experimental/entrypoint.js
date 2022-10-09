
try {
  new Function("import('/hacsfiles/frontend/main-bd0f996b.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/hacsfiles/frontend/main-bd0f996b.js';
  el.type = 'module';
  document.body.appendChild(el);
}
  