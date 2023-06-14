import time
import pyautogui
import tqdm
import pandas as pd
import datetime

# last

def move_to_position(last,start,end,value,rangeOf,negative=False):
    pyautogui.moveTo(x=last[0], y=last[1])
    new_position=(((end[0]-start[0])/rangeOf)*(value)+start[0],end[1])
    if negative:
        new_position=(((end[0]-start[0])/rangeOf)*(value+90)+start[0],end[1])
    pyautogui.dragTo(x=new_position[0], y=new_position[1])
    return new_position[0]


if __name__=="__main__":
    wait_time=10
    samples=pd.read_csv('samples.csv',header=None)
    ##
    lastposition_Snelheid = (140,430)
    Snelheid_start_position = (140, 430)
    Snelheid_end_position = (1610, 430)
    Snelheid_range=10
    ###
    lastposition_module0_omvang = (350,620)
    Module0_Omvang_start_position = (350,620)
    Module0_Omvang_end_position =(550,620)
    Module0_Omvang_range=90
    ###
    lastposition_module0_Positie = (350,750)
    Module0_Positie_start_position = (350,750)
    Module0_Positie_end_position =(550,750)
    Module0_Positie_range=180
    ### 
    lastposition_module1_omvang = (1195,650)
    Module1_Omvang_start_position =(1195,650)
    Module1_Omvang_end_position =(1390,650)
    Module1_Omvang_range=90
    ###
    lastposition_module1_Positie =(1197,763)
    Module1_Positie_start_position =(1197,763)
    Module1_Positie_end_position =(1390,763)
    Module1_Positie_range=180
    ###
    lastposition_relatie=(760,900)
    Relatie_start_position=(760,900)
    Relatie_end_position=(950,900)
    Relatie_range=180
    DF=pd.DataFrame(columns=['Timestamp','Snelheid','Omvang1','Positie1','Omvang2','Positie2','Relatie'])
    time.sleep(5)
    for index,row in samples.iloc[:500].iterrows():
        print(index)
        time.sleep(wait_time)
        # Snelheid
        l=move_to_position(lastposition_Snelheid,Snelheid_start_position,Snelheid_end_position,row[0],Snelheid_range)
        lastposition_Snelheid = (l,430)
        #Module0_Omvang
        l=move_to_position(lastposition_module0_omvang,Module0_Omvang_start_position,Module0_Omvang_end_position,row[1],Module0_Omvang_range)
        lastposition_module0_omvang = (l,630)
        #Module0_Positie
        l=move_to_position(lastposition_module0_Positie,Module0_Positie_start_position,Module0_Positie_end_position,row[2],Module0_Positie_range,negative=True)
        lastposition_module0_Positie = (l,763)
        #Module1_Omvang
        l=move_to_position(lastposition_module1_omvang,Module1_Omvang_start_position,Module1_Omvang_end_position,row[3],Module1_Omvang_range)
        lastposition_module1_omvang = (l,630)
        #Module1_Positie
        l=move_to_position(lastposition_module1_Positie,Module1_Positie_start_position,Module1_Positie_end_position,row[4],Module1_Positie_range,negative=True)
        lastposition_module1_Positie = (l,763)
        #Relatie
        l=move_to_position(lastposition_relatie,Relatie_start_position,Relatie_end_position,row[5],Relatie_range,negative=True)
        lastposition_relatie = (l,900)
        DF=pd.concat([DF, pd.DataFrame([{'Timestamp':datetime.datetime.now().time(),'Snelheid':row[0],'Omvang1':row[1],'Positie1':row[2],
                      'Omvang2':row[3],'Positie2':row[4],'Relatie':row[5]}])], ignore_index=True)
        # print(row)
        # print(datetime.datetime.now().time())
    # print(DF.head())
    DF.to_csv('NewParameterSamples.csv',index=False)