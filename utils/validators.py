from datetime import datetime 


class CookieValidator :

    def validate (self ,cookie ):
        issues =[]
        warnings =[]


        if not cookie .secure :
            warnings .append ("Cookie is not marked as Secure")


        if not cookie .http_only :
            warnings .append ("Cookie is not marked as HttpOnly")


        if not cookie .domain or cookie .domain =='unknown':
            warnings .append ("Cookie has no valid domain specified")


        if cookie .expires >0 :
            try :
                exp_date =datetime .fromtimestamp (cookie .expires )
                if exp_date <datetime .now ():
                    warnings .append ("Cookie has expired")
            except (ValueError ,OverflowError ):
                issues .append ("Invalid expiration timestamp")


        if not cookie .value or not cookie .value .strip ():
            warnings .append ("Cookie has empty value")


        if not cookie .name or not cookie .name .strip ():
            issues .append ("Cookie has empty name")


        if not cookie .same_site :
            warnings .append ("Cookie lacks SameSite attribute")


        valid =len (issues )==0 

        return {
        'valid':valid ,
        'issues':issues ,
        'warnings':warnings 
        }
