import time
import pyautogui
import tqdm
Snelheid_start_position = (125, 420)
Snelheid_end_position = (1623, 420)
Module0_Omvang_start_position = (366, 622)
Module0_Omvang_end_position = (560, 620)
Module0_Positie_start_position = (327, 730)
Module0_Positie_end_position = (567, 721)

Module1_Omvang_start_position = (1185, 600)
Module1_Omvang_end_position = (1410, 620)
Module1_Positie_start_position = (1172, 730)
Module1_Positie_end_position = (1408, 733)

Relatie_start_position = (765, 853)
Relatie_end_position= (942, 850)
change_mag = 30
Delay_time = 3


if __name__=="__main__":
    time.sleep(1)

    pyautogui.moveTo(x=868, y=Module0_Positie_start_position[1])
    pyautogui.dragTo(x=Module0_Positie_start_position[0], y=Module0_Positie_end_position[1]) 

    slider2=0
    # Horizontal Sliders
    for position1 in tqdm.tqdm(range(Snelheid_start_position[0],Snelheid_end_position[0],change_mag*5)):
        pyautogui.moveTo(x=position1, y=Snelheid_start_position[1])
        pyautogui.dragTo(x=position1+(change_mag*5), y=Snelheid_start_position[1], duration=0.5)
        time.sleep(Delay_time)
        for position2 in range(Module0_Omvang_start_position[0],Module0_Omvang_end_position[0],change_mag):
            pyautogui.moveTo(x=position2, y=Module0_Omvang_start_position[1])
            pyautogui.dragTo(x=position2+change_mag, y=Module0_Omvang_start_position[1], duration=0.5)
            time.sleep(Delay_time)
            for position3 in range(Module0_Positie_start_position[0],Module0_Positie_end_position[0],change_mag):
                pyautogui.moveTo(x=position3, y=Module0_Positie_start_position[1])
                pyautogui.dragTo(x=position3+change_mag, y=Module0_Positie_start_position[1], duration=0.5)
                time.sleep(Delay_time)
                for position4 in range(Module1_Omvang_start_position[0],Module1_Omvang_end_position[0],change_mag):
                    pyautogui.moveTo(x=position4, y=Module1_Omvang_start_position[1])
                    pyautogui.dragTo(x=position4+change_mag, y=Module1_Omvang_start_position[1], duration=0.5)
                    time.sleep(Delay_time)
                    for position5 in range(Module1_Positie_start_position[0],Module1_Positie_end_position[0],change_mag):
                        pyautogui.moveTo(x=position5, y=Module1_Positie_start_position[1])
                        pyautogui.dragTo(x=position5+change_mag, y=Module1_Positie_start_position[1], duration=0.5)
                        time.sleep(Delay_time)
                        for position6 in range(Relatie_start_position[0],Relatie_end_position[0],change_mag):
                            pyautogui.moveTo(x=position6, y=Relatie_start_position[1])
                            pyautogui.dragTo(x=position6+change_mag, y=Relatie_start_position[1], duration=0.5)
                            time.sleep(Delay_time)
                        ##   
                        pyautogui.moveTo(x=position6+change_mag, y=Relatie_end_position[1])
                        pyautogui.dragTo(x=Relatie_start_position[0], y=Relatie_start_position[1])
                    pyautogui.moveTo(x=position5+change_mag, y=Module1_Positie_start_position[1])
                    pyautogui.dragTo(x=Module1_Positie_start_position[0], y=Module1_Positie_start_position[1])
                pyautogui.moveTo(x=position4+change_mag, y=Module1_Omvang_start_position[1])
                pyautogui.dragTo(x=Module1_Omvang_start_position[0], y=Module1_Omvang_start_position[1])
            pyautogui.moveTo(x=position3+change_mag, y=Module0_Positie_start_position[1])
            pyautogui.dragTo(x=Module0_Positie_start_position[0], y=Module0_Positie_start_position[1])
        pyautogui.moveTo(x=position2+change_mag, y=Module0_Omvang_start_position[1])
        pyautogui.dragTo(x=Module0_Omvang_start_position[0], y=Module0_Omvang_start_position[1])
        silder2=0
        time.sleep(1)   