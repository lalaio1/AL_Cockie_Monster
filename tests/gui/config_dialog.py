import customtkinter as ctk 
from managers import ConfigManager 


class ConfigDialog (ctk .CTkToplevel ):
    def __init__ (self ,parent ,on_config_change =None ):
        super ().__init__ (parent )
        self .title ("⚙️ Configurações")
        self .geometry ("500x400")
        self .resizable (False ,True )

        self .on_config_change =on_config_change 
        self .config =ConfigManager .load_config ()


        header =ctk .CTkFrame (self ,fg_color ="#0d0d0d")
        header .pack (fill ='x',padx =0 ,pady =0 )

        ctk .CTkLabel (header ,text ='⚙️ Configurações da Aplicação',
        font =ctk .CTkFont (size =16 ,weight ='bold'),
        text_color ="#4a90e2").pack (anchor ='w',padx =20 ,pady =15 )


        main =ctk .CTkFrame (self ,fg_color ="#1a1a1a")
        main .pack (fill ='both',expand =True ,padx =20 ,pady =20 )


        settings_frame =ctk .CTkScrollableFrame (main ,fg_color ="transparent")
        settings_frame .pack (fill ='both',expand =True )


        self ._add_setting (settings_frame ,
        "🔄 Número de Threads (Workers)",
        "Aumentar torna o processamento mais rápido (cuidado com o CPU)",
        "max_workers","int",1 ,16 )


        self ._add_setting (settings_frame ,
        "⏱️ Timeout de Validação (segundos)",
        "Tempo máximo para validar cookies",
        "timeout_validate","int",5 ,60 )


        self ._add_setting (settings_frame ,
        "⏱️ Timeout de Filtros (segundos)",
        "Tempo máximo para aplicar filtros",
        "timeout_filter","int",5 ,60 )


        self ._add_setting (settings_frame ,
        "⏱️ Timeout de Análise (segundos)",
        "Tempo máximo para análise de segurança",
        "timeout_analyze","int",5 ,60 )


        btn_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        btn_frame .pack (fill ='x',padx =20 ,pady =(0 ,20 ))

        ctk .CTkButton (btn_frame ,text ='💾 Salvar',command =self ._save_config ,
        fg_color ="#2ecc71",hover_color ="#27ae60",width =100 ).pack (side ='left',padx =5 )

        ctk .CTkButton (btn_frame ,text ='🔄 Restaurar Padrão',command =self ._restore_default ,
        fg_color ="#f39c12",hover_color ="#d68910",width =150 ).pack (side ='left',padx =5 )

        ctk .CTkButton (btn_frame ,text ='❌ Cancelar',command =self .destroy ,
        fg_color ="#e74c3c",hover_color ="#c0392b",width =100 ).pack (side ='right',padx =5 )

        self .entries ={}

    def _add_setting (self ,parent ,title ,description ,key ,input_type ,min_val =None ,max_val =None ):
        frame =ctk .CTkFrame (parent ,fg_color ="#1f1f1f",corner_radius =6 )
        frame .pack (fill ='x',pady =(0 ,15 ))


        ctk .CTkLabel (frame ,text =title ,
        font =ctk .CTkFont (size =11 ,weight ='bold'),
        text_color ="#e0e0e0").pack (anchor ='w',padx =15 ,pady =(12 ,4 ))


        ctk .CTkLabel (frame ,text =description ,
        font =ctk .CTkFont (size =9 ),
        text_color ="#888888").pack (anchor ='w',padx =15 ,pady =(0 ,8 ))


        if input_type =="int":
            value =self .config .get (key ,4 )

            input_frame =ctk .CTkFrame (frame ,fg_color ="transparent")
            input_frame .pack (fill ='x',padx =15 ,pady =(0 ,12 ))

            entry =ctk .CTkEntry (input_frame ,width =100 ,height =32 )
            entry .pack (side ='left',padx =(0 ,10 ))
            entry .insert (0 ,str (value ))

            if min_val is not None and max_val is not None :
                slider =ctk .CTkSlider (input_frame ,from_ =min_val ,to =max_val ,
                number_of_steps =max_val -min_val ,
                command =lambda v :entry .delete (0 ,'end')or entry .insert (0 ,str (int (v ))))
                slider .pack (side ='left',fill ='x',expand =True )
                slider .set (value )

            self .entries [key ]=entry 

    def _save_config (self ):
        try :
            new_config ={}
            for key ,entry in self .entries .items ():
                try :
                    value =int (entry .get ())
                    new_config [key ]=value 
                except ValueError :
                    new_config [key ]=self .config [key ]

            ConfigManager .save_config (new_config )


            if self .on_config_change :
                self .on_config_change (new_config )

            from tkinter import messagebox 
            messagebox .showinfo ("Sucesso","Configurações salvas com sucesso!")
            self .destroy ()
        except Exception as e :
            from tkinter import messagebox 
            messagebox .showerror ("Erro",f"Falha ao salvar: {e }")

    def _restore_default (self ):
        from tkinter import messagebox 

        default ={
        'max_workers':4 ,
        'timeout_validate':10 ,
        'timeout_filter':15 ,
        'timeout_analyze':20 
        }

        if messagebox .askyesno ("Confirmar","Restaurar configurações padrão?"):
            ConfigManager .save_config (default )
            if self .on_config_change :
                self .on_config_change (default )
            messagebox .showinfo ("Sucesso","Configurações restauradas!")
            self .destroy ()
