import re 
from datetime import datetime 
from .security_analyzer import SecurityAnalyzer 

class FilterService :
    def __init__ (self ):
        try :
            from utils .logger import log_manager 
            self .logger =log_manager .get_logger ('filter_service')
        except :
            import logging 
            self .logger =logging .getLogger ('filter_service')
        self ._analyzer =SecurityAnalyzer ()
    def get_available_filters (self ):
        return {
        'security':{
        'description':'Filter by security characteristics',
        'options':[
        'remove_tracking',
        'remove_security',
        'keep_security_only',
        'remove_insecure'
        ]
        },
        'domain':{
        'description':'Filter by domain',
        'options':[
        'include_domains',
        'exclude_domains',
        'by_tld'
        ]
        },
        'expiration':{
        'description':'Filter by expiration',
        'options':[
        'remove_expired',
        'remove_session',
        'remove_persistent',
        'by_days'
        ]
        },
        'flags':{
        'description':'Filter by cookie flags',
        'options':[
        'remove_non_secure',
        'remove_non_http_only',
        'remove_non_same_site'
        ]
        },
        'specific':{
        'description':'Remove specific cookie types',
        'options':[
        'remove_anon',
        'remove_mscc',
        'remove_muid',
        'remove_tracking_patterns'
        ]
        },
        'value':{
        'description':'Filter by cookie value',
        'options':[
        'remove_empty',
        'remove_sensitive_patterns'
        ]
        }
        }

    def apply_filters (self ,cookies ,criteria ):
        filtered =cookies .copy ()
        self .logger .debug (f'Applying filters: {list (criteria .keys ())} to {len (cookies )} cookies')


        for filter_type ,filter_value in criteria .items ():
            if filter_type =='remove_anon':
                filtered =self ._remove_anon (filtered )
            elif filter_type =='remove_mscc':
                filtered =self ._remove_mscc (filtered )
            elif filter_type =='remove_muid':
                filtered =self ._remove_muid (filtered )
            elif filter_type =='remove_tracking':
                filtered =self ._remove_tracking (filtered )
            elif filter_type =='remove_security':
                filtered =self ._remove_security (filtered )
            elif filter_type =='keep_security_only':
                filtered =self ._keep_security_only (filtered )
            elif filter_type =='remove_insecure':
                filtered =self ._remove_insecure (filtered )
            elif filter_type =='remove_expired':
                filtered =self ._remove_expired (filtered )
            elif filter_type =='remove_session':
                filtered =self ._remove_session (filtered )
            elif filter_type =='remove_persistent':
                filtered =self ._remove_persistent (filtered )
            elif filter_type =='remove_non_secure':
                filtered =self ._remove_non_secure (filtered )
            elif filter_type =='remove_non_http_only':
                filtered =self ._remove_non_http_only (filtered )
            elif filter_type =='remove_non_same_site':
                filtered =self ._remove_non_same_site (filtered )
            elif filter_type =='remove_empty':
                filtered =self ._remove_empty (filtered )
            elif filter_type =='remove_tracking_patterns':
                filtered =self ._remove_tracking_patterns (filtered )
            elif filter_type =='remove_sensitive_patterns':
                filtered =self ._remove_sensitive_patterns (filtered )
            elif filter_type =='include_domains':
                filtered =self ._include_domains (filtered ,filter_value )
            elif filter_type =='exclude_domains':
                filtered =self ._exclude_domains (filtered ,filter_value )
            elif filter_type =='by_days':
                filtered =self ._filter_by_days (filtered ,filter_value )

            self .logger .debug (f'After {filter_type }: {len (filtered )} cookies remaining')

        return filtered 

    def _remove_anon (self ,cookies ):
        return [c for c in cookies if c .name .upper ()!='ANON']

    def _remove_mscc (self ,cookies ):
        return [c for c in cookies if c .name .upper ()!='MSCC']

    def _remove_muid (self ,cookies ):
        return [c for c in cookies if c .name .upper ()!='MUID']

    def _remove_tracking (self ,cookies ):
        return [c for c in cookies if not self ._analyzer .is_tracking_cookie (c )]

    def _remove_security (self ,cookies ):
        return [c for c in cookies if not self ._analyzer .is_security_cookie (c )]

    def _keep_security_only (self ,cookies ):
        return [c for c in cookies if self ._analyzer .is_security_cookie (c )]

    def _remove_insecure (self ,cookies ):
        return [c for c in cookies if c .secure and c .http_only ]

    def _remove_expired (self ,cookies ):
        now =datetime .now ().timestamp ()
        return [c for c in cookies if c .expires ==0 or c .expires >now ]

    def _remove_session (self ,cookies ):
        return [c for c in cookies if not c .is_session ]

    def _remove_persistent (self ,cookies ):
        return [c for c in cookies if c .is_session ]

    def _remove_non_secure (self ,cookies ):
        return [c for c in cookies if c .secure ]

    def _remove_non_http_only (self ,cookies ):
        return [c for c in cookies if c .http_only ]

    def _remove_empty (self ,cookies ):
        return [c for c in cookies if c .value and c .value .strip ()]

    def _include_domains (self ,cookies ,domains ):
        domains_set =set (d .lower ()for d in domains )
        return [c for c in cookies if c .domain .lower ()in domains_set ]

    def _exclude_domains (self ,cookies ,domains ):
        domains_set =set (d .lower ()for d in domains )
        return [c for c in cookies if c .domain .lower ()not in domains_set ]

    def _filter_by_days (self ,cookies ,days ):
        now =datetime .now ().timestamp ()
        target_time =now +(days *86400 )

        return [c for c in cookies if c .expires ==0 or c .expires <=target_time ]

    def _remove_non_same_site (self ,cookies ):
        return [c for c in cookies if c .same_site ]

    def _remove_tracking_patterns (self ,cookies ):
        analyzer =SecurityAnalyzer ()
        return [c for c in cookies if not analyzer .is_tracking_cookie (c )]

    def _remove_sensitive_patterns (self ,cookies ):
        sensitive_patterns ={'password','secret','token','key','credential','api_key'}
        filtered =[]
        for c in cookies :
            value_lower =c .value .lower ()
            if not any (pattern in value_lower for pattern in sensitive_patterns ):
                filtered .append (c )
        return filtered 