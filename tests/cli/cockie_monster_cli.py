import os 
import sys 
import json 
import msvcrt 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),'..'))

from gui .managers import FiltersManager ,ConfigManager 
from cli .engine import find_txt_files ,validate_files ,filter_files ,analyze_files ,list_filters 


try :
    from pystyle import Colors ,Colorate ,Center 
    def color_header (text ):
        return Colorate .Horizontal (Colors .blue_to_cyan ,text )
    def color_highlight (text ):
        return Colorate .Horizontal (Colors .white_to_blue ,text )
    def color_normal (text ):
        return Colorate .Horizontal (Colors .cyan ,text )
except Exception :
    def color_header (text ):
        return text 
    def color_highlight (text ):
        return text 
    def color_normal (text ):
        return text 

def cmd_scan (args ):
    folder =args .folder 
    if not folder or not os .path .isdir (folder ):
        print ('[-] pasta inexistente. Use --folder <path>')
        return 1 
    files =find_txt_files (folder )
    print (f"[+] arquivos .txt encontrados: {len (files )}")
    if not files :
        return 0 

    results =validate_files (files )
    for i ,res in enumerate (results ,1 ):
        print (f"[{i }/{len (results )}] -> {os .path .basename (res ['file'])} : {res ['status']} ({res ['cookies']})")

    if args .output :
        try :
            with open (args .output ,'w',encoding ='utf-8')as fo :
                json .dump (results ,fo ,indent =2 ,ensure_ascii =False )
            print (f"[+] resultados salvos em {args .output }")
        except Exception as e :
            print (f"[-] falha ao salvar: {e }")

    return 0 


def cmd_filter (args ):
    folder =args .folder 
    if not folder or not os .path .isdir (folder ):
        print ('[-] pasta inexistente. Use --folder <path>')
        return 1 

    if args .preset :
        presets =FiltersManager .load_filters ()
        if args .preset not in presets :
            print (f"[-] preset nao encontrado: {args .preset }")
            return 1 
        filters =presets [args .preset ]
    elif args .keys :
        keys =[k .strip ()for k in args .keys .split (',')if k .strip ()]
        filters ={k :True for k in keys }
    else :
        print ('[-] indique --preset NAME ou --keys key1,key2')
        return 1 

    files =find_txt_files (folder )
    print (f"[+] aplicando filtros a {len (files )} arquivos")

    results =filter_files (files ,filters )
    for i ,res in enumerate (results ,1 ):
        print (f"[{i }/{len (results )}] -> {os .path .basename (res ['file'])} : {res ['status']} ({res ['cookies']})")

    if args .output :
        try :
            with open (args .output ,'w',encoding ='utf-8')as fo :
                json .dump (results ,fo ,indent =2 ,ensure_ascii =False )
            print (f"[+] resultados salvos em {args .output }")
        except Exception as e :
            print (f"[-] falha ao salvar: {e }")

    return 0 


def cmd_analyze (args ):
    folder =args .folder 
    if not folder or not os .path .isdir (folder ):
        print ('[-] pasta inexistente. Use --folder <path>')
        return 1 

    files =find_txt_files (folder )
    print (f"[+] analisando {len (files )} arquivos")

    results =analyze_files (files )
    for i ,res in enumerate (results ,1 ):
        if res .get ('result'):
            total =res ['result'].get ('total_cookies',0 )
            print (f"[{i }/{len (results )}] -> {os .path .basename (res ['file'])} : ANALISADO ({total })")
        else :
            print (f"[{i }/{len (results )}] -> {os .path .basename (res ['file'])} : {res ['status']}")

    return 0 


def cmd_presets (args ):
    if args .action =='list':
        names =FiltersManager .get_filter_names ()
        if not names :
            print ('[+] nenhum preset encontrado')
            return 0 
        for n in names :
            print (f"[+] {n }")
        return 0 

    if args .action =='save':
        if not args .name or not args .keys :
            print ('[-] use --name NOME --keys key1,key2')
            return 1 
        keys =[k .strip ()for k in args .keys .split (',')if k .strip ()]
        data ={k :True for k in keys }
        presets =FiltersManager .load_filters ()
        presets [args .name ]=data 
        if FiltersManager .save_filters (presets ):
            print (f"[+] preset salvo: {args .name }")
        else :
            print ('[-] falha ao salvar preset')
        return 0 

    if args .action =='delete':
        if not args .name :
            print ('[-] use --name NOME')
            return 1 
        if FiltersManager .delete_filter (args .name ):
            print (f"[+] preset deletado: {args .name }")
        else :
            print ('[-] falha ao deletar preset')
        return 0 

    return 0 


def cmd_config (args ):
    if args .action =='show':
        cfg =ConfigManager .load_config ()
        print (json .dumps (cfg ,indent =2 ))
        return 0 
    if args .action =='set':
        if not args .key or args .value is None :
            print ('[-] use --key KEY --value VAL')
            return 1 
        try :
            val =int (args .value )
        except ValueError :
            val =args .value 
        cfg =ConfigManager .load_config ()
        cfg [args .key ]=val 
        if ConfigManager .save_config (cfg ):
            print (f"[+] config atualizada: {args .key } -> {val }")
            return 0 
        else :
            print ('[-] falha ao salvar config')
            return 1 

    return 0 


def interactive_mode ():
    options =[
    'Scan e validar arquivos',
    'Aplicar filtros (preset)',
    'Analisar arquivos',
    'Listar filtros disponiveis (api)',
    'Ver / editar config',
    'Sair'
    ]

    def read_key ():
        k =msvcrt .getwch ()
        if k in ('\x00','\xe0'):
            k2 =msvcrt .getwch ()
            if k2 =='H':
                return 'up'
            if k2 =='P':
                return 'down'
            if k2 =='K':
                return 'left'
            if k2 =='M':
                return 'right'
            return None 
        if k =='\r':
            return 'enter'
        if k =='\x1b':
            return 'esc'
        return k 

    idx =0 
    while True :
        os .system ('cls')
        print (color_header ('\n[+] Cockie Monster - Modo interativo\n'))
        for i ,opt in enumerate (options ):
            prefix ='→ 'if i ==idx else '  '
            text =f"{prefix }{opt }"
            if i ==idx :
                print (color_highlight (text ))
            else :
                print (color_normal (text ))

        key =read_key ()
        if key =='up':
            idx =(idx -1 )%len (options )
        elif key =='down':
            idx =(idx +1 )%len (options )
        elif key =='enter':
            choice =options [idx ]
            if choice =='Sair':
                print ('\n[+] saindo')
                break 

            if choice =='Scan e validar arquivos':
                folder =input ('\n[+] pasta (path): ').strip ()
                if not os .path .isdir (folder ):
                    print ('[-] pasta invalida')
                    input ('\nPressione ENTER para continuar...')
                    continue 
                results =validate_files (find_txt_files (folder ))
                for i ,r in enumerate (results ,1 ):
                    print (f"[{i }/{len (results )}] -> {os .path .basename (r ['file'])} : {r ['status']} ({r .get ('cookies')})")
                input ('\nPressione ENTER para continuar...')

            elif choice =='Aplicar filtros (preset)':
                folder =input ('\n[+] pasta (path): ').strip ()
                if not os .path .isdir (folder ):
                    print ('[-] pasta invalida')
                    input ('\nPressione ENTER para continuar...')
                    continue 
                api_filters =list_filters ()
                if api_filters :
                    print ('\n[+] filtros da API:')
                    try :
                        for k in api_filters .keys ():
                            print (f"[+] {k }")
                    except Exception :
                        print ('[+] filtros obtidos')
                presets =FiltersManager .get_filter_names ()
                if presets :
                    print ('\n[+] presets locais:')
                    for p in presets :
                        print (f"[+] {p }")
                name =input ('\n[+] usar preset local (nome) ou ENTER para digitar chaves: ').strip ()
                if name :
                    all_presets =FiltersManager .load_filters ()
                    if name not in all_presets :
                        print ('[-] preset local nao encontrado')
                        input ('\nPressione ENTER para continuar...')
                        continue 
                    filters =all_presets [name ]
                else :
                    keys =input ('\n[+] chaves separadas por virgula: ').strip ()
                    keys =[k .strip ()for k in keys .split (',')if k .strip ()]
                    filters ={k :True for k in keys }
                results =filter_files (find_txt_files (folder ),filters )
                for i ,r in enumerate (results ,1 ):
                    print (f"[{i }/{len (results )}] -> {os .path .basename (r ['file'])} : {r ['status']} ({r .get ('cookies')})")
                input ('\nPressione ENTER para continuar...')

            elif choice =='Analisar arquivos':
                folder =input ('\n[+] pasta (path): ').strip ()
                if not os .path .isdir (folder ):
                    print ('[-] pasta invalida')
                    input ('\nPressione ENTER para continuar...')
                    continue 
                results =analyze_files (find_txt_files (folder ))
                for i ,r in enumerate (results ,1 ):
                    if r .get ('result'):
                        total =r ['result'].get ('total_cookies',0 )
                        print (f"[{i }/{len (results )}] -> {os .path .basename (r ['file'])} : ANALISADO ({total })")
                    else :
                        print (f"[{i }/{len (results )}] -> {os .path .basename (r ['file'])} : {r ['status']}")
                input ('\nPressione ENTER para continuar...')

            elif choice =='Listar filtros disponiveis (api)':
                api_filters =list_filters ()
                if not api_filters :
                    print ('[-] nao foi possivel obter filtros da api')
                else :
                    print ('\n[+] filtros disponiveis:')
                    print (json .dumps (api_filters ,indent =2 ,ensure_ascii =False ))
                input ('\nPressione ENTER para continuar...')

            elif choice =='Ver / editar config':
                cfg =ConfigManager .load_config ()
                print ('\n[+] config atual:')
                print (json .dumps (cfg ,indent =2 ))
                if input ('\n[+] editar? (s/N): ').strip ().lower ()=='s':
                    key =input ('[+] chave: ').strip ()
                    val =input ('[+] valor: ').strip ()
                    try :
                        v =int (val )
                    except Exception :
                        v =val 
                    cfg [key ]=v 
                    ConfigManager .save_config (cfg )
                    print ('\n[+] config salva')
                input ('\nPressione ENTER para continuar...')
        elif key =='esc':
            break 



def main ():
    try :
        interactive_mode ()
    except KeyboardInterrupt :
        print ('\n[+] encerrando...')
    return 0 


if __name__ =='__main__':
    sys .exit (main ())
