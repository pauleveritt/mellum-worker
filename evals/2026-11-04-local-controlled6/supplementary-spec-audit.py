"""Supplementary post-registration Phase 1 spec diagnostic, never model-visible.

Does not replace the four hidden checks or alter the preregistered scoring rule.
Runs only inside a private grading container. Runtime launch is bounded and reaped.
"""
import ast,json,os,re,signal,subprocess,sys,time,urllib.request
from pathlib import Path

sys.path.insert(0,str(Path.cwd()))
checks={};errors={}
def check(name,fn):
 try:checks[name]=bool(fn())
 except Exception as e:checks[name]=False;errors[name]=f'{type(e).__name__}: {e}'

from turbohtml import parse
import jinja2
loaded=[]
original=jinja2.Environment.get_template
def tracked(self,name,*args,**kw):
 loaded.append(str(name));return original(self,name,*args,**kw)
jinja2.Environment.get_template=tracked
html='';application=None
try:
 from app import app as application
 from fastapi import FastAPI
 from starlette.testclient import TestClient
 with TestClient(application) as client:
  response=client.get('/');html=response.text;status=response.status_code
 check('fastapi_app_at_root',lambda:isinstance(application,FastAPI))
 check('home_200_tagline',lambda:status==200 and 'Come in. Sit down. Tell us about your human.' in html)
except Exception as e:
 checks['fastapi_app_at_root']=checks['home_200_tagline']=False;errors['import_or_request']=f'{type(e).__name__}: {e}'
doc=parse(html)
check('shared_base_template_used',lambda:Path('templates/base.html').is_file() and 'base.html' in loaded)
check('html5_and_english',lambda:bool(re.search(r'<!doctype\s+html\s*>',html,re.I)) and (doc.select_one('html').attr('lang') or '').lower()=='en')
check('responsive_viewport',lambda:any((m.attr('name') or '').lower()=='viewport' and 'width=device-width' in (m.attr('content') or '') for m in doc.select('head meta')))
check('bootstrap5_css_head',lambda:any(re.search(r'bootstrap(?:@|/|[-.])5',(m.attr('href') or ''),re.I) and (m.attr('rel') or '').lower()=='stylesheet' for m in doc.select('head link')))
check('bootstrap5_bundle_body_end',lambda:bool(re.search(r'<script\b[^>]*src=[\'"][^\'"]*bootstrap(?:@|/|[-.])5[^\'"]*bootstrap\.bundle(?:\.min)?\.js[^\'"]*[\'"][^>]*>\s*</script>\s*</body>',html,re.I)))
check('python_favicon',lambda:any('icon' in (m.attr('rel') or '').lower() and (m.attr('href') or '')=='https://www.python.org/static/favicon.ico' for m in doc.select('head link')))
check('default_title',lambda:doc.select_one('head title').text.strip()=='AgentClinic')
check('navbar_brand_and_links',lambda:any(a.text.strip()=='AgentClinic' for a in doc.select('nav a')) and any(a.attr('href')=='/' and a.text.strip().lower()=='home' for a in doc.select('nav a')) and any(a.attr('href')=='/complaints' and a.text.strip().lower()=='complaints' for a in doc.select('nav a')))
check('welcoming_paragraph',lambda:any(p.text.strip() and 'Come in. Sit down. Tell us about your human.' not in p.text for p in doc.select('p')))
def guarded_reload():
 tree=ast.parse(Path('app.py').read_text());found=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='__name__' and any(isinstance(c,ast.Constant) and c.value=='__main__' for c in n.test.comparators):
   found.extend(x for statement in n.body for x in ast.walk(statement) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='run' and any(k.arg=='reload' and isinstance(k.value,ast.Constant) and k.value.value is True for k in x.keywords))
 return bool(found)
check('reload_under_main_guard',guarded_reload)
# Execute precisely the startup command required by the task, only in isolation.
start={'command':['uv','run','--offline','--frozen','python','app.py'],'ready':False}
log=Path('/attempt/startup.log')
with log.open('w') as stream:
 process=subprocess.Popen(start['command'],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  until=time.monotonic()+12
  while process.poll() is None and time.monotonic()<until:
   text=log.read_text();match=re.search(r'http://(?:0\.0\.0\.0|127\.0\.0\.1|localhost|\[::\]):(\d+)',text)
   if match:
    try:
     with urllib.request.urlopen(f'http://127.0.0.1:{match[1]}/',timeout=.5) as response:
      if response.status==200:start['ready']=True;break
    except OSError:pass
   time.sleep(.1)
 finally:
  start['exit_before_shutdown']=process.poll()
  try:os.killpg(process.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
  start['reaped']=process.poll() is not None
checks['required_startup_serves_home']=start['ready']
Path('/attempt/spec-result.json').write_text(json.dumps({'scope':'Supplementary post-registration spec diagnostic; original hidden grade and fixed comparison scores unchanged.','checks':checks,'passed':sum(checks.values()),'total':len(checks),'all_pass':all(checks.values()),'errors':errors,'loaded_templates':loaded,'startup':start},indent=2)+'\n')
