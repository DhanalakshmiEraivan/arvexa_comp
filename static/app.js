(()=>{"use strict";
const $=id=>document.getElementById(id);
const topicList=["AI-Powered Learning Studio","Sustainable City Dashboard","Future of Digital Healthcare","Cybersecurity Awareness Hub","Accessible Career Navigator","Smart Agriculture Experience","Space Exploration Portal","Community Emergency Response","Climate Action Tracker","Local Business Digital Twin"];
function csrf(){
 const el=document.querySelector("[name=csrfmiddlewaretoken]")||$("csrfvalue");
 if(el?.value)return el.value;
 const match=document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
 return match?decodeURIComponent(match[1]):"";
}
function fireConfetti(){const wrap=document.createElement("div");wrap.className="confetti-layer";for(let i=0;i<34;i++){const s=document.createElement("i");s.style.left=(35+Math.random()*30)+"%";s.style.top="45%";s.style.setProperty("--dx",(Math.random()*360-180)+"px");s.style.setProperty("--dy",(Math.random()*300-120)+"px");s.style.setProperty("--rot",(Math.random()*720-360)+"deg");wrap.appendChild(s)}document.body.appendChild(wrap);setTimeout(()=>wrap.remove(),1300)}

function initWheel(){
 const wheel=$("wheel"),btn=$("spin");if(!wheel||!btn)return;
 const result=$("topicResult"),support=$("topicSupport"),link=$("websubmit"),pulse=$("assignmentPulse");
 let rotation=0,busy=false;
 function show(topic,locked){
   const n=topicList.indexOf(topic);

   result.textContent=n>=0
      ?`TOPIC ${String(n+1).padStart(2,"0")} · ${topic}`
      :"Awaiting your brief";

   support.textContent=locked
      ?"Assignment locked. Your brief is now attached to this participant session."
      :"Spin once to receive a single official brief.";

   link.href=locked
      ?"/webphobia/submit/"
      :"javascript:void(0)";

   link.classList.toggle("disabled-link",!locked);
   link.setAttribute("aria-disabled",locked?"false":"true");
   link.tabIndex=locked?0:-1;

   btn.textContent=locked?"Topic assigned":"Spin the wheel";
   btn.disabled=locked;
}
 const assigned=window.assignedTopic||"";
 if(assigned){show(assigned,true);return}
 async function assign(){
   const token=csrf();
   const r=await fetch("/webphobia/assign/",{
      method:"POST",
      credentials:"same-origin",
      headers:{
         "X-CSRFToken":token,
         "Accept":"application/json"
      }
   });

   if(!r.ok){
      const text=await r.text();
      console.error("Webphobia assignment failed:",r.status,text);
      throw new Error("assignment failed");
   }

   const data=await r.json();

   if(!data.topic){
      throw new Error("No topic returned");
   }

   return data;
}
 window.spinWheel=async()=>{
   if(busy)return;busy=true;btn.disabled=true;btn.textContent="Selecting brief…";
   try{
     const data=await assign(),topic=data.topic,n=topicList.indexOf(topic);
     const target=360-(n*36+18),delta=(target-(rotation%360)+360)%360;
     rotation+=2160+delta;
     wheel.style.transform=`rotate(${rotation}deg)`;
     setTimeout(()=>{
   show(topic,true);
   pulse.classList.add("active");
   fireConfetti();
   busy=false;
},5350);
   }catch(e){busy=false;btn.disabled=false;btn.textContent="Try again";support.textContent="The assignment service did not respond. Please try once more."}
 };
}
window.copyTopic=async()=>{const el=$("topicResult");if(!el)return;try{await navigator.clipboard.writeText(el.textContent);$("topicSupport").textContent="Brief copied to your clipboard."}catch(e){$("topicSupport").textContent="Clipboard access is unavailable in this browser."}};

function initExam(){
 if(!window.examData||!$("question"))return;
 const {questions,remaining}=window.examData;
 let answers=window.examData.answers||{},index=0,left=remaining,violations=0,done=false;
 let review=new Set();const storeKey="arvexa_exam_"+location.pathname;
 try{const saved=JSON.parse(localStorage.getItem(storeKey)||"{}");answers={...saved.answers,...answers};review=new Set(saved.review||[])}catch(e){}
 const persist=()=>{try{localStorage.setItem(storeKey,JSON.stringify({answers,review:[...review]}))}catch(e){}};
 const answeredCount=()=>Object.keys(answers).filter(k=>questions.some(q=>String(q.id)===String(k))).length;
 const saveTest=async()=>{
   persist();
   try{
     const r=await fetch("/aptiq/save/",{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify({answers,violations})});
     if(!r.ok)throw new Error();
     $("warning").textContent="Saved · "+new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
   }catch(e){$("warning").textContent="Connection issue · your latest answers remain saved on this device."}
 };
 function render(){
   const q=questions[index];if(!q)return;
   $("roundLabel").textContent="· "+(q.round===1?"AI AWARENESS":"LOGIC & APTITUDE");
   $("counter").textContent=`QUESTION ${index+1} / ${questions.length}`;
   $("question").textContent=q.prompt;$("choices").innerHTML="";
   ["A","B","C","D"].forEach(k=>{const b=document.createElement("button");b.type="button";b.className="choice"+(answers[q.id]===k?" selected":"");b.setAttribute("aria-pressed",answers[q.id]===k);b.textContent=k+". "+q[k.toLowerCase()];b.onclick=()=>{answers[q.id]=k;persist();render();saveTest()};$("choices").appendChild(b)});
   $("palette").innerHTML="";
   questions.forEach((item,i)=>{const b=document.createElement("button");b.type="button";b.textContent=i+1;b.className=(answers[item.id]?"done ":"")+(review.has(String(item.id))?"review ":"")+(i===index?"current":"");b.onclick=()=>{index=i;render()};$("palette").appendChild(b)});
   $("answered").textContent=`${answeredCount()} / ${questions.length}`;
   $("bar").style.width=(answeredCount()/questions.length*100)+"%";
   const mark=$("reviewCurrent");if(mark)mark.textContent=review.has(String(q.id))?"Remove review mark":"Mark for review";
 }
 window.move=d=>{index=Math.max(0,Math.min(questions.length-1,index+d));render()};
 window.toggleReview=()=>{const id=String(questions[index].id);review.has(id)?review.delete(id):review.add(id);persist();render()};
 window.finishTest=async(force=false)=>{
   if(done)return;
   const unanswered=questions.length-answeredCount();
   if(!force&&!confirm(unanswered?`There are ${unanswered} unanswered questions. Submit anyway?`:"Submit your assessment now?"))return;
   done=true;await saveTest();
   try{
     const r=await fetch("/aptiq/finish/",{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify({answers})});
     if(!r.ok)throw new Error();
     localStorage.removeItem(storeKey);location.href="/arenas/";
   }catch(e){done=false;alert("The assessment could not be submitted. Reconnect and try again.")}
 };
 let lastHeartbeat=Date.now();
 setInterval(()=>{if(done)return;left=Math.max(0,left-1);const c=$("clock");c.textContent=`${String(Math.floor(left/60)).padStart(2,"0")}:${String(left%60).padStart(2,"0")}`;c.classList.toggle("urgent",left<=300);if(left===300)$("warning").textContent="Five minutes remaining.";if(left===60)$("warning").textContent="One minute remaining.";if(left===0)window.finishTest(true)},1000);
 setInterval(()=>{if(!done&&navigator.onLine&&Date.now()-lastHeartbeat>9000){saveTest();lastHeartbeat=Date.now()}},10000);
 function monitor(type,detail){fetch("/api/heartbeat/",{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify({event_type:type,detail:detail||"",record:true})}).catch(()=>{})}
 document.addEventListener("visibilitychange",()=>{if(done)return;if(document.hidden){violations++;monitor("tab_hidden","Assessment document became hidden. Count: "+violations);$("warning").textContent="Focus change recorded · "+violations}else monitor("tab_visible","Assessment visible again")});
 window.addEventListener("blur",()=>{if(!done)monitor("window_blur","Browser window lost focus")});
 document.addEventListener("copy",e=>{if(!done){e.preventDefault();monitor("copy_attempt","Copy blocked during assessment")}});
 document.addEventListener("paste",e=>{if(!done){e.preventDefault();monitor("paste_attempt","Paste blocked during assessment")}});
 document.addEventListener("contextmenu",e=>{if(!done){e.preventDefault();monitor("context_menu","Context menu blocked during assessment")}});
 document.addEventListener("fullscreenchange",()=>{if(document.fullscreenElement===null&&!done)monitor("fullscreen_exit","Fullscreen exited during assessment")});
 document.addEventListener("keydown",e=>{if(e.altKey||e.ctrlKey||e.metaKey||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;if(e.key==="ArrowRight")move(1);else if(e.key==="ArrowLeft")move(-1);else if("abcd".includes(e.key.toLowerCase())){const b=$("choices").children["abcd".indexOf(e.key.toLowerCase())];if(b)b.click()}else if(e.key.toLowerCase()==="r")toggleReview()});
 render();
}
function initFullscreen(){document.addEventListener("submit",e=>{if(e.target.matches('form[action="/aptiq/start/"]')&&document.documentElement.requestFullscreen){const p=document.documentElement.requestFullscreen();if(p?.catch)p.catch(()=>{})}},true)}
function initReveal(){const els=document.querySelectorAll(".reveal,.challenge-card,.arena-card,.journey-card,.content-card,.admin-panel");if(!("IntersectionObserver"in window)){els.forEach(e=>e.classList.add("is-visible"));return}const io=new IntersectionObserver(entries=>entries.forEach(x=>{if(x.isIntersecting){x.target.classList.add("is-visible");io.unobserve(x.target)}}),{threshold:.08});els.forEach(e=>io.observe(e))}
window.addEventListener("DOMContentLoaded",()=>{initWheel();initExam();initFullscreen();initReveal()});
})();