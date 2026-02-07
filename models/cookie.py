from datetime import datetime 
from dataclasses import dataclass ,asdict 

@dataclass 
class Cookie :
    domain :str 
    include_subdomains :bool 
    path :str 
    secure :bool 
    expires :int 
    name :str 
    value :str 
    http_only :bool =False 

    def to_dict (self ):
        return asdict (self )

    @property 
    def is_session (self ):
        return self .expires ==0 

    @property 
    def expiration_date (self ):
        if self .expires ==0 :
            return None 
        return datetime .fromtimestamp (self .expires ).isoformat ()

    @property 
    def same_site (self ):

        return 'SameSite'in self .value or 'samesite'in self .name .lower ()