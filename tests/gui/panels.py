import customtkinter as ctk 
from tkinter import messagebox 
from managers import FiltersManager ,ConfigManager 


class FilterPanel (ctk .CTkFrame ):

    def __init__ (self ,parent ,on_apply_callback =None ):
        super ().__init__ (parent ,fg_color ="#1f1f1f",corner_radius =8 )

        self .on_apply =on_apply_callback 
        self .selected_filters ={}
        self .checkboxes ={}


        header =ctk .CTkFrame (self ,fg_color ="transparent")
        header .pack (fill ='x',padx =12 ,pady =(12 ,8 ))

        ctk .CTkLabel (header ,text ='🎯 Filtros',
        font =ctk .CTkFont (size =13 ,weight ='bold'),
        text_color ="#4a90e2").pack (side ='left')


        self .expand_btn =ctk .CTkButton (header ,text ='▼',width =30 ,height =30 ,
        command =self ._toggle_filters ,
        fg_color ="#333333",hover_color ="#404040")
        self .expand_btn .pack (side ='right')

        self .is_expanded =True 


        preset_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        preset_frame .pack (fill ='x',padx =12 ,pady =(0 ,8 ))

        ctk .CTkLabel (preset_frame ,text ='📂 Preset:',text_color ="#888888",
        font =ctk .CTkFont (size =10 )).pack (side ='left',padx =(0 ,5 ))

        presets_list =list (FiltersManager .load_filters ().keys ())
        self .preset_var =ctk .StringVar (value ="Nenhum")
        self .preset_menu =ctk .CTkOptionMenu (preset_frame ,variable =self .preset_var ,
        values =["Nenhum"]+presets_list ,
        command =self ._load_preset ,
        fg_color ="#252525",
        button_color ="#404040")
        self .preset_menu .pack (side ='left',fill ='x',expand =True ,padx =(0 ,5 ))


        save_preset_btn =ctk .CTkButton (preset_frame ,text ='💾',width =30 ,
        command =self ._save_new_preset ,
        fg_color ="#2ecc71",hover_color ="#27ae60")
        save_preset_btn .pack (side ='right')


        self .content_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        self .content_frame .pack (fill ='both',expand =True ,padx =0 ,pady =0 )

        self ._populate_filters ()


        button_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        button_frame .pack (fill ='x',padx =12 ,pady =(8 ,12 ))

        ctk .CTkButton (button_frame ,text ='✅ Aplicar',
        command =self ._apply ,
        fg_color ="#2ecc71",hover_color ="#27ae60",
        height =32 ).pack (fill ='x',padx =(0 ,5 ),side ='left',expand =True )

        ctk .CTkButton (button_frame ,text ='🔄 Limpar',
        command =self ._clear ,
        fg_color ="#f39c12",hover_color ="#d68910",
        height =32 ).pack (fill ='x',padx =5 ,side ='left',expand =True )

        ctk .CTkButton (button_frame ,text ='🗑️ Del',
        command =self ._delete_preset ,
        fg_color ="#e74c3c",hover_color ="#c0392b",
        height =32 ,width =40 ).pack (fill ='x',padx =(5 ,0 ),side ='left')

    def _populate_filters (self ):

        filters ={
        "Segurança":{
        "Secure":"secure",
        "HttpOnly":"httponly",
        "SameSite":"samesite"
        },
        "Status":{
        "Não Expirado":"not_expired",
        "Válido":"valid",
        "Ativo":"active"
        },
        "Domínio":{
        "Não Vazio":"domain_not_empty",
        "Específico":"domain_specific"
        }
        }

        scroll =ctk .CTkScrollableFrame (self .content_frame ,fg_color ="transparent")
        scroll .pack (fill ='both',expand =True ,padx =12 ,pady =(0 ,8 ))

        for category ,options in filters .items ():

            ctk .CTkLabel (scroll ,text =f"  {category }",
            font =ctk .CTkFont (size =10 ,weight ='bold'),
            text_color ="#888888").pack (anchor ='w',pady =(6 ,2 ))


            for label ,key in options .items ():
                var =ctk .BooleanVar (value =False )
                checkbox =ctk .CTkCheckBox (scroll ,text =label ,variable =var ,
                text_color ="#e0e0e0",
                checkbox_width =16 ,checkbox_height =16 )
                checkbox .pack (anchor ='w',padx =20 ,pady =1 )
                self .checkboxes [key ]=(var ,checkbox )

    def _toggle_filters (self ):
        if self .is_expanded :
            self .content_frame .pack_forget ()
            self .expand_btn .configure (text ='▶')
            self .is_expanded =False 
        else :
            self .content_frame .pack (fill ='both',expand =True ,padx =0 ,pady =0 )
            self .expand_btn .configure (text ='▼')
            self .is_expanded =True 

    def _load_preset (self ,preset_name ):
        if preset_name =="Nenhum":
            self ._clear ()
            return 

        presets =FiltersManager .load_filters ()
        if preset_name in presets :

            for var ,_ in self .checkboxes .values ():
                var .set (False )


            preset_filters =presets [preset_name ]
            for key in preset_filters :
                if key in self .checkboxes :
                    self .checkboxes [key ][0 ].set (True )

    def _save_new_preset (self ):
        dialog =ctk .CTkInputDialog (text ="Nome do novo preset:",title ="Salvar Preset")
        name =dialog .get_input ()

        if name :
            name =name .strip ()
            if not name :
                messagebox .showwarning ("Erro","Nome inválido")
                return 


            current ={k :var .get ()for k ,(var ,_ )in self .checkboxes .items ()if var .get ()}

            if not current :
                messagebox .showwarning ("Aviso","Selecione pelo menos um filtro")
                return 


            presets =FiltersManager .load_filters ()
            presets [name ]=current 
            FiltersManager .save_filters (presets )


            current_presets =list (presets .keys ())
            self .preset_menu .configure (values =["Nenhum"]+current_presets )
            self .preset_var .set (name )

            messagebox .showinfo ("Sucesso",f"Preset '{name }' salvo!")

    def _delete_preset (self ):
        current =self .preset_var .get ()
        if current =="Nenhum":
            messagebox .showwarning ("Aviso","Selecione um preset para deletar")
            return 

        if messagebox .askyesno ("Confirmar",f"Deletar preset '{current }'?"):
            FiltersManager .delete_filter (current )


            presets =FiltersManager .load_filters ()
            current_presets =list (presets .keys ())
            self .preset_menu .configure (values =["Nenhum"]+current_presets )
            self .preset_var .set ("Nenhum")
            self ._clear ()

            messagebox .showinfo ("Sucesso","Preset deletado!")

    def _clear (self ):
        for var ,_ in self .checkboxes .values ():
            var .set (False )
        self .preset_var .set ("Nenhum")

    def _apply (self ):
        selected ={k :True for k ,(var ,_ )in self .checkboxes .items ()if var .get ()}

        if not selected :
            messagebox .showwarning ("Aviso","Selecione pelo menos um filtro")
            return 

        if self .on_apply :
            self .on_apply (selected )


class SettingsPanel (ctk .CTkFrame ):

    def __init__ (self ,parent ,on_save_callback =None ):
        super ().__init__ (parent ,fg_color ="#1f1f1f",corner_radius =8 )

        self .on_save =on_save_callback 
        self .config =ConfigManager .load_config ()
        self .entries ={}
        self .sliders ={}


        header =ctk .CTkFrame (self ,fg_color ="transparent")
        header .pack (fill ='x',padx =12 ,pady =(12 ,8 ))

        ctk .CTkLabel (header ,text ='⚙️ Configurações',
        font =ctk .CTkFont (size =13 ,weight ='bold'),
        text_color ="#34495e").pack (side ='left')


        self .expand_btn =ctk .CTkButton (header ,text ='▼',width =30 ,height =30 ,
        command =self ._toggle_settings ,
        fg_color ="#333333",hover_color ="#404040")
        self .expand_btn .pack (side ='right')

        self .is_expanded =True 


        self .content_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        self .content_frame .pack (fill ='both',expand =True ,padx =12 ,pady =(0 ,8 ))

        self ._add_config_item ("🔄 Threads","max_workers",1 ,16 ,
        "Número de processamentos simultâneos")
        self ._add_config_item ("⏱️ Val.","timeout_validate",5 ,60 ,
        "Timeout validação (s)")
        self ._add_config_item ("⏱️ Filter","timeout_filter",5 ,60 ,
        "Timeout filtros (s)")
        self ._add_config_item ("⏱️ Análise","timeout_analyze",5 ,60 ,
        "Timeout análise (s)")


        button_frame =ctk .CTkFrame (self ,fg_color ="transparent")
        button_frame .pack (fill ='x',padx =12 ,pady =(8 ,12 ))

        ctk .CTkButton (button_frame ,text ='💾 Salvar',
        command =self ._save ,
        fg_color ="#2ecc71",hover_color ="#27ae60",
        height =32 ).pack (fill ='x',padx =(0 ,5 ),side ='left',expand =True )

        ctk .CTkButton (button_frame ,text ='🔄 Reset',
        command =self ._reset ,
        fg_color ="#f39c12",hover_color ="#d68910",
        height =32 ).pack (fill ='x',padx =5 ,side ='left',expand =True )

    def _add_config_item (self ,label ,key ,min_val ,max_val ,tooltip ):
        current =self .config .get (key ,4 )


        item =ctk .CTkFrame (self .content_frame ,fg_color ="transparent")
        item .pack (fill ='x',pady =8 )


        top =ctk .CTkFrame (item ,fg_color ="transparent")
        top .pack (fill ='x')

        ctk .CTkLabel (top ,text =label ,font =ctk .CTkFont (size =10 ,weight ='bold'),
        text_color ="#e0e0e0").pack (side ='left')

        value_label =ctk .CTkLabel (top ,text =str (current ),text_color ="#4a90e2",
        font =ctk .CTkFont (size =10 ,weight ='bold'))
        value_label .pack (side ='right')


        slider =ctk .CTkSlider (item ,from_ =min_val ,to =max_val ,
        number_of_steps =max_val -min_val ,
        command =lambda v :value_label .configure (text =str (int (v ))))
        slider .pack (fill ='x',pady =(4 ,0 ))
        slider .set (current )


        ctk .CTkLabel (item ,text =tooltip ,text_color ="#666666",
        font =ctk .CTkFont (size =8 )).pack (anchor ='w',pady =(2 ,0 ))

        self .sliders [key ]=slider 

    def _toggle_settings (self ):
        if self .is_expanded :
            self .content_frame .pack_forget ()
            self .expand_btn .configure (text ='▶')
            self .is_expanded =False 
        else :
            self .content_frame .pack (fill ='both',expand =True ,padx =12 ,pady =(0 ,8 ))
            self .expand_btn .configure (text ='▼')
            self .is_expanded =True 

    def _save (self ):
        new_config ={}
        for key ,slider in self .sliders .items ():
            new_config [key ]=int (slider .get ())

        ConfigManager .save_config (new_config )

        if self .on_save :
            self .on_save (new_config )

        messagebox .showinfo ("Sucesso","Configurações salvas!")

    def _reset (self ):
        if messagebox .askyesno ("Confirmar","Restaurar configurações padrão?"):
            default ={
            'max_workers':4 ,
            'timeout_validate':10 ,
            'timeout_filter':15 ,
            'timeout_analyze':20 
            }
            ConfigManager .save_config (default )


            for key ,slider in self .sliders .items ():
                slider .set (default [key ])

            if self .on_save :
                self .on_save (default )

            messagebox .showinfo ("Sucesso","Padrões restaurados!")
