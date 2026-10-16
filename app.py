import os
import subprocess
from flask import Flask, request, jsonify, render_template_string
from groq import Groq

app = Flask(__name__)
MODEL = "openai/gpt-oss-20b"
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

HTML = r"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#020805">
<title>NEXUS JARVIS</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#10251a,#020504 72%);
color:#7dffad;font-family:Arial,sans-serif;min-height:100vh}
main{max-width:520px;margin:auto;padding:22px 18px;display:flex;
flex-direction:column;align-items:center;min-height:100vh}
h1{letter-spacing:9px;font-size:28px;margin:18px 0 4px;text-shadow:0 0 15px #28ff78}
.sub{font-size:11px;letter-spacing:4px;color:#5ba879}
.hud{width:245px;height:245px;margin:30px auto;display:grid;place-items:center;position:relative}
.ring{position:absolute;inset:0;border:1px solid #35ff8a;border-radius:50%;
box-shadow:0 0 22px #0c9c4b,inset 0 0 24px #0b6436;animation:spin 14s linear infinite}
.ring:before,.ring:after{content:"";position:absolute;border:1px dashed #32e97a;
border-radius:50%;inset:13px}
.ring:after{inset:29px;border-style:solid;opacity:.5}
.core{width:100px;height:100px;border-radius:50%;border:2px solid #6dffa5;
box-shadow:0 0 35px #19e765,inset 0 0 30px #15aa53;
background:radial-gradient(circle,#62ff9b33,#071b10);animation:pulse 2s infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{50%{transform:scale(1.08);box-shadow:0 0 48px #28ff78}}
.status{font-size:12px;letter-spacing:3px;margin-bottom:14px}
#chat{width:100%;flex:1;min-height:120px;max-height:32vh;overflow:auto;
border:1px solid #174b2b;border-radius:12px;padding:12px;background:#041009aa}
.msg{margin:10px 0;line-height:1.45;white-space:pre-wrap}
.you{color:#d8ffe5}.ai{color:#66ff9c}
form{display:flex;width:100%;gap:8px;margin-top:14px}
input{min-width:0;flex:1;background:#06140b;border:1px solid #287844;
border-radius:10px;padding:13px;color:#d7ffe3;font-size:16px}
button{background:#0a2a16;color:#83ffae;border:1px solid #36e978;
border-radius:10px;padding:12px;font-weight:bold}
#mic{margin:14px;font-size:16px;border-radius:50%;width:70px;height:70px}
.small{font-size:11px;color:#6b9e7c;text-align:center;margin-top:12px}
</style>
</head>
<body><main>
<h1>NEXUS</h1><div class="sub">PERSONAL AI SYSTEM</div>
<div class="hud"><div class="ring"></div><div class="core"></div></div>
<div class="status" id="status">SYSTEM ONLINE</div>
<div id="chat"><div class="msg ai">NEXUS: Olá. Estou pronto para ajudar.</div></div>
<button id="mic" type="button">🎙 FALAR</button>
<form id="form"><input id="q" placeholder="Fale ou digite..." autocomplete="off">
<button>ENVIAR</button></form>
<div class="small">GROQ AI · VOZ E TEXTO</div>
<script>
const chat=document.querySelector('#chat'), statusEl=document.querySelector('#status');
function add(who,text,cls){let d=document.createElement('div');d.className='msg '+cls;
d.textContent=who+': '+text;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
function speak(text){
if(!('speechSynthesis' in window))return;
speechSynthesis.cancel();
let limpo=text
.replace(/\*{1,3}(.*?)\*{1,3}/g,'$1')
.replace(/#{1,6}\s*/g,'')
.replace(/```[\s\S]*?```/g,'')
.replace(/[*_`~]/g,'')
.replace(/\s+/g,' ')
.trim();
let u=new SpeechSynthesisUtterance(limpo);
u.lang='pt-BR';
u.rate=1.15;
speechSynthesis.speak(u);
}
async function send(text){
if(!text.trim())return;
add('VOCÊ',text,'you');document.querySelector('#q').value='';
statusEl.textContent='PROCESSANDO...';
try{
let r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({message:text})});
let data=await r.json();if(!r.ok)throw Error(data.error||'Falha na solicitação');
add('NEXUS',data.answer,'ai');speak(data.answer);
statusEl.textContent='SYSTEM ONLINE';
}catch(e){add('ERRO',e.message,'ai');statusEl.textContent='VERIFIQUE A CONEXÃO';}
}
document.querySelector('#form').addEventListener('submit',e=>{e.preventDefault();send(document.querySelector('#q').value);});
document.querySelector('#mic').addEventListener('click',()=>{
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!SR){statusEl.textContent='DITADO NÃO DISPONÍVEL; USE O MICROFONE DO TECLADO';return;}
let rec=new SR();rec.lang='pt-BR';rec.interimResults=false;
rec.onstart=()=>statusEl.textContent='ESTOU OUVINDO...';
rec.onresult=e=>send(e.results[0][0].transcript);
rec.onerror=e=>statusEl.textContent='ERRO DE VOZ: '+e.error;
rec.onend=()=>{if(statusEl.textContent==='ESTOU OUVINDO...')statusEl.textContent='SYSTEM ONLINE';};
rec.start();
});
</script>
</main></body></html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

@app.post("/ask")
def ask():
    if not os.environ.get("GROQ_API_KEY"):
        return jsonify(error="Configure GROQ_API_KEY no Termux."), 500
    message = request.json.get("message", "").strip()
    if not message:
        return jsonify(error="Digite uma pergunta."), 400
    try:
        result = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role":"system","content":"Seu nome é NEXUS. Responda em português brasileiro, de forma clara e amigável."},
                {"role":"user","content":message}
            ],
            max_tokens=700
        )
        return jsonify(answer=result.choices[0].message.content or "Não consegui responder.")
    except Exception as e:
        return jsonify(error=str(e)), 502

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
