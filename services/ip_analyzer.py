import requests 
import pycountry 
from ipwhois import IPWhois 
from functools import lru_cache 

class IPAnalyzer :
    def __init__ (self ):
        try :
            from utils .logger import log_manager 
            self .logger =log_manager .get_logger ('ip_analyzer')
        except :
            import logging 
            self .logger =logging .getLogger ('ip_analyzer')
        self ._ip_cache ={}

    def analyze (self ,ip_or_value ):

        if '-'in ip_or_value :
            ip =ip_or_value .split ('-')[0 ]
        else :
            ip =ip_or_value 


        if ip in self ._ip_cache :
            self .logger .debug (f'IP {ip } returned from cache')
            return self ._ip_cache [ip ]

        try :
            info =self ._analyze_ip (ip )
            self ._ip_cache [ip ]=info 
            return info 
        except Exception as e :
            self .logger .error (f'Error analyzing IP {ip }: {str (e )}')
            return {
            'ip':ip ,
            'error':str (e ),
            'country':'Unknown',
            'country_flag':'❓'
            }

    def _analyze_ip (self ,ip ):
        info ={
        'ip':ip ,
        'country':None ,
        'country_code':None ,
        'country_flag':None ,
        'region':None ,
        'city':None ,
        'isp':None ,
        'asn':None ,
        'organization':None ,
        'timezone':None ,
        'latitude':None ,
        'longitude':None ,
        'is_proxy':False ,
        'is_vpn':False ,
        'risk_score':0 
        }


        try :
            country_code =self ._get_country_code (ip )
            if country_code :
                country =pycountry .countries .get (alpha_2 =country_code )
                if country :
                    info ['country']=country .name 
                    info ['country_code']=country_code 
                    info ['country_flag']=self ._get_flag_emoji (country_code )
                    self .logger .debug (f'Country found for {ip }: {country .name }')
        except Exception as e :
            self .logger .debug (f'Country lookup failed for {ip }: {str (e )}')


        try :
            obj =IPWhois (ip ,timeout =3 )
            results =obj .lookup_rdap ()

            info ['asn']=results .get ('asn','N/A')
            info ['organization']=results .get ('asn_description','N/A')
            info ['isp']=results .get ('network',{}).get ('name','N/A')
            self .logger .debug (f'WHOIS info retrieved for {ip }')
        except Exception as e :
            self .logger .debug (f'WHOIS lookup failed for {ip }: {str (e )}')


        try :
            response =requests .get (f'http://ip-api.com/json/{ip }',timeout =5 )
            if response .status_code ==200 :
                data =response .json ()
                if data .get ('status')=='success':
                    info ['region']=data .get ('regionName')
                    info ['city']=data .get ('city')
                    info ['timezone']=data .get ('timezone')
                    info ['latitude']=data .get ('lat')
                    info ['longitude']=data .get ('lon')
                    self .logger .debug (f'Geolocation found for {ip }: {info ["city"]}, {info ["region"]}')
        except Exception as e :
            self .logger .debug (f'IP geolocation API failed for {ip }: {str (e )}')


        info ['risk_score']=self ._calculate_risk_score (info )

        return info 

    def _get_country_code (self ,ip ):

        try :
            response =requests .get (f'http://ip-api.com/json/{ip }?fields=countryCode',timeout =3 )
            if response .status_code ==200 :
                data =response .json ()
                return data .get ('countryCode')
        except :
            pass 
        return None 

    def _get_flag_emoji (self ,country_code ):
        try :

            code_points =[ord (char )+127397 for char in country_code .upper ()]
            return chr (code_points [0 ])+chr (code_points [1 ])
        except :
            return '🏳️'

    def _calculate_risk_score (self ,info ):
        score =0 


        if info .get ('isp'):
            isp_lower =info ['isp'].lower ()
            if any (keyword in isp_lower for keyword in ['proxy','vpn','tor','anonymous']):
                score +=30 


        high_risk_countries =['RU','CN','KP','IR','SY']
        if info .get ('country_code')in high_risk_countries :
            score +=20 


        if info .get ('asn')and 'unknown'in info ['asn'].lower ():
            score +=10 

        return min (score ,100 )