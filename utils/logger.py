import logging 
import logging .handlers 
import os 
#from datetime import datetime 


class LogManager :

    _instance =None 
    _loggers ={}

    def __new__ (cls ):
        if cls ._instance is None :
            cls ._instance =super ().__new__ (cls )
            cls ._instance ._initialized =False 
        return cls ._instance 

    def __init__ (self ):
        if self ._initialized :
            return 


        self .log_dir =os .path .join (os .path .dirname (__file__ ),'..','logs')
        os .makedirs (self .log_dir ,exist_ok =True )


        self .log_format =logging .Formatter (
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt ='%Y-%m-%d %H:%M:%S'
        )

        self ._initialized =True 

    def get_logger (self ,name ,level =logging .INFO ):
        if name in self ._loggers :
            return self ._loggers [name ]

        logger =logging .getLogger (name )
        logger .setLevel (level )


        log_file =os .path .join (self .log_dir ,f'{name }.log')
        file_handler =logging .handlers .RotatingFileHandler (
        log_file ,maxBytes =10 *1024 *1024 ,backupCount =5 
        )
        file_handler .setFormatter (self .log_format )
        logger .addHandler (file_handler )


        console_handler =logging .StreamHandler ()
        console_handler .setFormatter (self .log_format )
        logger .addHandler (console_handler )

        self ._loggers [name ]=logger 
        return logger 



log_manager =LogManager ()
