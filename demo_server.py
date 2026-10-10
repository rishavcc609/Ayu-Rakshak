"""Zero-install local preview API.

The production-shaped API lives in app/main.py (FastAPI + SQLAlchemy). This
stdlib server exists only so reviewers can exercise the complete UI without
Docker or installing Python packages.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta
import csv, hashlib, io, json, uuid

USERS={
 "admin@demo.ayurakshak.in":("Admin","Super Admin"),
 "coordinator@demo.ayurakshak.in":("Ananya Rao","Clinical Research Coordinator"),
 "investigator@demo.ayurakshak.in":("Dr. Meera Iyer","Principal Investigator"),
 "safety@demo.ayurakshak.in":("Dr. Kabir Sen","Pharmacovigilance/Safety Officer"),
 "auditor@demo.ayurakshak.in":("Nisha Verma","Auditor")}
USERS["user@demo.ayurakshak.in"]=("Arjun Sharma","User")
TRIALS=[{"id":"t1","trial_id":"AYU-TRIAL-001","protocol_id":"AR-ASH-01","title":"Ashwagandha Sleep Quality Study","sponsor":"All India Institute of Ayurveda","therapeutic_area":"Sleep health","phase":"Exploratory","current_enrollment":76,"target_sample_size":120,"status":"Active"},{"id":"t2","trial_id":"AYU-TRIAL-002","protocol_id":"AR-OA-02","title":"Ayurvedic Support in Knee Osteoarthritis","sponsor":"All India Institute of Ayurveda","therapeutic_area":"Musculoskeletal","phase":"Exploratory","current_enrollment":49,"target_sample_size":90,"status":"Active"},{"id":"t3","trial_id":"AYU-TRIAL-003","protocol_id":"AR-MET-03","title":"Integrative Metabolic Wellness Study","sponsor":"All India Institute of Ayurveda","therapeutic_area":"Metabolic health","phase":"Exploratory","current_enrollment":25,"target_sample_size":110,"status":"Active"}]
SITES=[{"id":f"site-{i+1}","site_id":f"SITE-{i+1:03}","trial_id":f"t{i%3+1}","name":f"Ayurveda Research Centre {i+1}","principal_investigator":f"Dr. Investigator {i+1}","location":["New Delhi","Jaipur","Lucknow","Pune","Bengaluru","Bhopal","Dehradun","Varanasi"][i],"ethics_status":"Approved","enrollment":12+i*2,"performance_score":92-i*2,"risk_score":18+i*7} for i in range(8)]
RISKS=[{"id":f"risk-{i}","entity_id":f"site-{i%8+1}","score":82-i*5,"level":"Critical" if i<2 else "High" if i<7 else "Moderate","factors":{"late_visits":max(4,20-i),"missing_data":max(3,18-i),"protocol_deviations":max(2,15-i),"query_backlog":10},"evidence":{"source":"Synthetic operational signals"},"recommendation":"Prioritize human review and verify outstanding safety, protocol and data-quality evidence.","status":"Open" if i%3 else "Resolved"} for i in range(10)]
COMPLIANCE=[{"id":f"c-{i}","title":f"Synthetic compliance task {i+1}","category":["Ethics approval","Training","Document expiry","Monitoring","CAPA"][i%5],"due_date":str((datetime.now()-timedelta(days=7-i)).date()),"owner":["Ananya Rao","Dr. Meera Iyer","Nisha Verma"][i%3],"evidence":"Synthetic evidence reference","status":"Overdue" if i<7 else "Due Soon" if i<12 else "Complete"} for i in range(18)]
AUDIT=[]
EXTRA_VISITS=[]
EXTRA_AES=[]
def audit(action,resource,user="demo@local",rid=None):
 prev=AUDIT[0]["entry_hash"] if AUDIT else "GENESIS"; stamp=datetime.now(timezone.utc).isoformat(); h=hashlib.sha256(f"{prev}{action}{resource}{rid}{stamp}".encode()).hexdigest()
 AUDIT.insert(0,{"id":str(uuid.uuid4()),"action":action,"resource":resource,"user_email":user,"role":"Demo user","entry_hash":h,"timestamp":stamp})
for i in range(40): audit(["CREATE","UPDATE","LOGIN","EXPORT","VIEW"][i%5],["trial","site","subject","visit","risk_event"][i%5])
def subjects(): return [{"id":f"sub-{i}","subject_id":f"SITE-{i%8+1:03}-SUB-{i+1:04}","trial_id":f"t{i%3+1}","site_id":f"site-{i%8+1}","screening_status":"Eligible","enrollment_status":"Enrolled","visit_status":"Due soon" if i%7==0 else "On schedule","risk_status":"Moderate" if i%6==0 else "Low"} for i in range(30)]
def visits(): return [{"id":f"visit-{i}","subject_id":f"sub-{i%30}","visit_type":["Screening","Baseline","Visit 1","Visit 2","Follow-up"][i%5],"scheduled_date":str((datetime.now()+timedelta(days=i-12)).date()),"actual_date":str((datetime.now()+timedelta(days=i-12)).date()) if i<12 else None,"status":"Completed" if i<12 else "Overdue" if i<15 else "Scheduled","investigator":f"Dr. Investigator {i%8+1}"} for i in range(36)]
def adverse(): return EXTRA_AES + [{"id":f"ae-{i}","ae_id":f"AE-{i+1:04}","subject_id":f"sub-{i}","event":["Headache","Nausea","Skin irritation","Dizziness"][i%4],"severity":["Mild","Moderate","Severe"][i%3],"seriousness":"Serious" if i%9==0 else "Non-serious","relatedness":"Pending human assessment","reporting_status":"Open" if i%4==0 else "Resolved"} for i in range(18)]
class API(BaseHTTPRequestHandler):
 def end_headers(self):
  self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type, X-Request-ID"); self.send_header("Access-Control-Allow-Methods","GET, POST, PATCH, PUT, DELETE, OPTIONS"); self.send_header("X-Request-ID",str(uuid.uuid4())); self.send_header("X-Content-Type-Options","nosniff"); super().end_headers()
 def do_OPTIONS(self): self.send_response(204); self.end_headers()
 def body(self):
  n=int(self.headers.get("Content-Length",0)); return json.loads(self.rfile.read(n) or b"{}")
 def send_json(self,data,code=200):
  raw=json.dumps(data,default=str).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
 def do_POST(self):
  path=urlparse(self.path).path; data=self.body()
  if path=="/api/v1/auth/login":
   found=USERS.get(data.get("email",""));
   if not found or data.get("password")!="Demo@123": return self.send_json({"success":False,"error":{"code":"INVALID_CREDENTIALS","message":"Email or password is incorrect","details":[]}},401)
   name,role=found; audit("LOGIN","session",data["email"]); return self.send_json({"access_token":"preview-token","refresh_token":"preview-refresh","token_type":"bearer","user":{"id":str(uuid.uuid4()),"name":name,"email":data["email"],"role":role}})
  if path=="/api/v1/trials":
   row={"id":str(uuid.uuid4()),"current_enrollment":0,**data}; TRIALS.insert(0,row); audit("CREATE","trial",rid=row["id"]); return self.send_json(row,201)
  if path=="/api/v1/visits":
   row={"id":str(uuid.uuid4()),"actual_date":None,**data}; EXTRA_VISITS.insert(0,row); audit("CREATE","visit",rid=row["id"]); return self.send_json(row,201)
  if path=="/api/v1/compliance":
   row={"id":str(uuid.uuid4()),**data}; COMPLIANCE.insert(0,row); audit("CREATE","compliance_item",rid=row["id"]); return self.send_json(row,201)
  if path=="/api/v1/adverse-events":
   row={"id":str(uuid.uuid4()),**data}; EXTRA_AES.insert(0,row); audit("CREATE","adverse_event",rid=row["id"])
   score=78 if row.get("seriousness")=="Serious" else 58; risk={"id":str(uuid.uuid4()),"entity_id":row["id"],"score":score,"level":"Critical" if score>=75 else "High","factors":{"safety_reporting_delay":17,"missing_data":18,"clinical_review_pending":23},"evidence":{"adverse_event":row["ae_id"]},"recommendation":"Prioritize qualified safety review, verify report completeness and document the human assessment.","status":"Open"}; RISKS.insert(0,risk); audit("CREATE","risk_event",rid=risk["id"]); return self.send_json(row,201)
  return self.send_json({"success":False,"error":{"code":"NOT_IMPLEMENTED","message":"This preview action is not available","details":[]}},404)
 def do_PATCH(self):
  path=urlparse(self.path).path; data=self.body()
  if path.startswith("/api/v1/risk/"):
   rid=path.rsplit("/",1)[-1]; row=next((x for x in RISKS if x["id"]==rid),None)
   if not row:return self.send_json({"success":False,"error":{"code":"NOT_FOUND","message":"Risk not found","details":[]}},404)
   row.update({k:v for k,v in data.items() if k in {"status","assigned_to","resolution"}}); audit("UPDATE","risk_event",rid=rid); return self.send_json(row)
  return self.send_json({"success":False,"error":{"code":"NOT_IMPLEMENTED","message":"This preview action is not available","details":[]}},404)
 def do_GET(self):
  parsed=urlparse(self.path); path=parsed.path
  if path=="/health": return self.send_json({"status":"ok","mode":"zero-install-preview"})
  if path=="/api/v1/dashboard": return self.send_json({"active_trials":len([t for t in TRIALS if t["status"]=="Active"]),"total_sites":8,"active_subjects":145,"upcoming_visits":34,"open_tasks":12,"open_safety_events":8,"high_risk_items":6,"protocol_deviations":14,"enrollment":{"planned":320,"screened":162,"enrolled":150,"active":145,"completed":3,"withdrawn":2}})
  if path=="/api/v1/search":
   q=parse_qs(parsed.query).get("q",[""])[0].strip().lower()
   results=[]
   if len(q)>=2:
    results += [{"type":"Trial","id":x["id"],"title":x["title"],"subtitle":x["protocol_id"],"context":x["therapeutic_area"],"recommendation":"Open the trial workspace and review current enrollment, sites, visits and oversight signals.","url":f"/app/trials/{x['id']}"} for x in TRIALS if q in x["title"].lower() or q in x["trial_id"].lower() or q in x["protocol_id"].lower()]
    results += [{"type":"Site","id":x["id"],"title":x["name"],"subtitle":x["site_id"]+" · "+x["location"],"context":f"Performance {x['performance_score']}% · Risk {x['risk_score']}/100","recommendation":"Review site enrollment, data completeness and outstanding operational signals with the assigned monitor.","url":"/app/sites"} for x in SITES if q in x["name"].lower() or q in x["site_id"].lower() or q in x["location"].lower()]
    results += [{"type":"Therapeutic area","id":x["id"],"title":x["therapeutic_area"],"subtitle":x["title"],"context":"Study context only; not a diagnosis or treatment recommendation.","recommendation":"Review the associated protocol and aggregate trial results. A qualified clinician must interpret clinical meaning.","url":f"/app/trials/{x['id']}"} for x in TRIALS if q in x["therapeutic_area"].lower()]
    seen=set()
    for x in adverse():
     if q in x["event"].lower() and x["event"] not in seen:
      seen.add(x["event"]); results.append({"type":"Reported effect","id":x["id"],"title":x["event"],"subtitle":x["severity"]+" · "+x["seriousness"],"context":"Synthetic adverse-event report · Causality pending human assessment","recommendation":"Open the safety queue, verify report completeness and timing, and route the case to a qualified safety reviewer. Do not infer causality from this search result.","url":"/app/safety"})
   return self.send_json({"query":q,"items":results[:10],"total":len(results[:10])})
  if path=="/api/v1/trials": return self.send_json({"items":TRIALS,"pagination":{"page":1,"page_size":20,"total":len(TRIALS),"pages":1}})
  routes={"/api/v1/sites":SITES,"/api/v1/visits":EXTRA_VISITS+visits(),"/api/v1/adverse-events":adverse(),"/api/v1/risk":RISKS,"/api/v1/compliance":COMPLIANCE,"/api/v1/notifications":[{"id":"n1","title":"Critical risk requires review","message":"Site 002 has overdue visits and safety reporting delays.","state":"Unread"},{"id":"n2","title":"Visit due tomorrow","message":"A synthetic follow-up visit is due within 24 hours.","state":"Unread"},{"id":"n3","title":"Document expiry approaching","message":"Ethics approval evidence expires in 14 days.","state":"Acknowledged"}],"/api/v1/audit":AUDIT,"/api/v1/cdisc":[{"id":"m1","source_field":"Participant ID","standard":"SDTM","target_domain":"DM","target_variable":"USUBJID","validation_status":"Valid"},{"id":"m2","source_field":"Visit Date","standard":"SDTM","target_domain":"SV","target_variable":"SVSTDTC","validation_status":"Valid"},{"id":"m3","source_field":"Adverse Event Term","standard":"SDTM","target_domain":"AE","target_variable":"AETERM","validation_status":"Valid"}]}
  if path in routes:return self.send_json(routes[path])
  if path.startswith("/api/v1/fhir/"): return self.send_json({"resourceType":"Bundle","type":"searchset","total":1,"entry":[{"resource":{"resourceType":"Organization","id":"aiia-demo","name":"Synthetic AIIA Demo Organization"}}]})
  if path=="/api/v1/reports/export":
   raw=("Report,Generated at,Synthetic data only\nTrial Status,"+datetime.now(timezone.utc).isoformat()+",true\n").encode(); self.send_response(200); self.send_header("Content-Type","text/csv"); self.send_header("Content-Disposition","attachment; filename=ayurakshak-report.csv"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); return self.wfile.write(raw)
  return self.send_json({"success":False,"error":{"code":"NOT_FOUND","message":"Endpoint not found","details":[]}},404)
 def log_message(self,fmt,*args): print(json.dumps({"time":datetime.now(timezone.utc).isoformat(),"request":fmt%args}))
if __name__=="__main__":
 print("AYU RAKSHAK preview API: http://127.0.0.1:8000"); ThreadingHTTPServer(("127.0.0.1",8000),API).serve_forever()
