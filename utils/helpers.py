from datetime import datetime 
#from typing import List ,Dict ,Any 
import re 


def validate_domain (domain :str )->bool :
    if not domain or not isinstance (domain ,str ):
        return False 


    domain_pattern =r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
    return bool (re .match (domain_pattern ,domain ))


def validate_path (path :str )->bool :
    if not path or not isinstance (path ,str ):
        return False 


    return path .startswith ('/')


def is_expired_timestamp (timestamp :int )->bool :
    if timestamp ==0 :
        return False 

    try :
        expiry_date =datetime .fromtimestamp (timestamp )
        return expiry_date <datetime .now ()
    except (ValueError ,OverflowError ):
        return False 


def format_timestamp (timestamp :int )->str :
    if timestamp ==0 :
        return "Session"

    try :
        return datetime .fromtimestamp (timestamp ).isoformat ()
    except (ValueError ,OverflowError ):
        return "Invalid"


def get_days_until_expiry (timestamp :int )->int :
    if timestamp ==0 :
        return -1 

    try :
        expiry_date =datetime .fromtimestamp (timestamp )
        delta =(expiry_date -datetime .now ()).days 
        return delta 
    except (ValueError ,OverflowError ):
        return 0 


def sanitize_cookie_value (value :str )->str :
    if not value :
        return ""


    max_length =100 
    if len (value )>max_length :
        return value [:max_length ]+"..."

    return value 
