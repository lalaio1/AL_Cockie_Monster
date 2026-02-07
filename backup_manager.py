import os 
import zipfile 
import logging 
from datetime import datetime 

class BackupManager :
    def __init__ (self ,project_root =None ):
        self .project_root =project_root or os .path .dirname (os .path .abspath (__file__ ))
        self .backups_dir =os .path .join (self .project_root ,'backups')
        self .logs_dir =os .path .join (self .project_root ,'logs')
        self .log_file =os .path .join (self .logs_dir ,'backup_log.log')
        os .makedirs (self .backups_dir ,exist_ok =True )
        self .setup_logging ()

    def setup_logging (self ):
        self .logger =logging .getLogger ('BackupManager')
        self .logger .setLevel (logging .INFO )


        handler =logging .FileHandler (self .log_file ,encoding ='utf-8')
        formatter =logging .Formatter (
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt ='%Y-%m-%d %H:%M:%S'
        )
        handler .setFormatter (formatter )


        self .logger .handlers .clear ()


        self .logger .addHandler (handler )

    def should_exclude (self ,file_path ,arcname ):
        exclude_patterns =[
        'venv',
        '__pycache__',
        '.pyc',
        'backups',
        'bak',
        '.git',
        '.gitignore',
        '*.egg-info',
        '.pytest_cache',
        '.coverage'
        ]

        for pattern in exclude_patterns :
            if pattern in arcname .split (os .sep ):
                return True 

        return False 

    def create_backup (self ,backup_name =None ):
        try :

            if backup_name is None :
                timestamp =datetime .now ().strftime ('%Y%m%d_%H%M%S')
                backup_name =f'cockie_monster_backup_{timestamp }.zip'

            backup_path =os .path .join (self .backups_dir ,backup_name )

            self .logger .info (f'Starting backup: {backup_name }')
            self .logger .info (f'Project root: {self .project_root }')


            with zipfile .ZipFile (backup_path ,'w',zipfile .ZIP_DEFLATED )as zipf :
                files_included =0 
                files_excluded =0 


                for root ,dirs ,files in os .walk (self .project_root ):

                    dirs [:]=[d for d in dirs if d not in ['backups','bak','venv','__pycache__']]

                    for file in files :
                        file_path =os .path .join (root ,file )
                        arcname =os .path .relpath (file_path ,self .project_root )


                        if self .should_exclude (file_path ,arcname ):
                            files_excluded +=1 
                            continue 

                        try :
                            zipf .write (file_path ,arcname )
                            files_included +=1 
                        except Exception as e :
                            self .logger .warning (f'Could not include file {file_path }: {str (e )}')
                            files_excluded +=1 

                self .logger .info (f'Backup created successfully')
                self .logger .info (f'Files included: {files_included }, Files excluded: {files_excluded }')


            backup_size =os .path .getsize (backup_path )
            backup_size_mb =backup_size /(1024 *1024 )
            self .logger .info (f'Backup size: {backup_size_mb :.2f} MB')
            self .logger .info (f'Backup path: {backup_path }')
            self .logger .info ('='*60 )

            return backup_path 

        except Exception as e :
            self .logger .error (f'Error creating backup: {str (e )}')
            raise 

    def list_backups (self ):
        backups =[]
        if os .path .exists (self .backups_dir ):
            for file in os .listdir (self .backups_dir ):
                if file .endswith ('.zip'):
                    file_path =os .path .join (self .backups_dir ,file )
                    file_size =os .path .getsize (file_path )
                    file_size_mb =file_size /(1024 *1024 )
                    mod_time =datetime .fromtimestamp (os .path .getmtime (file_path ))
                    backups .append ({
                    'name':file ,
                    'size_mb':file_size_mb ,
                    'modified':mod_time .strftime ('%Y-%m-%d %H:%M:%S')
                    })

        return sorted (backups ,key =lambda x :x ['modified'],reverse =True )

    def cleanup_old_backups (self ,keep_count =5 ):
        backups =self .list_backups ()

        if len (backups )>keep_count :
            backups_to_delete =backups [keep_count :]

            for backup in backups_to_delete :
                backup_path =os .path .join (self .backups_dir ,backup ['name'])
                try :
                    os .remove (backup_path )
                    self .logger .info (f'Deleted old backup: {backup ["name"]}')
                except Exception as e :
                    self .logger .warning (f'Could not delete {backup ["name"]}: {str (e )}')


def main ():
    import argparse 

    parser =argparse .ArgumentParser (description ='AL Cockie Monster Backup Manager')
    parser .add_argument ('-c','--create',action ='store_true',help ='Create a new backup')
    parser .add_argument ('-l','--list',action ='store_true',help ='List all backups')
    parser .add_argument ('-n','--name',help ='Custom backup name')
    parser .add_argument ('-k','--keep',type =int ,default =5 ,help ='Keep only last N backups (default: 5)')

    args =parser .parse_args ()

    manager =BackupManager ()

    if args .create :
        backup_path =manager .create_backup (args .name )
        print (f'-> Backup created: {backup_path }')


        manager .cleanup_old_backups (args .keep )
        print (f'-> Keeping only the last {args .keep } backups')

    elif args .list :
        backups =manager .list_backups ()
        if backups :
            print ('\nExisting Backups:')
            print ('-'*60 )
            for backup in backups :
                print (f'{backup ["name"]:40} {backup ["size_mb"]:8.2f} MB  {backup ["modified"]}')
            print ('-'*60 )
        else :
            print ('No backups found')

    else :
        parser .print_help ()


if __name__ =='__main__':
    main ()
