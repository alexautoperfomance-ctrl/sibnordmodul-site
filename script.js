'use strict';
(()=>{
 const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
 const drawer=$('#menu-drawer'), photo=$('#photo-modal');
 function open(d){if(!d)return;d.showModal();document.body.style.overflow='hidden'}
 function close(d){d.close();if(!$$('dialog[open]').length)document.body.style.overflow=''}
 $$('dialog').forEach(d=>{d.addEventListener('cancel',()=>{document.body.style.overflow=''});d.addEventListener('click',e=>{if(e.target.closest('[data-close]'))close(d);if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close(d)}})});
 const om=$('#open-menu'); if(om) om.addEventListener('click',()=>open(drawer));
 if(drawer) $$('nav a',drawer).forEach(a=>a.addEventListener('click',()=>close(drawer)));
 $$('[data-privacy]').forEach(b=>b.addEventListener('click',()=>open($('#privacy-modal'))));
 $$('[data-year]').forEach(e=>e.textContent=new Date().getFullYear());

 const filters=$$('[data-filter]'), tiles=$$('.scheme-tile');
 let active='all', query='';
 function filter(){
  if(!tiles.length)return;
  let count=0;
  tiles.forEach(p=>{
   const show=(active==='all'||p.dataset.cat===active)&&(!query||(p.dataset.search||'').includes(query));
   p.hidden=!show; if(show)count++;
  });
  const empty=$('.empty-results'); if(empty) empty.hidden=count>0;
  filters.forEach(b=>{
   const on=b.dataset.filter===active;
   b.setAttribute('aria-pressed', on?'true':'false');
   b.classList.toggle('on', on);
  });
 }
 filters.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.filter;filter();history.replaceState(null,'','#cat-'+active)}));
 if(location.hash.startsWith('#cat-')){
  const h=location.hash.slice(5);
  if(filters.some(b=>b.dataset.filter===h)){active=h;filter();}
 }

 let galleryItems=[], current=0;
 function itemsOf(name){return $$(`[data-gallery="${name}"]`).filter(a=>{const t=a.closest('.scheme-tile,.product');return !t||!t.hidden})}
 function showPhoto(i){
  if(!galleryItems.length||!photo)return;
  current=(i+galleryItems.length)%galleryItems.length;
  const a=galleryItems[current], im=$('#lightbox-image');
  im.src=a.getAttribute('href')||a.dataset.full||'';
  im.alt=a.dataset.title||'';
  const t=$('#photo-title'); if(t) t.textContent=a.dataset.title||'';
  const c=$('.photo-counter'); if(c) c.textContent=`${current+1} / ${galleryItems.length}`;
 }
 function openGallery(el){
  const name=el.dataset.gallery||'photos';
  galleryItems=itemsOf(name);
  const i=Math.max(0, galleryItems.indexOf(el));
  showPhoto(i); open(photo);
 }
 $$('[data-gallery]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();openGallery(a)}));
 const prev=photo&&$('.prev',photo), next=photo&&$('.next',photo);
 if(prev) prev.addEventListener('click',()=>showPhoto(current-1));
 if(next) next.addEventListener('click',()=>showPhoto(current+1));
 document.addEventListener('keydown',e=>{if(photo&&photo.open){if(e.key==='ArrowLeft')showPhoto(current-1);if(e.key==='ArrowRight')showPhoto(current+1)}});
})();
