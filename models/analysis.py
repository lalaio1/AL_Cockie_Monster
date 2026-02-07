from dataclasses import dataclass ,asdict 
from typing import List ,Dict ,Any 
#from datetime import datetime 


@dataclass 
class CookieAnalysis :
    cookie_name :str 
    cookie_domain :str 
    is_security_cookie :bool 
    is_tracking_cookie :bool 
    security_level :str 
    flags :List [str ]
    risks :List [str ]
    recommendations :List [str ]

    def to_dict (self )->Dict [str ,Any ]:
        return asdict (self )


@dataclass 
class OverallAnalysis :
    total_cookies :int 
    security_cookies :int 
    tracking_cookies :int 
    secure_cookies :int 
    http_only_cookies :int 
    same_site_cookies :int 
    security_score :float 
    risk_level :str 
    recommendations :List [str ]
    timestamp :str 

    def to_dict (self )->Dict [str ,Any ]:
        return asdict (self )
