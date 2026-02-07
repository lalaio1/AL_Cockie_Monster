import re 
from datetime import datetime 

class SecurityAnalyzer :

    SECURITY_PATTERNS ={
    'authentication':['auth','session','token','jwt','bearer','oauth'],
    'authorization':['perm','role','access','acl'],
    'security':['secure','samesite','http_only','csrf','xsrf'],
    'tracking':['track','analytics','ad','pixel','beacon'],
    'session':['session','sid','sessionid']
    }


    SECURITY_COOKIES ={
    '__Host-','__Secure-','ASP.NET_SessionId','PHPSESSID',
    'connect.sid','express:sess','koa:sess','session',
    'auth_token','access_token','refresh_token','jwt',
    'csrf_token','xsrf_token','samesite','secure'
    }


    TRACKING_INDICATORS =[
    'google','facebook','twitter','linkedin','analytics',
    'ad','ads','doubleclick','taboola','outbrain','taboola'
    ]

    def __init__ (self ):
        """Initialize with logger and cache"""
        try :
            from utils .logger import log_manager 
            self .logger =log_manager .get_logger ('security_analyzer')
        except :
            import logging 
            self .logger =logging .getLogger ('security_analyzer')
        self ._pattern_cache ={}

    def analyze (self ,cookie ):
        analysis ={
        'is_security_cookie':False ,
        'is_tracking_cookie':False ,
        'security_level':'low',
        'flags':[],
        'risks':[],
        'recommendations':[]
        }


        if self .is_security_cookie (cookie ):
            analysis ['is_security_cookie']=True 
            analysis ['flags'].append ('Security Cookie')


        if self .is_tracking_cookie (cookie ):
            analysis ['is_tracking_cookie']=True 
            analysis ['flags'].append ('Tracking Cookie')


        if cookie .secure :
            analysis ['flags'].append ('Secure Flag')
        else :
            analysis ['risks'].append ('Missing Secure Flag')
            analysis ['recommendations'].append ('Add Secure flag for HTTPS only')

        if cookie .http_only :
            analysis ['flags'].append ('HttpOnly Flag')
        else :
            analysis ['risks'].append ('Missing HttpOnly Flag')
            analysis ['recommendations'].append ('Add HttpOnly flag to prevent XSS')


        if cookie .expires ==0 :
            analysis ['flags'].append ('Session Cookie')
        else :
            expiry_date =datetime .fromtimestamp (cookie .expires )
            days_until_expiry =(expiry_date -datetime .now ()).days 

            if days_until_expiry <0 :
                analysis ['risks'].append ('Expired Cookie')
            elif days_until_expiry >365 :
                analysis ['risks'].append ('Long-lived Cookie')
                analysis ['recommendations'].append ('Consider shorter expiration')


        analysis ['security_level']=self ._calculate_security_level (analysis )

        return analysis 

    def is_security_cookie (self ,cookie ):

        cache_key =f'sec_{cookie .name }_{cookie .domain }'
        if cache_key in self ._pattern_cache :
            return self ._pattern_cache [cache_key ]

        name_lower =cookie .name .lower ()
        value_lower =cookie .value .lower ()


        if any (c in cookie .name for c in self .SECURITY_COOKIES ):
            self ._pattern_cache [cache_key ]=True 
            return True 


        for category ,patterns in self .SECURITY_PATTERNS .items ():
            if any (pattern in name_lower for pattern in patterns ):
                self ._pattern_cache [cache_key ]=True 
                return True 


        if any (keyword in value_lower for keyword in ['token','session','auth']):
            self ._pattern_cache [cache_key ]=True 
            return True 

        self ._pattern_cache [cache_key ]=False 
        return False 

    def is_tracking_cookie (self ,cookie ):

        cache_key =f'track_{cookie .name }_{cookie .domain }'
        if cache_key in self ._pattern_cache :
            return self ._pattern_cache [cache_key ]

        name_lower =cookie .name .lower ()
        domain_lower =cookie .domain .lower ()


        if any (indicator in domain_lower for indicator in self .TRACKING_INDICATORS ):
            self ._pattern_cache [cache_key ]=True 
            return True 


        if any (indicator in name_lower for indicator in self .TRACKING_INDICATORS ):
            self ._pattern_cache [cache_key ]=True 
            return True 

        self ._pattern_cache [cache_key ]=False 
        return False 

    def overall_analysis (self ,cookies ):
        total =len (cookies )
        security_cookies =sum (1 for c in cookies if self .is_security_cookie (c ))
        tracking_cookies =sum (1 for c in cookies if self .is_tracking_cookie (c ))


        secure_flags =sum (1 for c in cookies if c .secure )
        http_only_flags =sum (1 for c in cookies if c .http_only )

        security_score =((secure_flags +http_only_flags )/(total *2 ))*100 if total >0 else 0 

        return {
        'total_cookies':total ,
        'security_cookies':security_cookies ,
        'tracking_cookies':tracking_cookies ,
        'secure_cookies':secure_flags ,
        'http_only_cookies':http_only_flags ,
        'security_score':round (security_score ,2 ),
        'risk_level':self ._calculate_overall_risk (security_score ,security_cookies ,tracking_cookies ),
        'recommendations':self ._generate_recommendations (cookies )
        }

    def generate_report (self ,cookies ):
        analysis =self .overall_analysis (cookies )


        high_risk_cookies =[]
        for cookie in cookies :
            cookie_analysis =self .analyze (cookie )
            if cookie_analysis ['security_level']=='high':
                high_risk_cookies .append ({
                'cookie':cookie .to_dict (),
                'analysis':cookie_analysis 
                })

        return {
        'summary':analysis ,
        'high_risk_cookies':high_risk_cookies ,
        'security_recommendations':analysis ['recommendations'],
        'timestamp':datetime .now ().isoformat ()
        }

    def _calculate_security_level (self ,analysis ):
        risk_count =len (analysis ['risks'])

        if risk_count ==0 :
            return 'high'
        elif risk_count <=2 :
            return 'medium'
        else :
            return 'low'

    def _calculate_overall_risk (self ,security_score ,security_cookies ,tracking_cookies ):
        if security_score >80 :
            return 'low'
        elif security_score >50 :
            return 'medium'
        else :
            return 'high'

    def _generate_recommendations (self ,cookies ):
        recommendations =[]


        missing_secure =sum (1 for c in cookies if not c .secure )
        missing_http_only =sum (1 for c in cookies if not c .http_only )

        if missing_secure >0 :
            recommendations .append (
            f'{missing_secure } cookies missing Secure flag - add Secure flag for HTTPS only'
            )

        if missing_http_only >0 :
            recommendations .append (
            f'{missing_http_only } cookies missing HttpOnly flag - add to prevent XSS attacks'
            )


        long_lived =sum (1 for c in cookies 
        if c .expires !=0 and 
        (datetime .fromtimestamp (c .expires )-datetime .now ()).days >365 )

        if long_lived >0 :
            recommendations .append (
            f'{long_lived } cookies have expiration > 1 year - consider shorter lifetimes'
            )


        tracking =sum (1 for c in cookies if self .is_tracking_cookie (c ))
        if tracking >0 :
            recommendations .append (
            f'{tracking } tracking cookies detected - review privacy implications'
            )

        return recommendations 