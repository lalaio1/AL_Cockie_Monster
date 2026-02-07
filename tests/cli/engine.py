import os 
#import json 
import requests 
from concurrent .futures import ThreadPoolExecutor ,as_completed 
import time 
import logging 
from typing import List ,Dict ,Any ,Optional ,Union 
from pathlib import Path 

from gui .managers import ConfigManager 
from gui .config_gui import API_BASE 


logging .basicConfig (level =logging .WARNING )
logger =logging .getLogger (__name__ )

class APIError (Exception ):
    pass 

class FileReadError (Exception ):
    pass 

def find_txt_files (folder :Union [str ,Path ])->List [str ]:
    folder =str (folder )
    files =[]
    try :
        for root ,dirs ,fns in os .walk (folder ):
            for fn in fns :
                if fn .lower ().endswith ('.txt'):
                    files .append (os .path .join (root ,fn ))
    except Exception as e :
        logger .error (f"Erro ao buscar arquivos em {folder }: {e }")
    return files 


def _get_cfg ()->tuple :
    cfg =ConfigManager .load_config ()
    return (
    cfg .get ('max_workers',4 ),
    cfg .get ('timeout_validate',10 ),
    cfg .get ('timeout_filter',15 ),
    cfg .get ('timeout_analyze',20 ),
    cfg .get ('retry_attempts',3 ),
    cfg .get ('retry_delay',1 )
    )


def _read_file_safe (fpath :str )->Optional [str ]:
    try :
        if not os .path .exists (fpath ):
            logger .error (f"Arquivo não encontrado: {fpath }")
            return None 

        file_size =os .path .getsize (fpath )
        if file_size >100 *1024 *1024 :
            logger .warning (f"Arquivo muito grande ({file_size } bytes): {fpath }")


        with open (fpath ,'r',encoding ='utf-8',errors ='ignore')as fh :
            content =fh .read ()

        if not content .strip ():
            logger .warning (f"Arquivo vazio: {fpath }")

        return content 
    except UnicodeDecodeError :
        try :

            encodings =['latin-1','iso-8859-1','cp1252']
            for enc in encodings :
                try :
                    with open (fpath ,'r',encoding =enc ,errors ='ignore')as fh :
                        return fh .read ()
                except UnicodeDecodeError :
                    continue 
            logger .error (f"Não foi possível decodificar o arquivo: {fpath }")
            return None 
        except Exception as e :
            logger .error (f"Erro ao ler arquivo {fpath }: {e }")
            return None 
    except Exception as e :
        logger .error (f"Erro ao ler arquivo {fpath }: {e }")
        return None 


def _make_api_request_with_retry (
endpoint :str ,
data :Dict ,
timeout :int ,
retry_attempts :int =3 ,
retry_delay :float =1 
)->Optional [requests .Response ]:
    url =f"{API_BASE }{endpoint }"

    for attempt in range (retry_attempts ):
        try :
            response =requests .post (url ,json =data ,timeout =timeout )
            response .raise_for_status ()
            return response 
        except requests .exceptions .Timeout :
            logger .warning (f"Timeout na tentativa {attempt +1 } para {endpoint }")
            if attempt <retry_attempts -1 :
                time .sleep (retry_delay *(attempt +1 ))
            else :
                raise 
        except requests .exceptions .ConnectionError :
            logger .warning (f"Erro de conexão na tentativa {attempt +1 }")
            if attempt <retry_attempts -1 :
                time .sleep (retry_delay )
            else :
                raise 
        except requests .exceptions .RequestException as e :
            logger .error (f"Erro na requisição: {e }")
            if attempt <retry_attempts -1 and 500 <=e .response .status_code <600 :
                time .sleep (retry_delay )
            else :
                raise 

    return None 


def validate_files (
files :List [str ],
max_workers :Optional [int ]=None ,
timeout :Optional [int ]=None 
)->List [Dict [str ,Any ]]:
    max_w ,t_validate ,_ ,_ ,retry_attempts ,retry_delay =_get_cfg ()
    max_workers =max_workers or max_w 
    timeout =timeout or t_validate 

    def _worker (fpath :str )->Dict [str ,Any ]:
        start_time =time .time ()
        try :
            content =_read_file_safe (fpath )
            if content is None :
                return {
                'file':fpath ,
                'status':'ERRO_LEITURA',
                'cookies':0 ,
                'processing_time':0 
                }


            if not content .strip ():
                return {
                'file':fpath ,
                'status':'VAZIO',
                'cookies':0 ,
                'processing_time':time .time ()-start_time 
                }

            response =_make_api_request_with_retry (
            '/api/validate',
            {'cookies_text':content },
            timeout ,
            retry_attempts ,
            retry_delay 
            )

            if response and response .status_code ==200 :
                data =response .json ()
                total =data .get ('total_cookies',0 )
                status ='VALID'if total >0 else 'EMPTY'
                return {
                'file':fpath ,
                'status':status ,
                'cookies':total ,
                'processing_time':time .time ()-start_time ,
                'api_data':data 
                }
            else :
                return {
                'file':fpath ,
                'status':f'API_ERROR_{response .status_code if response else "NO_RESPONSE"}',
                'cookies':0 ,
                'processing_time':time .time ()-start_time 
                }

        except requests .exceptions .Timeout :
            return {
            'file':fpath ,
            'status':'TIMEOUT',
            'cookies':0 ,
            'processing_time':time .time ()-start_time 
            }
        except Exception as e :
            error_msg =str (e )[:60 ]
            return {
            'file':fpath ,
            'status':f'ERROR_{error_msg }',
            'cookies':0 ,
            'processing_time':time .time ()-start_time 
            }

    results =[]
    with ThreadPoolExecutor (max_workers =max_workers )as ex :
        futures ={ex .submit (_worker ,f ):f for f in files }


        total_files =len (files )
        if total_files >10 :
            print (f"[*] Validando {total_files } arquivos...")

        for i ,fut in enumerate (as_completed (futures ),1 ):
            try :
                results .append (fut .result ())


                if total_files >10 and i %max (1 ,total_files //10 )==0 :
                    print (f"[*] Progresso: {i }/{total_files } ({i /total_files *100 :.0f}%)")

            except Exception as e :
                logger .error (f"Erro no worker para {futures [fut ]}: {e }")
                results .append ({
                'file':futures [fut ],
                'status':'WORKER_ERROR',
                'cookies':0 ,
                'processing_time':0 
                })

    return results 


def filter_files (
files :List [str ],
filters :Dict [str ,Any ],
max_workers :Optional [int ]=None ,
timeout :Optional [int ]=None 
)->List [Dict [str ,Any ]]:
    max_w ,_ ,t_filter ,_ ,retry_attempts ,retry_delay =_get_cfg ()
    max_workers =max_workers or max_w 
    timeout =timeout or t_filter 

    def _worker (fpath :str )->Dict [str ,Any ]:
        start_time =time .time ()
        try :
            content =_read_file_safe (fpath )
            if content is None :
                return {
                'file':fpath ,
                'status':'ERRO_LEITURA',
                'cookies':0 ,
                'processing_time':0 
                }


            if not content .strip ():
                return {
                'file':fpath ,
                'status':'VAZIO',
                'cookies':0 ,
                'processing_time':time .time ()-start_time 
                }

            data ={'cookies_text':content ,'filters':filters }
            response =_make_api_request_with_retry (
            '/api/filter',
            data ,
            timeout ,
            retry_attempts ,
            retry_delay 
            )

            if response and response .status_code ==200 :
                res =response .json ()
                cnt =res .get ('filtered_count',0 )
                return {
                'file':fpath ,
                'status':'FILTERED',
                'cookies':cnt ,
                'processing_time':time .time ()-start_time ,
                'filtered_cookies':res .get ('filtered_cookies',[]),
                'api_data':res 
                }
            else :
                return {
                'file':fpath ,
                'status':f'API_ERROR_{response .status_code if response else "NO_RESPONSE"}',
                'cookies':0 ,
                'processing_time':time .time ()-start_time 
                }

        except requests .exceptions .Timeout :
            return {
            'file':fpath ,
            'status':'TIMEOUT',
            'cookies':0 ,
            'processing_time':time .time ()-start_time 
            }
        except Exception as e :
            error_msg =str (e )[:60 ]
            return {
            'file':fpath ,
            'status':f'ERROR_{error_msg }',
            'cookies':0 ,
            'processing_time':time .time ()-start_time 
            }

    results =[]
    with ThreadPoolExecutor (max_workers =max_workers )as ex :
        futures ={ex .submit (_worker ,f ):f for f in files }


        total_files =len (files )
        if total_files >10 :
            print (f"[*] Filtrando {total_files } arquivos...")

        for i ,fut in enumerate (as_completed (futures ),1 ):
            try :
                results .append (fut .result ())


                if total_files >10 and i %max (1 ,total_files //10 )==0 :
                    print (f"[*] Progresso: {i }/{total_files } ({i /total_files *100 :.0f}%)")

            except Exception as e :
                logger .error (f"Erro no worker para {futures [fut ]}: {e }")
                results .append ({
                'file':futures [fut ],
                'status':'WORKER_ERROR',
                'cookies':0 ,
                'processing_time':0 
                })

    return results 


def analyze_files (
files :List [str ],
max_workers :Optional [int ]=None ,
timeout :Optional [int ]=None 
)->List [Dict [str ,Any ]]:
    max_w ,_ ,_ ,t_analyze ,retry_attempts ,retry_delay =_get_cfg ()
    max_workers =max_workers or max_w 
    timeout =timeout or t_analyze 

    def _worker (fpath :str )->Dict [str ,Any ]:
        start_time =time .time ()
        try :
            content =_read_file_safe (fpath )
            if content is None :
                return {
                'file':fpath ,
                'status':'ERRO_LEITURA',
                'result':None ,
                'processing_time':0 
                }


            if not content .strip ():
                return {
                'file':fpath ,
                'status':'VAZIO',
                'result':{'total_cookies':0 ,'cookies_by_type':{}},
                'processing_time':time .time ()-start_time 
                }

            response =_make_api_request_with_retry (
            '/api/analyze',
            {'cookies_text':content },
            timeout ,
            retry_attempts ,
            retry_delay 
            )

            if response and response .status_code ==200 :
                res =response .json ()
                return {
                'file':fpath ,
                'status':'ANALYZED',
                'result':res ,
                'processing_time':time .time ()-start_time 
                }
            else :
                return {
                'file':fpath ,
                'status':f'API_ERROR_{response .status_code if response else "NO_RESPONSE"}',
                'result':None ,
                'processing_time':time .time ()-start_time 
                }

        except requests .exceptions .Timeout :
            return {
            'file':fpath ,
            'status':'TIMEOUT',
            'result':None ,
            'processing_time':time .time ()-start_time 
            }
        except Exception as e :
            error_msg =str (e )[:60 ]
            return {
            'file':fpath ,
            'status':f'ERROR_{error_msg }',
            'result':None ,
            'processing_time':time .time ()-start_time 
            }

    results =[]
    with ThreadPoolExecutor (max_workers =max_workers )as ex :
        futures ={ex .submit (_worker ,f ):f for f in files }


        total_files =len (files )
        if total_files >10 :
            print (f"[*] Analisando {total_files } arquivos...")

        for i ,fut in enumerate (as_completed (futures ),1 ):
            try :
                results .append (fut .result ())


                if total_files >10 and i %max (1 ,total_files //10 )==0 :
                    print (f"[*] Progresso: {i }/{total_files } ({i /total_files *100 :.0f}%)")

            except Exception as e :
                logger .error (f"Erro no worker para {futures [fut ]}: {e }")
                results .append ({
                'file':futures [fut ],
                'status':'WORKER_ERROR',
                'result':None ,
                'processing_time':0 
                })

    return results 


def list_filters ()->Dict [str ,Any ]:
    try :
        response =requests .get (f"{API_BASE }/api/filters",timeout =10 )
        if response .status_code ==200 :
            return response .json ()
        else :
            logger .error (f"API retornou status {response .status_code }")
            return {}
    except requests .exceptions .Timeout :
        logger .error ("Timeout ao buscar filtros")
        return {}
    except requests .exceptions .ConnectionError :
        logger .error ("Erro de conexão ao buscar filtros")
        return {}
    except Exception as e :
        logger .error (f"Erro ao buscar filtros: {e }")
        return {}



def validate_single_file (file_path :str )->Dict [str ,Any ]:
    results =validate_files ([file_path ])
    return results [0 ]if results else None 


def filter_single_file (file_path :str ,filters :Dict [str ,Any ])->Dict [str ,Any ]:
    results =filter_files ([file_path ],filters )
    return results [0 ]if results else None 


def analyze_single_file (file_path :str )->Dict [str ,Any ]:
    results =analyze_files ([file_path ])
    return results [0 ]if results else None 


def batch_process (
folder :str ,
operation :str ="validate",
filters :Optional [Dict [str ,Any ]]=None 
)->List [Dict [str ,Any ]]:
    files =find_txt_files (folder )

    if not files :
        return []

    if operation =="validate":
        return validate_files (files )
    elif operation =="filter":
        if filters is None :
            raise ValueError ("Filtros são necessários para operação de filtro")
        return filter_files (files ,filters )
    elif operation =="analyze":
        return analyze_files (files )
    else :
        raise ValueError (f"Operação desconhecida: {operation }")



def get_file_stats (file_path :str )->Dict [str ,Any ]:
    try :
        stat =os .stat (file_path )
        return {
        'size':stat .st_size ,
        'modified':stat .st_mtime ,
        'created':stat .st_ctime ,
        'extension':os .path .splitext (file_path )[1 ].lower ()
        }
    except Exception as e :
        logger .error (f"Erro ao obter estatísticas de {file_path }: {e }")
        return {}


def check_api_health ()->bool :
    try :
        response =requests .get (f"{API_BASE }/api/health",timeout =5 )
        return response .status_code ==200 
    except Exception :
        return False 



def process_files (
files :List [str ],
mode :str ="validate",
filters :Optional [Dict [str ,Any ]]=None ,
**kwargs 
)->List [Dict [str ,Any ]]:
    """
    Função genérica para processar arquivos (compatibilidade).
    
    Args:
        files: Lista de arquivos
        mode: Modo de operação
        filters: Filtros (apenas para modo 'filter')
        **kwargs: Argumentos adicionais
        
    Returns:
        Lista de resultados
    """
    if mode =="validate":
        return validate_files (files ,**kwargs )
    elif mode =="filter":
        if filters is None :
            raise ValueError ("Filtros são necessários para modo filter")
        return filter_files (files ,filters ,**kwargs )
    elif mode =="analyze":
        return analyze_files (files ,**kwargs )
    else :
        raise ValueError (f"Modo desconhecido: {mode }")