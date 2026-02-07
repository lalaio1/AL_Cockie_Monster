import os 
import json 
import tkinter as tk 
from tkinter import filedialog ,messagebox 
import customtkinter as ctk 


class FilePreviewWindow (ctk .CTkToplevel ):
    def __init__ (self ,parent ,filepath ):
        super ().__init__ (parent )
        self .title (f"Preview - {os .path .basename (filepath )}")
        self .geometry ("600x400")

        try :
            with open (filepath ,'r',encoding ='utf-8',errors ='replace')as f :
                content =f .read (2000 )
        except Exception as e :
            content =f"Erro ao ler arquivo: {str (e )}"

        textbox =ctk .CTkTextbox (self ,wrap ="none")
        textbox .pack (fill ="both",expand =True ,padx =10 ,pady =10 )
        textbox .insert ("0.0",content )
        textbox .configure (state ="disabled")


class ExportDialog (ctk .CTkToplevel ):
    def __init__ (self ,parent ,results_data ):
        super ().__init__ (parent )
        self .title ("Exportar Resultados")
        self .geometry ("400x200")
        self .results_data =results_data 

        frame =ctk .CTkFrame (self )
        frame .pack (fill ="both",expand =True ,padx =20 ,pady =20 )

        ctk .CTkLabel (frame ,text ="Formato de Exportação:").pack (pady =10 )

        format_var =tk .StringVar (value ="json")
        ctk .CTkRadioButton (frame ,text ="JSON",variable =format_var ,value ="json").pack (anchor ='w',padx =20 )
        ctk .CTkRadioButton (frame ,text ="CSV",variable =format_var ,value ="csv").pack (anchor ='w',padx =20 )
        ctk .CTkRadioButton (frame ,text ="TXT",variable =format_var ,value ="txt").pack (anchor ='w',padx =20 )

        button_frame =ctk .CTkFrame (frame ,fg_color ="transparent")
        button_frame .pack (pady =20 )

        ctk .CTkButton (button_frame ,text ="Exportar",
        command =lambda :self .export (format_var .get ())).pack (side ="left",padx =5 )
        ctk .CTkButton (button_frame ,text ="Cancelar",
        command =self .destroy ).pack (side ="left",padx =5 )

    def export (self ,format_type ):
        filepath =filedialog .asksaveasfilename (
        defaultextension =f".{format_type }",
        filetypes =[(f"{format_type .upper ()} files",f"*.{format_type }")]
        )
        if not filepath :
            return 

        try :
            if format_type =="json":
                with open (filepath ,'w',encoding ='utf-8')as f :
                    json .dump (self .results_data ,f ,indent =2 ,ensure_ascii =False )
            elif format_type =="csv":
                import csv 
                with open (filepath ,'w',newline ='',encoding ='utf-8')as f :
                    writer =csv .writer (f )
                    writer .writerow (["Arquivo","Status","Cookies"])
                    for item in self .results_data :
                        writer .writerow ([item ['file'],item ['status'],item ['cookies']])
            elif format_type =="txt":
                with open (filepath ,'w',encoding ='utf-8')as f :
                    for item in self .results_data :
                        f .write (f"{item ['file']} - {item ['status']} ({item ['cookies']})\n")

            messagebox .showinfo ("Sucesso",f"Resultados exportados para {filepath }")
            self .destroy ()
        except Exception as e :
            messagebox .showerror ("Erro",f"Erro ao exportar: {str (e )}")
