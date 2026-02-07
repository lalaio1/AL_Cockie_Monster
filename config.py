import os 

class Config :
    DEBUG =True 
    SECRET_KEY =os .environ .get ('SECRET_KEY','dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH =16 *1024 *1024 
    ALLOWED_ORIGINS =['*']
    RATE_LIMIT ='100 per hour'
    @staticmethod 
    def init_app (app ):
        pass 