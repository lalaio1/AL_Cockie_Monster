import tkinter as tk 
from tkinter import messagebox 
import customtkinter as ctk 
import json 
from managers import FiltersManager 


class FilterDialog (ctk .CTkToplevel ):
    def __init__ (self ,parent ,available_filters ):
        super ().__init__ (parent )
        self .title ("Gerenciador de Filtros")
        self .geometry ("600x500")
        self .resizable (True ,True )

        self .available_filters =available_filters 
        self .selected_filters ={}


        header =ctk .CTkFrame (self ,fg_color ="#0d0d0d")
        header .pack (fill ='x',padx =0 ,pady =0 )

        ctk .CTkLabel (header ,text ='🎯 Gerenciar Filtros',
        font =ctk .CTkFont (size =16 ,weight ='bold'),
        text_color ="#4a90e2").pack (anchor ='w',padx =20 ,pady =15 )


        main =ctk .CTkFrame (self ,fg_color ="#1a1a1a")
        main .pack (fill ='both',expand =True ,padx =15 ,pady =15 )


        left =ctk .CTkFrame (main ,fg_color ="#1f1f1f",corner_radius =8 )
        left .pack (side ='left',fill ='both',expand =True ,padx =(0 ,8 ))

        ctk .CTkLabel (left ,text ='Filtros Disponíveis',
        font =ctk .CTkFont (size =12 ,weight ='bold'),
        text_color ="#4a90e2").pack (anchor ='w',padx =12 ,pady =(12 ,8 ))

        self .available_frame =ctk .CTkScrollableFrame (left ,fg_color ="transparent")
        self .available_frame .pack (fill ='both',expand =True ,padx =12 ,pady =(0 ,12 ))


        right =ctk .CTkFrame (main ,fg_color ="#1f1f1f",corner_radius =8 )
        right .pack (side ='right',fill ='both',expand =True ,padx =(8 ,0 ))

        ctk .CTkLabel (right ,text ='Filtros Selecionados',
        font =ctk .CTkFont (size =12 ,weight ='bold'),
        text_color ="#f39c12").pack (anchor ='w',padx =12 ,pady =(12 ,8 ))

        self .selected_frame =ctk .CTkScrollableFrame (right ,fg_color ="transparent")
        self .selected_frame .pack (fill ='both',expand =True ,padx =12 ,pady =(0 ,12 ))


        self ._populate_available ()


        btn_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        btn_frame .pack (fill ='x',padx =15 ,pady =(0 ,15 ))

        ctk .CTkButton (btn_frame ,text ='✅ Aplicar',command =self ._apply_filters ,
        fg_color ="#2ecc71",hover_color ="#27ae60",width =100 ).pack (side ='left',padx =5 )

        ctk .CTkButton (btn_frame ,text ='💾 Salvar Preset',command =self ._save_preset ,
        fg_color ="#3498db",hover_color ="#2980b9",width =120 ).pack (side ='left',padx =5 )

        ctk .CTkButton (btn_frame ,text ='❌ Cancelar',command =self .destroy ,
        fg_color ="#e74c3c",hover_color ="#c0392b",width =100 ).pack (side ='right',padx =5 )

        self .result =None 

    def _populate_available (self ):
        for group ,info in self .available_filters .items ():
            lbl =ctk .CTkLabel (self .available_frame ,text =f"📌 {group }",
            font =ctk .CTkFont (size =11 ,weight ='bold'),
            text_color ="#4a90e2")
            lbl .pack (anchor ='w',padx =0 ,pady =(8 ,4 ))

            for opt in info .get ('options',[]):
                var =tk .BooleanVar (value =False )
                cb =ctk .CTkCheckBox (self .available_frame ,text =opt ,variable =var ,
                text_color ="#e0e0e0",checkbox_width =18 ,checkbox_height =18 )
                cb .pack (anchor ='w',padx =12 ,pady =2 )
                self .selected_filters [opt ]=var 

    def _apply_filters (self ):
        self .result ={k :v .get ()for k ,v in self .selected_filters .items ()if v .get ()}
        self .destroy ()

    def _save_preset (self ):
        dialog =ctk .CTkInputDialog (text ="Nome do preset:",title ="Salvar Preset")
        name =dialog .get_input ()
        if name :
            filters_dict =FiltersManager .load_filters ()
            filters_dict [name ]={k :v .get ()for k ,v in self .selected_filters .items ()if v .get ()}
            if FiltersManager .save_filters (filters_dict ):
                messagebox .showinfo ("Sucesso",f"Preset '{name }' salvo!")
            else :
                messagebox .showerror ("Erro","Falha ao salvar preset")

    def get_result (self ):
        return self .result if self .result else {}


class PresetsDialog (ctk .CTkToplevel ):
    def __init__ (self ,parent ):
        super ().__init__ (parent )
        self .title ("Carregador de Presets")
        self .geometry ("400x350")

        self .result =None 


        header =ctk .CTkFrame (self ,fg_color ="#0d0d0d")
        header .pack (fill ='x',padx =0 ,pady =0 )

        ctk .CTkLabel (header ,text ='📂 Presets de Filtros',
        font =ctk .CTkFont (size =14 ,weight ='bold'),
        text_color ="#4a90e2").pack (anchor ='w',padx =20 ,pady =15 )


        main =ctk .CTkFrame (self ,fg_color ="#1a1a1a")
        main .pack (fill ='both',expand =True ,padx =15 ,pady =15 )


        list_frame =ctk .CTkFrame (main ,fg_color ="#1f1f1f",corner_radius =8 )
        list_frame .pack (fill ='both',expand =True ,padx =0 ,pady =0 )

        presets =FiltersManager .get_filter_names ()

        if not presets :
            ctk .CTkLabel (list_frame ,text ='Nenhum preset salvo',
            text_color ="#888888").pack (pady =30 )
        else :
            scroll =ctk .CTkScrollableFrame (list_frame ,fg_color ="transparent")
            scroll .pack (fill ='both',expand =True ,padx =12 ,pady =12 )

            for preset_name in presets :
                btn_frame =ctk .CTkFrame (scroll ,fg_color ="#252525",corner_radius =6 )
                btn_frame .pack (fill ='x',pady =5 )

                ctk .CTkLabel (btn_frame ,text =preset_name ,
                font =ctk .CTkFont (size =11 ,weight ='bold'),
                text_color ="#e0e0e0").pack (anchor ='w',padx =12 ,pady =(8 ,2 ))

                btn_sub =ctk .CTkFrame (btn_frame ,fg_color ="transparent")
                btn_sub .pack (fill ='x',padx =12 ,pady =(2 ,8 ))

                ctk .CTkButton (btn_sub ,text ='✅ Usar',width =60 ,
                command =lambda n =preset_name :self ._select_preset (n ),
                fg_color ="#2ecc71",hover_color ="#27ae60").pack (side ='left',padx =5 )

                ctk .CTkButton (btn_sub ,text ='🗑️ Deletar',width =60 ,
                command =lambda n =preset_name :self ._delete_preset (n ),
                fg_color ="#e74c3c",hover_color ="#c0392b").pack (side ='left',padx =5 )


        btn_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        btn_frame .pack (fill ='x',padx =15 ,pady =(0 ,15 ))

        ctk .CTkButton (btn_frame ,text ='❌ Fechar',command =self .destroy ,
        fg_color ="#34495e",hover_color ="#2c3e50",width =100 ).pack (side ='right')

    def _select_preset (self ,name ):
        filters =FiltersManager .load_filters ()
        self .result =filters .get (name ,{})
        self .destroy ()

    def _delete_preset (self ,name ):
        if messagebox .askyesno ("Confirmar",f"Deletar preset '{name }'?"):
            if FiltersManager .delete_filter (name ):
                messagebox .showinfo ("Sucesso","Preset deletado!")
                self .destroy ()
            else :
                messagebox .showerror ("Erro","Falha ao deletar")

    def get_result (self ):
        return self .result if self .result else None 
