import os 
import json 


CONFIG_DIR =os .path .join (os .path .dirname (__file__ ),'json')
os .makedirs (CONFIG_DIR ,exist_ok =True )

FILTERS_FILE =os .path .join (CONFIG_DIR ,'filters.json')
CONFIG_FILE =os .path .join (CONFIG_DIR ,'config.json')


DEFAULT_CONFIG ={
"max_workers":4 ,
"timeout_validate":10 ,
"timeout_filter":15 ,
"timeout_analyze":20 
}


class FiltersManager :
    @staticmethod 
    def load_filters ():
        if os .path .exists (FILTERS_FILE ):
            try :
                with open (FILTERS_FILE ,'r',encoding ='utf-8')as f :
                    return json .load (f )
            except Exception :
                return {}
        return {}

    @staticmethod 
    def save_filters (filters ):
        try :
            with open (FILTERS_FILE ,'w',encoding ='utf-8')as f :
                json .dump (filters ,f ,indent =2 ,ensure_ascii =False )
            return True 
        except Exception :
            return False 

    @staticmethod 
    def get_filter_names ():
        filters =FiltersManager .load_filters ()
        return list (filters .keys ())

    @staticmethod 
    def delete_filter (name ):
        filters =FiltersManager .load_filters ()
        if name in filters :
            del filters [name ]
            return FiltersManager .save_filters (filters )
        return False 


class ConfigManager :
    @staticmethod 
    def load_config ():
        if os .path .exists (CONFIG_FILE ):
            try :
                with open (CONFIG_FILE ,'r',encoding ='utf-8')as f :
                    return json .load (f )
            except Exception :
                return DEFAULT_CONFIG .copy ()
        return DEFAULT_CONFIG .copy ()

    @staticmethod 
    def save_config (config ):
        try :
            with open (CONFIG_FILE ,'w',encoding ='utf-8')as f :
                json .dump (config ,f ,indent =2 ,ensure_ascii =False )
            return True 
        except Exception :
            return False 

    @staticmethod 
    def get (key ,default =None ):
        config =ConfigManager .load_config ()
        return config .get (key ,default )

    @staticmethod 
    def set (key ,value ):
        config =ConfigManager .load_config ()
        config [key ]=value 
        return ConfigManager .save_config (config )
