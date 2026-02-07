import sys 
import os 


sys .path .insert (0 ,os .path .dirname (__file__ ))

from main_window import CockieMonsterGUI 


if __name__ =='__main__':
    app =CockieMonsterGUI ()
    app .mainloop ()
