'use strict';
(()=>{
 const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
 const callback=$('#callback-modal'), drawer=$('#menu-drawer'), photo=$('#photo-modal');
 function open(d){d.showModal();document.body.style.overflow='hidden'}
 function close(d){d.close();if(!$$('dialog[open]').length)document.body.style.overflow=''}
 $$('dialog').forEach(d=>{d.addEventListener('cancel',()=>{document.body.style.overflow=''});d.addEventListener('click',e=>{if(e.target.closest('[data-close]'))close(d);if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close(d)}})});
 $$('[data-callback]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();$('input[name=product]',callback).value=a.dataset.product||'Строительная бытовка';$('.form-status',callback).textContent='';open(callback)}));
 $('#open-menu').addEventListener('click',()=>open(drawer));$$('nav a',drawer).forEach(a=>a.addEventListener('click',()=>close(drawer)));
 $$('[data-privacy]').forEach(b=>b.addEventListener('click',()=>open($('#privacy-modal'))));
 $$('[data-year]').forEach(e=>e.textContent=new Date().getFullYear());
 const filters=$$('[data-filter]'),products=$$('.product');let active='all',query='';
 function filter(){let count=0;products.forEach(p=>{const show=(active==='all'||p.dataset.category===active)&&p.dataset.search.includes(query);p.hidden=!show;if(show)count++});$('.empty-results').hidden=count>0;filters.forEach(b=>b.setAttribute('aria-pressed',b.dataset.filter===active?'true':'false'))}
 filters.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.filter;query='';$('#catalog-search').value='';filter()}));
 $$('[data-nav-filter]').forEach(a=>a.addEventListener('click',()=>{active=a.dataset.navFilter;query='';$('#catalog-search').value='';filter()}));
 $('#search-form').addEventListener('submit',e=>{e.preventDefault();active='all';query=$('#catalog-search').value.trim().toLocaleLowerCase('ru');filter();$('#catalog').scrollIntoView({behavior:'smooth'})});
 const galleries=$$('[data-gallery]');let current=0;
 function showPhoto(i){current=(i+galleries.length)%galleries.length;const a=galleries[current],im=$('#lightbox-image');im.src=a.getAttribute('href');im.alt=a.dataset.title;$('#photo-title').textContent=a.dataset.title;$('.photo-counter').textContent=`${current+1} / ${galleries.length}`}
 galleries.forEach((a,i)=>a.addEventListener('click',e=>{e.preventDefault();showPhoto(i);open(photo)}));
 $$('[data-photo]').forEach(b=>b.addEventListener('click',()=>{const i=galleries.findIndex(a=>a.getAttribute('href')===b.dataset.photo);showPhoto(Math.max(0,i));open(photo)}));
 $('.prev',photo).addEventListener('click',()=>showPhoto(current-1));$('.next',photo).addEventListener('click',()=>showPhoto(current+1));document.addEventListener('keydown',e=>{if(photo.open){if(e.key==='ArrowLeft')showPhoto(current-1);if(e.key==='ArrowRight')showPhoto(current+1)}});
 function message(form){const d=new FormData(form);return `Здравствуйте! Интересует: ${d.get('product')||'строительная бытовка'}.\nИмя: ${String(d.get('customer')||'').trim()}.\nТелефон для связи: ${String(d.get('phone')||'').trim()}.\nПодскажите, пожалуйста, наличие и стоимость.`}
 function valid(form){if(!form.reportValidity())return false;const input=$('input[name=phone]',form);const n=input.value.replace(/\D/g,'');if(n.length<10||n.length>15){input.setCustomValidity('Укажите корректный номер телефона (10–15 цифр).');input.reportValidity();return false}return true}
 $$('.callback-form').forEach(form=>{
  $('input[name=phone]',form).addEventListener('input',e=>e.target.setCustomValidity(''));
  form.addEventListener('submit',e=>{e.preventDefault();if(!valid(form))return;const url='https://wa.me/79139438814?text='+encodeURIComponent(message(form));const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';a.click();$('.form-status',form).textContent='Откроется WhatsApp с подготовленным текстом. Заявка ещё не отправлена.'});
  $('[data-email]',form).addEventListener('click',()=>{if(!valid(form))return;window.location.href='mailto:Sibnordmodul@yandex.ru?subject='+encodeURIComponent('Заявка с сайта SibNordModul')+'&body='+encodeURIComponent(message(form));$('.form-status',form).textContent='Сообщение подготовлено для вашей почтовой программы. Проверьте его перед отправкой.'});
 });
})();
