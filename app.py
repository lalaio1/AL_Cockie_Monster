from flask import Flask ,request ,jsonify ,send_file 
from flask_cors import CORS 
from flask_swagger_ui import get_swaggerui_blueprint 
from flask_limiter import Limiter 
from flask_limiter .util import get_remote_address 
import os 
import json 
import tempfile 
import time 
import threading 
from datetime import datetime 
from models .cookie import Cookie 
from services .cookie_parser import CookieParser 
from services .ip_analyzer import IPAnalyzer 
from services .security_analyzer import SecurityAnalyzer 
from services .filter_service import FilterService 
from utils .validators import CookieValidator 
from utils .logger import log_manager 
from backup_manager import BackupManager 

logger =log_manager .get_logger ('app')

app =Flask (__name__ )

CORS (app ,
resources ={r"/api/*":{
"origins":["http://localhost:3000","http://localhost:5000","http://localhost"],
"methods":["GET","POST","OPTIONS"],
"allow_headers":["Content-Type"],
"max_age":3600 
}},
supports_credentials =True ,
expose_headers =["Content-Type"])

@app .after_request 
def set_security_headers (response ):
    response .headers ['X-Content-Type-Options']='nosniff'
    response .headers ['X-Frame-Options']='DENY'
    response .headers ['X-XSS-Protection']='1; mode=block'
    response .headers ['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    response .headers ['Content-Security-Policy']="default-src 'self'; script-src 'self'"
    response .headers ['Referrer-Policy']='strict-origin-when-cross-origin'
    response .headers ['Permissions-Policy']='geolocation=(), microphone=(), camera=()'
    return response 

limiter =Limiter (
app =app ,
key_func =get_remote_address ,
default_limits =["200 per day","50 per hour"],
storage_uri ="memory://"
)

app .config .setdefault ('RATELIMIT_HEADERS_ENABLED',True )

def _is_local_request ():
    try :
        addr =request .remote_addr or ''
        if addr .startswith ('127.')or addr =='::1'or addr =='localhost':
            return True 
        if request .headers .get ('X-Internal-Client')=='1':
            return True 
    except Exception :
        pass 
    return False 

limiter .request_filter (_is_local_request )

SWAGGER_URL ='/api/docs'
API_URL ='/static/swagger.json'
swaggerui_blueprint =get_swaggerui_blueprint (
SWAGGER_URL ,
API_URL ,
config ={'app_name':"Cockie Monster API"}
)
app .register_blueprint (swaggerui_blueprint ,url_prefix =SWAGGER_URL )

cookie_parser =CookieParser ()
ip_analyzer =IPAnalyzer ()
security_analyzer =SecurityAnalyzer ()
filter_service =FilterService ()
validator =CookieValidator ()
backup_manager =BackupManager ()

logger .info ('Application initialized with all services loaded')

class FileChangeMonitor :
    def __init__ (self ,backup_manager ,project_root ):
        self .backup_manager =backup_manager 
        self .project_root =project_root 
        self .file_hashes ={}
        self .backup_lock =threading .Lock ()
        self .is_monitoring =False 
        self .excluded_dirs ={'venv','__pycache__','backups','bak','.git'}
        self .backup_cooldown =300 
        self .last_backup_time =None 

        self ._scan_initial_files ()

    def _scan_initial_files (self ):
        import hashlib 

        for root ,dirs ,files in os .walk (self .project_root ):
            dirs [:]=[d for d in dirs if d not in self .excluded_dirs ]

            for file in files :
                if file .endswith (('.py','.json','.txt','.md','.bat','.ps1')):
                    file_path =os .path .join (root ,file )
                    try :
                        with open (file_path ,'rb')as f :
                            self .file_hashes [file_path ]=hashlib .md5 (f .read ()).hexdigest ()
                    except Exception as e :
                        logger .debug (f'Could not hash {file_path }: {str (e )}')

    def check_changes (self ):
        import hashlib 

        changes_detected =[]

        for root ,dirs ,files in os .walk (self .project_root ):
            dirs [:]=[d for d in dirs if d not in self .excluded_dirs ]

            for file in files :
                if file .endswith (('.py','.json','.txt','.md','.bat','.ps1')):
                    file_path =os .path .join (root ,file )

                    try :
                        with open (file_path ,'rb')as f :
                            current_hash =hashlib .md5 (f .read ()).hexdigest ()

                        previous_hash =self .file_hashes .get (file_path ,None )

                        if previous_hash is None or previous_hash !=current_hash :
                            changes_detected .append (file_path )
                            self .file_hashes [file_path ]=current_hash 

                            rel_path =os .path .relpath (file_path ,self .project_root )
                            if previous_hash is None :
                                logger .info (f'[FileMonitor] New file detected: {rel_path }')
                            else :
                                logger .info (f'[FileMonitor] Change detected: {rel_path }')

                    except Exception as e :
                        logger .debug (f'Could not check {file_path }: {str (e )}')

        if changes_detected :
            current_time =time .time ()
            if self .last_backup_time is None or (current_time -self .last_backup_time )>=self .backup_cooldown :
                self ._trigger_backup (changes_detected )
                self .last_backup_time =current_time 
            else :
                remaining =self .backup_cooldown -(current_time -self .last_backup_time )
                logger .debug (f'[FileMonitor] Backup cooldown active. Remaining: {remaining :.0f}s')

    def _trigger_backup (self ,changes ):
        def backup_thread ():
            with self .backup_lock :
                try :
                    timestamp =datetime .now ().strftime ('%Y%m%d_%H%M%S')
                    backup_name =f'cockie_monster_auto_backup_{timestamp }.zip'

                    logger .info (f'[FileMonitor] Backup triggered - {len (changes )} files changed')
                    for change in changes [:5 ]:
                        rel_path =os .path .relpath (change ,self .project_root )
                        logger .info (f'[FileMonitor]   Changed: {rel_path }')
                    if len (changes )>5 :
                        logger .info (f'[FileMonitor]   ... and {len (changes )-5 } more files')

                    backup_path =self .backup_manager .create_backup (backup_name )
                    logger .info (f'[FileMonitor] Auto backup completed: {os .path .basename (backup_path )}')


                except Exception as e :
                    logger .error (f'[FileMonitor] Backup failed: {str (e )}')

        thread =threading .Thread (target =backup_thread ,daemon =True )
        thread .start ()

    def start_monitoring (self ,interval =30 ):
        def monitor_loop ():
            logger .info (f'[FileMonitor] Started monitoring (check interval: {interval }s)')

            while self .is_monitoring :
                try :
                    self .check_changes ()
                    time .sleep (interval )
                except Exception as e :
                    logger .error (f'[FileMonitor] Monitor error: {str (e )}')
                    time .sleep (interval )

        self .is_monitoring =True 
        thread =threading .Thread (target =monitor_loop ,daemon =True )
        thread .start ()
        logger .info ('[FileMonitor] File monitoring thread started')

    def stop_monitoring (self ):
        self .is_monitoring =False 
        logger .info ('[FileMonitor] File monitoring stopped')

file_monitor =FileChangeMonitor (backup_manager ,app .root_path )

file_monitor .start_monitoring (interval =30 )

def assess_cookie_risk (cookie :Cookie )->dict :
    risk_score =0 
    vulnerabilities =[]

    if not cookie .secure :
        risk_score +=30 
        vulnerabilities .append ('Not transmitted over HTTPS')

    if not cookie .http_only :
        risk_score +=25 
        vulnerabilities .append ('Accessible to JavaScript (XSS risk)')

    if not cookie .same_site :
        risk_score +=20 
        vulnerabilities .append ('No SameSite attribute (CSRF risk)')

    if not cookie .is_session and cookie .expires >0 :
        from datetime import datetime 
        expiration =datetime .fromtimestamp (cookie .expires )
        if (expiration -datetime .now ()).days >365 :
            risk_score +=15 
            vulnerabilities .append ('Very long expiration period')

    if risk_score >=70 :
        risk_level ='critical'
    elif risk_score >=50 :
        risk_level ='high'
    elif risk_score >=25 :
        risk_level ='medium'
    else :
        risk_level ='low'

    return {
    'risk_score':min (risk_score ,100 ),
    'risk_level':risk_level ,
    'vulnerabilities':vulnerabilities 
    }


@app .route ('/api/analyze',methods =['POST'])
@limiter .limit ("10 per minute")
def analyze_cookies ():
    start_time =time .time ()
    logger .debug (f'Analyze request received from {request .remote_addr }')
    try :
        if 'file'in request .files :
            file =request .files ['file']
            logger .debug (f'Processing file upload: {file .filename }')
            content =file .read ().decode ('utf-8')
        elif request .is_json and 'cookies_text'in request .json :
            content =request .json ['cookies_text']
            logger .debug (f'Processing text input with {len (content )} chars')
        else :
            logger .warning ('Analyze request missing required data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Parsed {len (cookies )} cookies from input')

        analysis ={
        'total_cookies':len (cookies ),
        'cookies':[],
        'security_analysis':{},
        'ip_analysis':[],
        'filters_available':filter_service .get_available_filters ()
        }

        session_cookies_count =0 
        persistent_cookies_count =0 

        for i ,cookie in enumerate (cookies ):
            cookie_dict =cookie .to_dict ()

            cookie_dict ['metadata']={
            'is_session':cookie .is_session ,
            'expiration_date':cookie .expiration_date ,
            'has_samesite':cookie .same_site ,
            'is_secure':cookie .secure ,
            'is_http_only':cookie .http_only 
            }

            if cookie .is_session :
                session_cookies_count +=1 
            else :
                persistent_cookies_count +=1 

            security_info =security_analyzer .analyze (cookie )
            cookie_dict ['security']=security_info 

            risk_assessment =assess_cookie_risk (cookie )
            cookie_dict ['risk_assessment']=risk_assessment 
            logger .debug (f'Cookie {i +1 }/{len (cookies )}: {cookie .name } security analyzed')

            if cookie .name =='MSCC':
                ip_analysis =ip_analyzer .analyze (cookie .value )
                cookie_dict ['ip_analysis']=ip_analysis 
                analysis ['ip_analysis'].append (ip_analysis )
                logger .debug (f'IP analysis completed for MSCC cookie: {ip_analysis .get ("country","Unknown")}')

            analysis ['cookies'].append (cookie_dict )

        analysis ['statistics']={
        'session_cookies':session_cookies_count ,
        'persistent_cookies':persistent_cookies_count ,
        'secure_cookies':sum (1 for c in cookies if c .secure ),
        'http_only_cookies':sum (1 for c in cookies if c .http_only ),
        'samesite_cookies':sum (1 for c in cookies if c .same_site )
        }

        analysis ['security_analysis']=security_analyzer .overall_analysis (cookies )

        elapsed =time .time ()-start_time 
        logger .info (f'Analyze completed: {len (cookies )} cookies in {elapsed :.2f}s')
        return jsonify (analysis )

    except Exception as e :
        logger .error (f'Error in analyze: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/filter',methods =['POST'])
@limiter .limit ("10 per minute")
def filter_cookies ():
    start_time =time .time ()
    logger .debug (f'Filter request from {request .remote_addr }')
    try :
        if not request .is_json and 'file'not in request .files :
            logger .warning ('Filter request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json or multipart/form-data'}),415 

        data =request .json if request .is_json else {}

        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif 'cookies_text'in data :
            content =data ['cookies_text']
        else :
            logger .warning ('Filter request missing cookies data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Parsed {len (cookies )} cookies for filtering')

        filter_criteria =data .get ('filters',{})
        logger .debug (f'Applying filters: {list (filter_criteria .keys ())}')

        filtered_cookies =filter_service .apply_filters (cookies ,filter_criteria )

        result ={
        'original_count':len (cookies ),
        'filtered_count':len (filtered_cookies ),
        'removed_count':len (cookies )-len (filtered_cookies ),
        'filters_applied':filter_criteria ,
        'cookies':[c .to_dict ()for c in filtered_cookies ]
        }

        elapsed =time .time ()-start_time 
        logger .info (f'Filter completed: {len (cookies )} → {len (filtered_cookies )} cookies in {elapsed :.2f}s')
        return jsonify (result )

    except Exception as e :
        logger .error (f'Error in filter: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/risk-assessment',methods =['POST'])
@limiter .limit ("10 per minute")
def assess_cookies_risk ():
    start_time =time .time ()
    logger .debug (f'Risk assessment request from {request .remote_addr }')
    try :
        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif request .is_json and 'cookies_text'in request .json :
            content =request .json ['cookies_text']
        else :
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Parsed {len (cookies )} cookies for risk assessment')

        critical_cookies =[]
        high_risk_cookies =[]
        medium_risk_cookies =[]

        risk_details =[]

        for cookie in cookies :
            risk_info =assess_cookie_risk (cookie )

            cookie_risk ={
            'name':cookie .name ,
            'domain':cookie .domain ,
            'risk_assessment':risk_info ,
            'properties':{
            'is_session':cookie .is_session ,
            'secure':cookie .secure ,
            'http_only':cookie .http_only ,
            'same_site':cookie .same_site ,
            'expiration_date':cookie .expiration_date 
            }
            }

            if risk_info ['risk_level']=='critical':
                critical_cookies .append (cookie_risk )
            elif risk_info ['risk_level']=='high':
                high_risk_cookies .append (cookie_risk )
            elif risk_info ['risk_level']=='medium':
                medium_risk_cookies .append (cookie_risk )

            risk_details .append (cookie_risk )

        result ={
        'total_cookies':len (cookies ),
        'risk_summary':{
        'critical':len (critical_cookies ),
        'high':len (high_risk_cookies ),
        'medium':len (medium_risk_cookies ),
        'low':len (cookies )-len (critical_cookies )-len (high_risk_cookies )-len (medium_risk_cookies )
        },
        'critical_cookies':critical_cookies ,
        'high_risk_cookies':high_risk_cookies ,
        'medium_risk_cookies':medium_risk_cookies ,
        'all_assessments':risk_details 
        }

        elapsed =time .time ()-start_time 
        logger .info (f'Risk assessment completed: {len (critical_cookies )} critical, {len (high_risk_cookies )} high-risk in {elapsed :.2f}s')
        return jsonify (result )

    except Exception as e :
        logger .error (f'Error in risk assessment: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/export',methods =['POST'])
@limiter .limit ("10 per minute")
def export_cookies ():
    start_time =time .time ()
    logger .debug (f'Export request from {request .remote_addr }')
    try :
        if not request .is_json and 'file'not in request .files :
            logger .warning ('Export request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json or multipart/form-data'}),415 
        data =request .json if request .is_json else {}
        format_type =data .get ('format','netscape')
        logger .debug (f'Export format requested: {format_type }')

        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif 'cookies_text'in data :
            content =data ['cookies_text']
        else :
            logger .warning ('Export request missing cookies data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Parsed {len (cookies )} cookies for export')

        if 'filters'in data :
            original_count =len (cookies )
            cookies =filter_service .apply_filters (cookies ,data ['filters'])
            logger .debug (f'Applied filters: {original_count } → {len (cookies )} cookies')

        if format_type =='netscape':
            output =cookie_parser .export_netscape (cookies )
            filename ='filtered_cookies.txt'
        elif format_type =='json':
            output =json .dumps ([c .to_dict ()for c in cookies ],indent =2 )
            filename ='filtered_cookies.json'
        elif format_type =='csv':
            output =cookie_parser .export_csv (cookies )
            filename ='filtered_cookies.csv'
        else :
            logger .error (f'Invalid format type: {format_type }')
            return jsonify ({'error':'Invalid format type'}),400 

        with tempfile .NamedTemporaryFile (mode ='w',delete =False ,suffix =f'.{format_type }')as f :
            f .write (output )
            temp_path =f .name 

        elapsed =time .time ()-start_time 
        logger .info (f'Export completed: {len (cookies )} cookies as {format_type } in {elapsed :.2f}s')
        return send_file (temp_path ,as_attachment =True ,download_name =filename )

    except Exception as e :
        logger .error (f'Error in export: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/ip-info',methods =['POST'])
@limiter .limit ("10 per minute")
def get_ip_info ():
    logger .debug (f'IP-info request from {request .remote_addr }')
    try :
        if not request .is_json :
            logger .warning ('IP-info request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json'}),415 

        data =request .json 
        ips =data .get ('ips',[])

        if not ips :
            logger .warning ('IP-info request missing IPs')
            return jsonify ({'error':'No IPs provided'}),400 

        results =[]
        for ip in ips :
            info =ip_analyzer .analyze (ip )
            results .append (info )

        logger .info (f'IP-info: {len (results )} IPs analyzed')
        return jsonify ({
        'total_ips':len (results ),
        'ips':results 
        })

    except Exception as e :
        logger .error (f'Error in ip-info: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 


@app .route ('/api/extract-ips',methods =['POST'])
@limiter .limit ("10 per minute")
def extract_ips ():
    start_time =time .time ()
    logger .debug (f'Extract-ips request from {request .remote_addr }')
    try :
        if not request .is_json and 'file'not in request .files :
            logger .warning ('Extract-ips request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json or multipart/form-data'}),415 

        data =request .json if request .is_json else {}

        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif 'cookies_text'in data :
            content =data ['cookies_text']
        else :
            logger .warning ('Extract-ips request missing cookies data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .debug (f'Parsed {len (cookies )} cookies for IP extraction')

        import re 
        ip_pattern =re .compile (r'(?:\d{1,3}\.){3}\d{1,3}')
        ips =set ()
        for c in cookies :
            for field in (c .name ,c .value ,c .domain ):
                if field :
                    for m in ip_pattern .findall (str (field )):
                        ips .add (m )

        logger .debug (f'Extracted {len (ips )} unique IPs from cookies')
        results =[]
        for i ,ip in enumerate (sorted (ips )):
            results .append (ip_analyzer .analyze (ip ))
            logger .debug (f'IP {i +1 }/{len (ips )}: {ip } analyzed')

        elapsed =time .time ()-start_time 
        logger .info (f'Extract-ips completed: {len (results )} IPs extracted and analyzed in {elapsed :.2f}s')
        return jsonify ({'total_ips':len (results ),'ips':results })

    except Exception as e :
        logger .error (f'Error in extract-ips: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/security-check',methods =['POST'])
@limiter .limit ("10 per minute")
def security_check ():
    start_time =time .time ()
    logger .debug (f'Security-check request from {request .remote_addr }')
    try :
        if not request .is_json and 'file'not in request .files :
            logger .warning ('Security-check request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json or multipart/form-data'}),415 

        data =request .json if request .is_json else {}

        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif 'cookies_text'in data :
            content =data ['cookies_text']
        else :
            logger .warning ('Security-check request missing cookies data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Parsing {len (cookies )} cookies for security analysis')

        security_report =security_analyzer .generate_report (cookies )

        elapsed =time .time ()-start_time 
        logger .info (f'Security-check completed: {len (cookies )} cookies analyzed in {elapsed :.2f}s')
        return jsonify (security_report )

    except Exception as e :
        logger .error (f'Error in security-check: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/validate',methods =['POST'])
@limiter .limit ("20 per minute")
def validate_cookies ():
    start_time =time .time ()
    logger .debug (f'Validate request from {request .remote_addr }')
    try :
        if not request .is_json and 'file'not in request .files :
            logger .warning ('Validate request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json or multipart/form-data'}),415 

        data =request .json if request .is_json else {}

        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif 'cookies_text'in data :
            content =data ['cookies_text']
        else :
            logger .warning ('Validate request missing cookies data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Validating {len (cookies )} cookies')

        validation_results =[]
        for i ,cookie in enumerate (cookies ):
            result =validator .validate (cookie )
            validation_results .append ({
            'cookie':cookie .to_dict (),
            'valid':result ['valid'],
            'issues':result .get ('issues',[]),
            'warnings':result .get ('warnings',[])
            })
            if result ['valid']:
                logger .debug (f'Cookie {i +1 }/{len (cookies )}: {cookie .name } is VALID')
            else :
                logger .debug (f'Cookie {i +1 }/{len (cookies )}: {cookie .name } has issues')

        valid_count =sum (1 for r in validation_results if r ['valid'])
        elapsed =time .time ()-start_time 
        logger .info (f'Validate completed: {valid_count }/{len (cookies )} valid in {elapsed :.2f}s')

        return jsonify ({
        'total_cookies':len (cookies ),
        'valid_count':valid_count ,
        'invalid_count':len (cookies )-valid_count ,
        'validation_results':validation_results 
        })

    except Exception as e :
        logger .error (f'Error in validate: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .route ('/api/filters',methods =['GET'])
@limiter .limit ("30 per minute")
def get_filters ():
    logger .debug ('Filters list requested')
    return jsonify (filter_service .get_available_filters ())

@app .route ('/api/stats',methods =['POST'])
@limiter .limit ("10 per minute")
def get_stats ():
    start_time =time .time ()
    logger .debug (f'Stats request from {request .remote_addr }')
    try :
        if not request .is_json and 'file'not in request .files :
            logger .warning ('Stats request with invalid content type')
            return jsonify ({'error':'Content-Type must be application/json or multipart/form-data'}),415 

        data =request .json if request .is_json else {}

        if 'file'in request .files :
            file =request .files ['file']
            content =file .read ().decode ('utf-8')
        elif 'cookies_text'in data :
            content =data ['cookies_text']
        else :
            logger .warning ('Stats request missing cookies data')
            return jsonify ({'error':'No cookies data provided'}),400 

        cookies =cookie_parser .parse (content )
        logger .info (f'Calculating stats for {len (cookies )} cookies')

        stats ={
        'total_cookies':len (cookies ),
        'by_domain':{},
        'by_path':{},
        'by_security':{
        'secure':0 ,
        'http_only':0 ,
        'same_site':0 
        },
        'by_expiration':{
        'session':0 ,
        'persistent':0 
        },
        'security_cookies':0 ,
        'tracking_cookies':0 
        }

        for cookie in cookies :
            domain =cookie .domain 
            stats ['by_domain'][domain ]=stats ['by_domain'].get (domain ,0 )+1 

            path =cookie .path 
            stats ['by_path'][path ]=stats ['by_path'].get (path ,0 )+1 

            if cookie .secure :
                stats ['by_security']['secure']+=1 
            if cookie .http_only :
                stats ['by_security']['http_only']+=1 
            if cookie .same_site :
                stats ['by_security']['same_site']+=1 

            if cookie .expires ==0 :
                stats ['by_expiration']['session']+=1 
            else :
                stats ['by_expiration']['persistent']+=1 

            if security_analyzer .is_security_cookie (cookie ):
                stats ['security_cookies']+=1 

            if security_analyzer .is_tracking_cookie (cookie ):
                stats ['tracking_cookies']+=1 

        elapsed =time .time ()-start_time 
        logger .info (f'Stats completed: {stats ["security_cookies"]} security, {stats ["tracking_cookies"]} tracking in {elapsed :.2f}s')
        return jsonify (stats )

    except Exception as e :
        logger .error (f'Error in stats: {str (e )}',exc_info =True )
        return jsonify ({'error':str (e )}),500 

@app .errorhandler (400 )
def bad_request (error ):
    logger .warning (f'Bad request: {str (error )}')
    return jsonify ({'error':'Bad request'}),400 

@app .errorhandler (404 )
def not_found (error ):
    logger .warning (f'Not found: {request .path }')
    return jsonify ({'error':'Endpoint not found'}),404 

@app .errorhandler (429 )
def rate_limit_handler (e ):
    logger .warning (f'Rate limit exceeded from {request .remote_addr }')
    return jsonify ({'error':'Rate limit exceeded. Too many requests.'}),429 

@app .errorhandler (500 )
def internal_error (error ):
    logger .error (f'Internal server error: {str (error )}',exc_info =True )
    return jsonify ({'error':'Internal server error'}),500 

if __name__ =='__main__':
    import atexit 

    def shutdown_handler ():
        logger .info ('[FileMonitor] Shutting down file monitor...')
        file_monitor .stop_monitoring ()
        logger .info ('[FileMonitor] File monitor stopped')

    atexit .register (shutdown_handler )

    logger .info ('='*50 )
    logger .info ('Starting Cockie Monster API Server')
    logger .info (f'Debug Mode: {os .getenv ("FLASK_DEBUG","False")}')
    logger .info (f'Environment: {os .getenv ("FLASK_ENV","production")}')
    logger .info (f'Automatic backups: ENABLED (cooldown: {file_monitor .backup_cooldown }s)')
    logger .info ('='*50 )
    app .run (debug =False )
