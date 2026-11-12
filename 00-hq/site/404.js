// Shows the address the visitor tried, as plain text (never as HTML), cut to 80 characters.
(function(){var t=document.getElementById('tried');if(!t)return;var p=decodeURIComponentSafe(location.pathname+location.search);
if(p&&p!=='/'&&p!=='/404.html')t.textContent=p.length>80?p.slice(0,79)+'\u2026':p;
function decodeURIComponentSafe(s){try{return decodeURIComponent(s);}catch(e){return s;}}})();
