import os 
import threading 
import requests 
import json 
import tkinter as tk 
from tkinter import filedialog ,messagebox ,ttk 
import customtkinter as ctk 
from datetime import datetime 
import concurrent .futures 

from config_gui import API_BASE ,MAX_WORKERS 
from dialogs import FilePreviewWindow ,ExportDialog 
from managers import FiltersManager ,ConfigManager 
from panels import FilterPanel ,SettingsPanel 

ctk .set_appearance_mode ('dark')
ctk .set_default_color_theme ('blue')


class CockieMonsterGUI (ctk .CTk ):
    def __init__ (self ):
        super ().__init__ ()
        self .title ("Cockie Monster Pro")
        self .geometry ("1400x900")
        self .current_folder =None 
        self .files =[]
        self .max_workers =MAX_WORKERS 
        self .active_workers =0 
        self .lock =threading .Lock ()
        self .executor =concurrent .futures .ThreadPoolExecutor (max_workers =self .max_workers )
        self .protocol ("WM_DELETE_WINDOW",self ._on_close )


        self .color_bg ="#1a1a1a"
        self .color_fg ="#e0e0e0"
        self .color_accent ="#4a90e2"
        self .color_success ="#2ecc71"
        self .color_warning ="#f39c12"
        self .color_error ="#e74c3c"


        header =ctk .CTkFrame (self ,fg_color ="#0d0d0d",corner_radius =0 )
        header .pack (fill ='x',padx =0 ,pady =0 )

        title_frame =ctk .CTkFrame (header ,fg_color ="#0d0d0d")
        title_frame .pack (side ='left',padx =20 ,pady =15 )

        ctk .CTkLabel (title_frame ,text ='🍪 Cockie Monster Pro',
        font =ctk .CTkFont (size =28 ,weight ='bold'),text_color =self .color_accent ).pack (anchor ='w')
        ctk .CTkLabel (title_frame ,text ='Análise Inteligente de Cookies',
        font =ctk .CTkFont (size =12 ),text_color ="#888888").pack (anchor ='w')


        toolbar =ctk .CTkFrame (self ,fg_color ="#242424",corner_radius =0 )
        toolbar .pack (fill ='x',padx =0 ,pady =0 )

        btn_frame =ctk .CTkFrame (toolbar ,fg_color ="#242424")
        btn_frame .pack (side ='left',padx =15 ,pady =10 ,fill ='x',expand =True )

        self .btn_select =ctk .CTkButton (btn_frame ,text ='📁 Selecionar Pasta',
        command =self .select_folder ,width =140 ,
        fg_color =self .color_accent ,hover_color ="#3a7bc8")
        self .btn_select .grid (row =0 ,column =0 ,padx =8 ,pady =6 )

        self .btn_scan =ctk .CTkButton (btn_frame ,text ='🔍 Scan Recursivo',
        command =self .scan_selected_folder ,width =140 ,
        fg_color ="#2ecc71",hover_color ="#27ae60")
        self .btn_scan .grid (row =0 ,column =1 ,padx =8 ,pady =6 )

        self .btn_apply =ctk .CTkButton (btn_frame ,text ='⚙️ Aplicar Filtros',
        command =self .apply_filters_selected ,width =140 ,
        fg_color ="#f39c12",hover_color ="#d68910")
        self .btn_apply .grid (row =0 ,column =2 ,padx =8 ,pady =6 )

        self .btn_analyze =ctk .CTkButton (btn_frame ,text ='📊 Analisar',
        command =self .analyze_selected ,width =130 ,
        fg_color ="#9b59b6",hover_color ="#8e44ad")
        self .btn_analyze .grid (row =0 ,column =3 ,padx =8 ,pady =6 )

        self .btn_export =ctk .CTkButton (btn_frame ,text ='💾 Exportar',
        command =self .export_results ,width =120 ,
        fg_color ="#3498db",hover_color ="#2980b9")
        self .btn_export .grid (row =0 ,column =4 ,padx =8 ,pady =6 )

        self .btn_help =ctk .CTkButton (btn_frame ,text ='ℹ️ Help',
        command =self .show_help ,width =100 ,
        fg_color ="#34495e",hover_color ="#2c3e50")
        self .btn_help .grid (row =0 ,column =5 ,padx =8 ,pady =6 )


        content =ctk .CTkFrame (self ,fg_color =self .color_bg )
        content .pack (fill ='both',expand =True ,padx =10 ,pady =10 )


        left_panel =ctk .CTkFrame (content ,fg_color ="#1f1f1f",corner_radius =8 )
        left_panel .pack (side ='left',fill ='both',expand =True ,padx =(0 ,8 ),pady =0 )


        title_left =ctk .CTkLabel (left_panel ,text ='📝 Arquivos Encontrados',
        font =ctk .CTkFont (size =14 ,weight ='bold'),
        text_color =self .color_accent )
        title_left .pack (fill ='x',padx =15 ,pady =(15 ,10 ))


        tree_container =ctk .CTkFrame (left_panel ,fg_color ="#1f1f1f")
        tree_container .pack (fill ='both',expand =True ,padx =12 ,pady =(0 ,12 ))

        tree_style =ttk .Style ()
        tree_style .theme_use ("clam")
        tree_style .configure ("Treeview",background ="#2a2a2a",foreground ="#e0e0e0",
        fieldbackground ="#2a2a2a",borderwidth =0 ,font =('Arial',10 ))
        tree_style .configure ("Treeview.Heading",background ="#333333",foreground ="#e0e0e0",
        borderwidth =0 ,font =('Arial',10 ,'bold'))
        tree_style .map ('Treeview',background =[('selected',self .color_accent )])
        tree_style .map ('Treeview.Heading',background =[('active','#404040')])

        self .tree =ttk .Treeview (tree_container ,columns =('status','cookies','path'),
        show ='headings',selectmode ='extended',height =15 )
        self .tree .heading ('status',text ='Status')
        self .tree .heading ('cookies',text ='Cookies')
        self .tree .heading ('path',text ='Caminho')
        self .tree .column ('status',width =120 )
        self .tree .column ('cookies',width =80 )
        self .tree .column ('path',width =400 )

        v_scrollbar =ttk .Scrollbar (tree_container ,orient ="vertical",command =self .tree .yview )
        h_scrollbar =ttk .Scrollbar (tree_container ,orient ="horizontal",command =self .tree .xview )
        self .tree .configure (yscrollcommand =v_scrollbar .set ,xscrollcommand =h_scrollbar .set )

        self .tree .grid (row =0 ,column =0 ,sticky ="nsew")
        v_scrollbar .grid (row =0 ,column =1 ,sticky ="ns")
        h_scrollbar .grid (row =1 ,column =0 ,sticky ="ew")

        tree_container .grid_rowconfigure (0 ,weight =1 )
        tree_container .grid_columnconfigure (0 ,weight =1 )

        self .tree .bind ("<Double-1>",self .on_file_double_click )


        right_panel =ctk .CTkScrollableFrame (content ,fg_color ="#1f1f1f",corner_radius =8 )
        right_panel .pack (side ='right',fill ='both',expand =False ,padx =(8 ,0 ),pady =0 ,ipadx =0 ,ipady =0 )
        right_panel .configure (width =300 )


        stats_label =ctk .CTkLabel (right_panel ,text ='📈 Estatísticas',
        font =ctk .CTkFont (size =13 ,weight ='bold'),
        text_color =self .color_success )
        stats_label .pack (fill ='x',padx =12 ,pady =(12 ,8 ))


        stats_card_frame =ctk .CTkFrame (right_panel ,fg_color ="transparent")
        stats_card_frame .pack (fill ='x',padx =0 ,pady =(0 ,12 ))


        card1 =ctk .CTkFrame (stats_card_frame ,fg_color ="#252525",corner_radius =6 )
        card1 .pack (fill ='x',pady =(0 ,6 ),padx =12 )
        ctk .CTkLabel (card1 ,text ='Total',font =ctk .CTkFont (size =10 ),
        text_color ="#888888").pack (anchor ='w',padx =10 ,pady =(6 ,1 ))
        self .lbl_total =ctk .CTkLabel (card1 ,text ='0',font =ctk .CTkFont (size =16 ,weight ='bold'),
        text_color =self .color_accent )
        self .lbl_total .pack (anchor ='w',padx =10 ,pady =(0 ,6 ))


        card2 =ctk .CTkFrame (stats_card_frame ,fg_color ="#252525",corner_radius =6 )
        card2 .pack (fill ='x',pady =(0 ,6 ),padx =12 )
        ctk .CTkLabel (card2 ,text ='Processados',font =ctk .CTkFont (size =10 ),
        text_color ="#888888").pack (anchor ='w',padx =10 ,pady =(6 ,1 ))
        self .lbl_processed =ctk .CTkLabel (card2 ,text ='0/0',font =ctk .CTkFont (size =16 ,weight ='bold'),
        text_color =self .color_success )
        self .lbl_processed .pack (anchor ='w',padx =10 ,pady =(0 ,6 ))


        card3 =ctk .CTkFrame (stats_card_frame ,fg_color ="#252525",corner_radius =6 )
        card3 .pack (fill ='x',pady =(0 ,6 ),padx =12 )
        ctk .CTkLabel (card3 ,text ='Completos',font =ctk .CTkFont (size =10 ),
        text_color ="#888888").pack (anchor ='w',padx =10 ,pady =(6 ,1 ))
        self .lbl_completed =ctk .CTkLabel (card3 ,text ='0',font =ctk .CTkFont (size =16 ,weight ='bold'),
        text_color ="#2ecc71")
        self .lbl_completed .pack (anchor ='w',padx =10 ,pady =(0 ,6 ))


        card4 =ctk .CTkFrame (stats_card_frame ,fg_color ="#252525",corner_radius =6 )
        card4 .pack (fill ='x',padx =12 )
        ctk .CTkLabel (card4 ,text ='Cookies',font =ctk .CTkFont (size =10 ),
        text_color ="#888888").pack (anchor ='w',padx =10 ,pady =(6 ,1 ))
        self .lbl_cookies =ctk .CTkLabel (card4 ,text ='0',font =ctk .CTkFont (size =16 ,weight ='bold'),
        text_color =self .color_warning )
        self .lbl_cookies .pack (anchor ='w',padx =10 ,pady =(0 ,6 ))


        progress_label =ctk .CTkLabel (right_panel ,text ='Progresso',
        font =ctk .CTkFont (size =10 ),text_color ="#888888")
        progress_label .pack (anchor ='w',padx =12 ,pady =(12 ,4 ))
        self .progress_bar =ctk .CTkProgressBar (right_panel ,fg_color ="#333333",height =6 )
        self .progress_bar .pack (fill ='x',padx =12 ,pady =(0 ,12 ))
        self .progress_bar .set (0 )


        sep =ctk .CTkFrame (right_panel ,fg_color ="#333333",height =1 )
        sep .pack (fill ='x',padx =0 ,pady =(0 ,12 ))


        self .filter_panel =FilterPanel (right_panel ,on_apply_callback =self .apply_filters_from_panel )
        self .filter_panel .pack (fill ='x',padx =0 ,pady =(0 ,12 ))


        sep2 =ctk .CTkFrame (right_panel ,fg_color ="#333333",height =1 )
        sep2 .pack (fill ='x',padx =0 ,pady =(0 ,12 ))


        self .settings_panel =SettingsPanel (right_panel ,on_save_callback =self .save_config_from_panel )
        self .settings_panel .pack (fill ='x',padx =0 ,pady =(0 ,12 ))


        log_frame =ctk .CTkFrame (self ,fg_color ="#1f1f1f",corner_radius =8 )
        log_frame .pack (fill ='x',padx =10 ,pady =(0 ,10 ))

        log_label =ctk .CTkLabel (log_frame ,text ='📋 Log de Atividade',
        font =ctk .CTkFont (size =12 ,weight ='bold'),
        text_color ="#888888")
        log_label .pack (anchor ='w',padx =15 ,pady =(12 ,8 ))

        self .log =tk .Text (log_frame ,height =5 ,bg ='#2a2a2a',fg ='#e0e0e0',
        relief ="flat",borderwidth =0 ,wrap ="word",font =('Courier',9 ))
        scrollbar =ctk .CTkScrollbar (log_frame ,command =self .log .yview )
        self .log .configure (yscrollcommand =scrollbar .set )

        self .log .pack (side ='left',fill ='both',expand =True ,padx =(15 ,0 ),pady =(0 ,12 ))
        scrollbar .pack (side ='right',fill ='y',pady =(0 ,12 ),padx =(0 ,15 ))

        self .update_stats ()

    def log_message (self ,msg ):
        timestamp =datetime .now ().strftime ("%H:%M:%S")
        try :
            self .log .insert ('end',f"[{timestamp }] {msg }\n")
            self .log .see ('end')
        except tk .TclError :
            pass 
        self .after (100 ,self .update_stats )

    def apply_filters_from_panel (self ,selected_filters ):
        selected_items =self .tree .selection ()
        if not selected_items :
            messagebox .showwarning ("Aviso","Selecione arquivos para filtrar")
            return 

        self .log_message (f"🎯 Aplicando {len (selected_filters )} filtro(s)...")
        for item_id in selected_items :
            self ._apply_filters_wrapper (item_id ,selected_filters )

    def save_config_from_panel (self ,config ):
        self .max_workers =config .get ('max_workers',4 )
        self .log_message (f"⚙️ Configurações atualizadas")

    def update_stats (self ):
        total_files =len (self .files )
        pending =0 
        processed =0 
        completed =0 

        for item in self .tree .get_children ():
            try :
                values =self .tree .item (item )['values']
                if values and len (values )>0 :
                    status =values [0 ]
                    if '⏳'in status :
                        pending +=1 
                    elif '⚠️'in status or '❌'in status :
                        processed +=1 
                    elif '✅'in status or '🔽'in status :
                        completed +=1 
            except tk .TclError :
                pass 

        total_cookies =0 
        for item in self .tree .get_children ():
            try :
                values =self .tree .item (item )['values']
                if values and len (values )>1 :
                    cookies_val =values [1 ]
                    try :
                        if isinstance (cookies_val ,str )and cookies_val .isdigit ():
                            total_cookies +=int (cookies_val )
                        elif isinstance (cookies_val ,int ):
                            total_cookies +=cookies_val 
                    except (ValueError ,TypeError ):
                        pass 
            except tk .TclError :
                pass 


        try :
            self .lbl_total .configure (text =str (total_files ))
            self .lbl_processed .configure (text =f"{processed }/{total_files }")
            self .lbl_completed .configure (text =str (completed ))
            self .lbl_cookies .configure (text =str (total_cookies ))
        except tk .TclError :
            pass 

    def select_folder (self ):
        path =filedialog .askdirectory ()
        if path :
            self .current_folder =path 
            self .log_message (f'✅ Pasta selecionada: {path }')
            self .populate_files ()

    def populate_files (self ):
        for item in self .tree .get_children ():
            self .tree .delete (item )
        self .files =[]
        if not self .current_folder :
            return 
        for root ,dirs ,files in os .walk (self .current_folder ):
            for fn in files :
                if fn .lower ().endswith ('.txt'):
                    full =os .path .join (root ,fn )
                    rel_path =os .path .relpath (full ,self .current_folder )
                    self .files .append (full )
                    self .tree .insert ('','end',iid =full ,values =('⏳ Pendente','0',rel_path ))
        self .log_message (f'🔍 {len (self .files )} arquivos .txt encontrados (recursivo)')
        self .update_stats ()

    def scan_selected_folder (self ):
        if not self .current_folder :
            messagebox .showwarning ('Aviso','Selecione uma pasta primeiro')
            return 
        if not self .files :
            messagebox .showwarning ('Aviso','Nenhum arquivo encontrado')
            return 

        for item in self .tree .get_children ():
            self .tree .set (item ,'status','⏳ Pendente')
            self .tree .set (item ,'cookies','0')

        with self .lock :
            self .active_workers =0 
        self .progress_bar .set (0 )

        for fpath in self .files :
            try :
                self .executor .submit (self ._scan_worker_wrapper ,fpath )
            except Exception as e :
                self .log_message (f'❌ Erro ao agendar {os .path .basename (fpath )}: {e }')

    def _scan_worker_single (self ,fpath ):
        try :
            with open (fpath ,'r',encoding ='utf-8',errors ='ignore')as fh :
                content =fh .read ()
            resp =requests .post (f"{API_BASE }/api/validate",json ={'cookies_text':content },timeout =10 )
            if resp .status_code ==200 :
                data =resp .json ()
                total =data .get ('total_cookies',0 )
                status ='✅ OK'if total >0 else '⚠️ Vazio'
                self .after (0 ,lambda :self ._update_tree_item (fpath ,status ,str (total )))
                self .log_message (f'{os .path .basename (fpath )} → {status } ({total })')
            else :
                self .after (0 ,lambda :self ._update_tree_item (fpath ,'❌ Erro API','0'))
                self .log_message (f'❌ API error {resp .status_code }: {os .path .basename (fpath )}')
        except Exception as e :
            self .after (0 ,lambda :self ._update_tree_item (fpath ,'❌ Erro','0'))
            self .log_message (f'❌ {os .path .basename (fpath )}: {str (e )[:50 ]}')

    def _scan_worker_wrapper (self ,fpath ):
        with self .lock :
            self .active_workers +=1 
        try :
            self ._scan_worker_single (fpath )
        finally :
            with self .lock :
                self .active_workers =max (0 ,self .active_workers -1 )
            self .after (0 ,self ._update_progress )

    def _apply_filters_wrapper (self ,fpath ,filters ):
        with self .lock :
            self .active_workers +=1 
        try :
            self ._apply_filters_single (fpath ,filters )
        finally :
            with self .lock :
                self .active_workers =max (0 ,self .active_workers -1 )
            self .after (0 ,self ._update_progress )

    def _analyze_wrapper (self ,fpath ):
        with self .lock :
            self .active_workers +=1 
        try :
            self ._analyze_single (fpath )
        finally :
            with self .lock :
                self .active_workers =max (0 ,self .active_workers -1 )
            self .after (0 ,self ._update_progress )

    def _on_close (self ):
        try :
            self .executor .shutdown (wait =False )
        except Exception :
            pass 
        try :
            self .destroy ()
        except Exception :
            pass 

    def _update_tree_item (self ,fpath ,status ,cookies ):
        try :
            if fpath in self .tree .get_children ():
                self .tree .set (fpath ,'status',status )
                self .tree .set (fpath ,'cookies',cookies )
                self .after (10 ,self .update_stats )
        except tk .TclError :
            pass 

    def _update_progress (self ):
        try :
            total =len (self .files )
            if total ==0 :
                self .progress_bar .set (0 )
                return 

            processed =0 
            for item in self .tree .get_children ():
                try :
                    values =self .tree .item (item )['values']
                    if values and len (values )>0 and '⏳'not in values [0 ]:
                        processed +=1 
                except tk .TclError :
                    pass 

            progress =processed /total if total >0 else 0 
            self .progress_bar .set (progress )
        except Exception :
            pass 

    def build_filters_payload (self ):
        payload ={}
        for name ,var in self .filters_checkboxes .items ():
            if var .get ():
                payload [name ]=True 
        return payload 

    def apply_filters_selected (self ):
        sel =self .tree .selection ()
        if not sel :
            messagebox .showinfo ('Info','Selecione arquivos')
            return 
        filters =self .build_filters_payload ()
        if not filters :
            messagebox .showwarning ('Aviso','Selecione um filtro')
            return 

        for iid in sel :
            fpath =iid 
            try :
                self .executor .submit (self ._apply_filters_wrapper ,fpath ,filters )
            except Exception as e :
                self .log_message (f'❌ Erro ao agendar filtro: {e }')

    def _apply_filters_single (self ,fpath ,filters ):
        try :
            with open (fpath ,'r',encoding ='utf-8',errors ='ignore')as fh :
                content =fh .read ()
            data ={'cookies_text':content ,'filters':filters }
            resp =requests .post (f"{API_BASE }/api/filter",json =data ,timeout =15 )
            if resp .status_code ==200 :
                res =resp .json ()
                cnt =res .get ('filtered_count',0 )
                self .after (0 ,lambda :self ._update_tree_item (fpath ,f'🔽 Filtrado ({cnt })',str (cnt )))
                self .log_message (f'{os .path .basename (fpath )} → filtrado ({cnt })')
            else :
                self .log_message (f'❌ Erro ao filtrar: {resp .status_code }')
        except Exception as e :
            self .log_message (f'❌ Erro filtro: {str (e )[:40 ]}')

    def analyze_selected (self ):
        sel =self .tree .selection ()
        if not sel :
            messagebox .showinfo ('Info','Selecione arquivos')
            return 
        for iid in sel :
            fpath =iid 
            try :
                self .executor .submit (self ._analyze_wrapper ,fpath )
            except Exception as e :
                self .log_message (f'❌ Erro ao agendar análise: {e }')

    def _analyze_single (self ,fpath ):
        try :
            with open (fpath ,'r',encoding ='utf-8',errors ='ignore')as fh :
                content =fh .read ()
            data ={'cookies_text':content }
            resp =requests .post (f"{API_BASE }/api/analyze",json =data ,timeout =20 )
            if resp .status_code ==200 :
                res =resp .json ()
                total =res .get ('total_cookies',0 )
                sec =res .get ('security_analysis',{})
                msg =f"📊 Análise: {os .path .basename (fpath )}\n\n"
                msg +=f"Total de Cookies: {total }\n\n"
                msg +="Segurança:\n"
                msg +=json .dumps (sec ,indent =2 ,ensure_ascii =False )

                win =ctk .CTkToplevel (self )
                win .title (f'Análise - {os .path .basename (fpath )}')
                win .geometry ('650x550')

                textbox =ctk .CTkTextbox (win ,wrap ="word",fg_color ="#2a2a2a",text_color ="#e0e0e0")
                textbox .pack (fill ="both",expand =True ,padx =15 ,pady =15 )
                textbox .insert ("0.0",msg )
                textbox .configure (state ="disabled")

                self .log_message (f'📊 Analisado {os .path .basename (fpath )}: {total } cookies')
            else :
                self .log_message (f'❌ Erro análise: {resp .status_code }')
        except Exception as e :
            self .log_message (f'❌ Erro: {str (e )[:40 ]}')

    def on_file_double_click (self ,event ):
        selection =self .tree .selection ()
        if selection :
            fpath =selection [0 ]
            FilePreviewWindow (self ,fpath )

    def export_results (self ):
        results =[]
        for item in self .tree .get_children ():
            try :
                values =self .tree .item (item )['values']
                if values and len (values )>=3 :
                    results .append ({
                    'file':os .path .basename (item ),
                    'status':values [0 ],
                    'cookies':values [1 ],
                    'path':values [2 ]
                    })
            except tk .TclError :
                pass 

        if not results :
            messagebox .showinfo ("Info","Nenhum resultado para exportar")
            return 

        ExportDialog (self ,results )

    def show_help (self ):
        help_text =(
        "🍪 COCKIE MONSTER PRO - GUIA\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📁 SELECIONAR PASTA\n"
        "Escolha a pasta contendo arquivos .txt com cookies\n\n"
        "🔍 SCAN RECURSIVO\n"
        "Processa todos os arquivos recursivamente e valida cookies\n\n"
        "⚙️ FILTROS\n"
        "Selecione critérios e aplique filtros aos arquivos\n\n"
        "📊 ANALISAR\n"
        "Análise detalhada de segurança dos cookies selecionados\n\n"
        "💾 EXPORTAR\n"
        "Salva resultados em JSON, CSV ou TXT\n\n"
        "📈 ESTATÍSTICAS\n"
        "Monitore o progresso em tempo real"
        )

        win =ctk .CTkToplevel (self )
        win .title ('Ajuda - Cockie Monster Pro')
        win .geometry ('600x500')
        win .configure (fg_color ="#1f1f1f")

        textbox =ctk .CTkTextbox (win ,wrap ="word",fg_color ="#2a2a2a",text_color ="#e0e0e0")
        textbox .pack (fill ="both",expand =True ,padx =15 ,pady =15 )
        textbox .insert ("0.0",help_text )
        textbox .configure (state ="disabled")
