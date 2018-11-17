from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.clock import Clock, mainthread
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color
from kivy.core.window import Window
import datetime
import threading
import time
import serial
import re
import string
import io
import configparser
#import RPi.GPIO as GPIO
import csv


Window.size = (800, 480)
#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(5, GPIO.IN)


class RootWidget(BoxLayout):
    pass

    StopUhr = threading.Event()
    StopOBD = threading.Event()


    def init_app_thread(self, button, gui, app):
        threading.Thread(target=app.uhr_thread, args=()).start()
        app.read_ini_file()

    def start_OBD_thread(self, button, gui, app):
        if app.root.ids.ConectButton.state == 'down':
            threading.Thread(target=app.OBD_thread, args=()).start()
        else:
            app.root.StopOBD.set()



class ConsumptionMonitorApp(App):
    pass

    
    ObdErrorStatus=0
    LadenActiv = bool(0)
    LadenGestartet = bool(0)
    LadenGestoppt = bool(0)
    NumToasts=0
    CumulativeChargedEnergyStart=0
    KiloWatt=0.0
    Preis=0.0
    
    LogDate="01.01.1970"
    LogTime="00:00:00"
    LogCumulativeChargeEnergyStart="0.0"
    LogCumulativeChargedEnergyEnd="0.0"
    LogAuxBat="0.0"    
    LogOdoMeterValue="0"
    LogChargeStart="00:00:00"
    LogChargeEnd="00:00:00"
    LogReceivedEnergy="0.0"
    LogPreisBasis="Home"
    LogPreis="0.2546"
    LogChargeTyp="Vollladung"
    
    LogChargedEnergy="0.0"    
    LogChargeDuration="0"
    LogKosten="0.0"
    
    LogTOC="typ2_ccs_not_connected"
    LogCharging="blitz_rot"    
    LogSOC="0"    
    
    StopCounter = threading.Event()
    
    PowerCounterStart=0
    SoCDisp=""
    


    config=configparser.ConfigParser()
#    Dongel=serial.Serial("/dev/rfcomm0", timeout=None)
#    Dongel.baudrate = 57600
    
    
    def uhr_thread(self):
        while True:
            if self.root.StopUhr.is_set():
                # Stop running this thread so the main Python process can exit.
                return
            self.SetzeDatumUndZeit()
            time.sleep(1)

    def OBD_thread(self):
        self.set_gui_text("AuxBat",0.0)
        self.set_gui_text("ChargedEnergy",0.0)
        self.set_gui_text("ChargeTime",0)
        self.set_gui_text("SoC",0.0)
        self.set_gui_text("PowerCounter",0.0)
        
        Dongel=serial.Serial("/dev/rfcomm0", timeout=None)
        Dongel.baudrate = 57600
        Dongel.flushInput()
        time.sleep(1)
        self.set_icons("ConnectState",1)
        InitListe = [["Z", "Dongel zurueckgesetzt"], ["BRD 45", "Baudrate auf 57600 bps gesetzt"],
                     ["L0", "Linefeed ausgeschaltet"], ["E0", "Echo ausgeschaltet"], ["S0", "Leerzeichen abgeschaltet"],
                     ["h0", "header ausgeschaltet"], ["CAF1", "Autoformat eingeschaltet"],
                     ["CFC1", "CANFLOW eingeschaltet"], ["CM7FF", "Maske gesetzt"],
                     ["AR", "Autoresponse eingeschaltet"], ["CF7EC", "Filter auf 7EC gesetzt"]]
        for Befehl, Ausgabe in InitListe:
            obddate_init="Nochmal"
            Kommando='AT'+ Befehl +'\r\n'
            while obddate_init=="Nochmal":
                obddate_init=self.init_Dongel(Kommando,Ausgabe,Dongel)
                if Befehl=="Z" and obddate_init=="Unknown command":
                    obddate_init="Nochmal"
                    time.sleep(1)
            time.sleep(1)
            self.SetToast(Ausgabe)
        self.ObdErrorStatus=0
        self.LadenActiv=bool(0)
        self.LadenGestartet = bool(0)
        self.LadenGestoppt = bool(0)
        self.root.StopOBD.clear()
        self.set_icons("ConnectState",2)
        if self.ObdErrorStatus==0:
            while True:
                if self.root.StopOBD.is_set() or self.LadenGestoppt==bool(1):
                    # Stop running this thread so the main Python process can exit.
                    break
                # Befehl 2105 absetzen
                obddata=self.get_bms_data("2105","PID 2105 abfragen",Dongel)
                if obddata != "Unknown command" and obddata != "Fehler":
                    SoCDisp=self.get_pid_data(obddata,"SoCDisp")
                    if SoCDisp>=0:
                        if SoCDisp > 0 and SoCDisp <= 100:
                            self.set_gui_text("SoC",SoCDisp)
                            self.LogSOC=str(SoCDisp)                            
                        else:
                            self.SetToast("SoCDisp ist ausserhalb des erlaubten Bereichs")
                    else:
                        self.SetToast("Keinen Relevanten Daten-Abschnitt für SoC gefunden")
                else:
                    self.SetToast("2105 ist ein unbekannter Befehl") 
                # Befehl 2101 absetzen
                obddata=self.get_bms_data("2101","PID 2101 Abfragen",Dongel)
                if obddata != "Unknown command" and obddata != "Fehler":
                    StatusField=int(self.get_pid_data(obddata,"StatusField"))
                    if StatusField>=0:
                        LadenMaske = 128
                        CCSMaske = 64
                        Typ2Maske = 32
                        Laden = 0
                        CCS = 0
                        Typ2 = 0
                        Verbunden=0
                        Laden = StatusField & LadenMaske
                        CCS = StatusField & CCSMaske
                        Typ2 = StatusField & Typ2Maske
                        if CCS > 0:
                            Verbunden=2
                        if Typ2 > 0:
                            Verbunden=1
                        self.set_icons("ConnectType",Verbunden)
                        if Laden > 0:
                            if self.LadenActiv == bool(0):
                                self.LadenActiv = bool(1)
                                self.LadenGestartet = bool(1)
                                self.set_icons("ChargeState",int(self.LadenActiv))
                                self.SetToast("Ladevorgang wurde gestartet.")
                        else:
                            if self.LadenActiv == bool(1):
                                self.LadenActiv = bool(0)
                                self.LadenGestoppt = bool(1)
                                self.root.StopOBD.set()
                                self.SetToast("Ladevorgang wurde beendet.")
                                self.set_icons("ChargeState",int(self.LadenActiv))
                    else:
                        self.SetToast("Keinen Relevanten Daten-Abschnitt für Statusfeld gefunden")
                    BattVolt=self.get_pid_data(obddata,"AuxBat")
                    if BattVolt>=0:
                        self.set_gui_text("AuxBat",BattVolt)
                    else:
                        self.SetToast("Keinen Relevanten Daten-Abschnitt für Hilfsbatterie gefunden")
                    CumulativeChargedEnergy=self.get_pid_data(obddata,"ChargedEnergy")
                    if CumulativeChargedEnergy>=0:
                        if (self.LadenGestartet == bool(1)):
                            self.CumulativeChargedEnergyStart = CumulativeChargedEnergy
                            self.PowerCounterStart=datetime.datetime.now()
                            self.start_counter_thread()
                            self.LadenGestartet = bool(0)
                            self.LogCumulativeChargeEnergyStart=str(CumulativeChargedEnergy)
                            self.LogChargeStart=self.PowerCounterStart.strftime("%H:%M:%S")
                            self.LogDate=datetime.datetime.now().strftime("%d.%m.%Y")
                            self.LogTime=datetime.datetime.now().strftime("%H:%M:%S")                            
                            fobj_out = open("/media/pi/INTENSO/StatData.txt","w")
                            fobj_out.write(self.LogDate)
                            fobj_out.write(self.LogTime)
                            fobj_out.write(self.LogCumulativeChargeEnergyStart)
                            fobj_out.close()                            
                        CumulativeChargedEnergAkt = CumulativeChargedEnergy
                        PowerCounterAkt=datetime.datetime.now()
                        ChargedEnergy = round(CumulativeChargedEnergAkt - self.CumulativeChargedEnergyStart,2)
                        self.set_gui_text("ChargedEnergy",ChargedEnergy)
                        TimeDifftmp=PowerCounterAkt-self.PowerCounterStart
                        if TimeDifftmp.seconds % 60 > 0:
                            TimeDiff=((TimeDifftmp.seconds)//60)+1
                        else:
                            TimeDiff=((TimeDifftmp.seconds)//60) 
                        self.set_gui_text("ChargeTime",TimeDiff)
                        if (self.LadenGestoppt == bool(1)):
                            self.LadenGestoppt = bool(0)
                            self.root.StopOBD.set()
                            self.LogCumulativeChargedEnergyEnd=str(CumulativeChargedEnergAkt)
                            self.LogChargedEnergy=str(ChargedEnergy)
                            self.LogChargeEnd=PowerCounterAkt.strftime("%H:%M:%S")
                            self.LogChargeDuration=str(TimeDiff)
                            self.LogChargeTyp=self.root.ids.LadungsTyp.text
                            self.LogPreis=self.root.ids.Preis.text
                            self.LogPreisBasis=self.root.ids.PreisBasis.text
                            self.LogOdoMeterValue=self.root.ids.km_Tacho.text
                            self.LogReceivedEnergy=self.root.ids.PowerCounter.text
                            self.LogAuxBat=self.root.ids.VoltBatAux.text
                            if self.LogPreisBasis == "Flat":
                                KostenRaw=self.Preis
                            elif self.LogPreisBasis == "Min":
                                KostenRaw=TimeDiff*self.Preis
                            else:
                                if self.LogReceivedEnergy=="0.0":
                                    KostenRaw=self.KiloWatt*self.Preis
                                else:
                                    KostenRaw=ChargedEnergy*self.Preis
                            
                            self.LogKosten=str(KostenRaw)                    
                            self.StopCounter.set()
                    else:
                        self.SetToast("Keinen Relevanten Daten-Abschnitt für die Energie gefunden")
                else:
                    self.SetToast("2101 ist ein unbekannter Befehl")
                fobj_out = open("/dev/shm/AktChargeState.txt","w")
                fobj_out.write(datetime.datetime.now().strftime("%d.%m.%Y -- %H:%M:%S")+"\r\n")
                fobj_out.write(self.LogTOC+"\r\n")
                fobj_out.write(self.LogCharging+"\r\n")
                fobj_out.write(self.LogSOC+"\r\n")
                fobj_out.close()                 
                time.sleep(1)
            Kommando='AT LP\r\n'
            obddataclose=self.init_Dongel(Kommando,"Dongel abschalten",Dongel)
            time.sleep(2)
            self.set_icons("ConnectState",0)
            self.set_icons("ConnectType",0)
            self.set_icons("ChargeState",0)
            self.UnLockConnectButton()
            self.SetToast("Ladungs-Überwachung beendet")
            self.SendToDB()
        return

        

    def get_pid_data(self,commanddata,pid):
        if pid=="AuxBat":
            blockstart=4
            blockende=5
            pidstart=10
            pidend=12
            compumethod = 10.0
        elif pid=="ChargedEnergy":
            blockstart=5
            blockende=7
            pidstart=-18
            pidend=-10
            compumethod = 10
        if pid=="StatusField":
            blockstart=1
            blockende=2
            pidstart=12
            pidend=14
            compumethod = 1  
        if pid == "SoCDisp":
            blockstart=4
            blockende=5
            pidstart=14
            pidend=16
            compumethod = 2           
        matched_string_groups = re.search(str(blockstart)+':([^;]*)'+str(blockende)+':', commanddata)
        if matched_string_groups:
            first_matched_group_string = str(matched_string_groups.group(0))
            if blockende-blockstart>1:
                blockmitte=blockstart+1
                first_matched_group_string = first_matched_group_string.replace(str(blockmitte)+':', '')
            pid_string = (first_matched_group_string[pidstart:pidend])
            pid_data=(int(pid_string, 16) / compumethod)
        else:
            pid_data=-1
        return pid_data
                       

    def init_Dongel(self,command,AusgabeText,OBD_Dongel):
        self.SetToast(AusgabeText)
        local_data="Unknown command"        
        ByteBefehl=bytes(command, 'utf-8')
        OBD_Dongel.write(ByteBefehl)
        OBD_Dongel.flush()
        seq = []
        joineddata=''
        while True:
            reading = OBD_Dongel.read()
            seq.append(reading)
            joineddata = ' '.join(str(v) for v in seq).replace(' ', '')
            err = re.search('ERROR', joineddata)
            if err:
                self.SetToast("Befehl " + command + "ist Fehlgeschlagen")
                local_data="Fehler"
                break
            Unbekannt = re.search('\?', joineddata)
            if Unbekannt:
                self.SetToast("Befehl " + command + "ist Unbekannt") 
                local_data="Unknown command"
                break 
            m = re.search('>', joineddata)
            if m:
                tmpdata0=bytes('-',"utf-8").join(seq)
                tmpdata1=tmpdata0.decode("utf-8")
                tmpdata2=tmpdata1.replace(' ', '')
                tmpdata3=tmpdata2.replace('-', '')
                local_data=tmpdata3.replace('\r', '')
                self.SetToast("Befehl " + command + " ist Abgearbeitet")
                break       
        return local_data

    def get_bms_data(self,command,AusgabeText,OBD_Dongel):
        self.SetToast(AusgabeText)        
        local_data="Unknown command"
        if command=="2105":
            OBD_Dongel.write(b'2105\r\n')
        else:
            OBD_Dongel.write(b'2101\r\n')
        OBD_Dongel.flush()
        seq = []
        joineddata=''
        while True:
            reading = OBD_Dongel.read()
            seq.append(reading)
            joineddata = ' '.join(str(v) for v in seq).replace(' ', '')
            err = re.search('ERROR', joineddata)
            if err:
                self.SetToast("Befehl " + command + "ist Fehlgeschlagen")
                local_data="Fehler"
                break
            Unbekannt = re.search('\?', joineddata)
            if Unbekannt:
                self.SetToast("Befehl " + command + "ist Unbekannt") 
                local_data="Unknown command"
                break 
            m = re.search('>', joineddata)            
            if m:
                tmpdata0=bytes('-',"utf-8").join(seq)
                tmpdata1=tmpdata0.decode("utf-8")
                tmpdata2=tmpdata1.replace(' ', '')
                tmpdata3=tmpdata2.replace('-', '')
                local_data=tmpdata3.replace('\r', '')
                self.SetToast("Befehl " + command + " ist Abgearbeitet")
                break       
        return local_data

    def SendToDB(self):
        #fields=[AblageDatum,AblageUhrzeit,LadungsTyp,Preisbasis,Preis,Tachostand,PowerCounterStart,PowerCounterEnd,AkkuStartWert,AkkuEndWert,BezogeneMenge,AkkuSpannung]
        fields=[self.LogDate,self.LogTime,self.LogChargeTyp,self.LogPreisBasis,self.LogPreis,self.LogOdoMeterValue,self.LogChargeStart,self.LogChargeEnd,self.LogCumulativeChargeEnergyStart,self.LogCumulativeChargedEnergyEnd,self.LogReceivedEnergy,self.LogAuxBat,self.LogChargeDuration,self.LogChargedEnergy,self.LogKosten]
        with open(r'/media/pi/INTENSO/IoniqDB.csv', 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter =";")
            writer.writerow(fields)

    def start_counter_thread(self):
        threading.Thread(target=self.counter_thread, args=()).start()


    def counter_thread(self):
        WattCount=0
        RisingEdge=0
        self.KiloWatt=0.0
        while True:
            if self.StopCounter.is_set() or self.LadenGestoppt==bool(1):
                # Stop running this thread so the main Python process can exit.
                break
            #if GPIO.input(5) == GPIO.HIGH and RisingEdge == 0:
                #WattCount=WattCount+1
                #RisingEdge=1
                #self.KiloWatt=WattCount/1000
                #self.set_gui_text("PowerCounter",self.KiloWatt)
                #time.sleep(0.1)
            #if GPIO.input(5) == GPIO.LOW:
                #RisingEdge=0
                #time.sleep(0.1)
        return


    @mainthread
    def UnLockConnectButton(self):
        self.root.ids.ConectButton.state="normal"

    @mainthread
    def SetToast(self,Text):
        self.root.ids.Toast.text=Text
        self.NumToasts=self.NumToasts+1
        Clock.schedule_once(self.ClrToast, 1)

    @mainthread
    def ClrToast(self,dt):
        if self.NumToasts==1:
            self.root.ids.Toast.text =""
        self.NumToasts=self.NumToasts-1


    @mainthread
    def set_icons(self,typ,status):
        if typ=="ConnectState":
            if status==2:
                self.root.ids.ComunicationTo.icon = "auto_gruen.png"
            if status==1:
                self.root.ids.ComunicationTo.icon = "dongel_gruen.png"
            elif status==0:
                self.root.ids.ComunicationTo.icon = "dongel_rot.png"
        if typ=="ConnectType":
            if status==2:
                self.root.ids.ConectorType.icon = "typ2_ccs_ccs_connected.png"
                self.LogTOC="typ2_ccs_ccs_connected"
            elif status==1:
                self.root.ids.ConectorType.icon = "typ2_ccs_typ2_connected.png"
                self.LogTOC="typ2_ccs_typ2_connected"
            else:
                self.root.ids.ConectorType.icon = "typ2_ccs_not_connected.png"
                self.LogTOC="typ2_ccs_not_connected"
        if typ=="ChargeState":
            if status == 1:
                self.root.ids.ChargingState.icon = "blitz_gruen.png"
                self.LogCharging="blitz_gruen"
            else:
                self.root.ids.ChargingState.icon = "blitz_rot.png"
                self.LogCharging="blitz_rot"

    @mainthread
    def read_ini_file(self):
        self.config.read('consumptionmonitor.ini')
        homepreis=self.config['DEFAULT']['preis']
        self.root.ids.Preis.text=homepreis
        self.Preis=float(homepreis)


    @mainthread
    def SetzeDatumUndZeit(self):
        self.root.ids.DatumLabel.text = datetime.datetime.now().strftime("%d.%m.%Y -- %H:%M:%S")

    @mainthread
    def set_gui_text(self,typ,Wert):
        #print(typ+": "+str(Wert))
        if typ=="SoC":
            self.root.ids.SoC_Value.text=str(Wert)
            self.root.ids.SoC_Bar.value=Wert
        elif typ=="AuxBat": 
            self.root.ids.VoltBatAux.text=str(Wert)
        elif typ=="ChargedEnergy":
            self.root.ids.PowerCar.text=str(Wert)
        elif typ=="PowerCounter":
            self.root.ids.PowerCounter.text=str(Wert)
        elif typ=="ChargeTime":
            self.root.ids.ChargeTime.text=str(Wert)
     
 
    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.StopUhr.set()
        self.root.StopOBD.set()
        self.StopCounter.set()
        if self.root.ids.PreisBasis.text=="Home":
            self.config = configparser.ConfigParser()
            self.config['DEFAULT'] = {'preis': self.root.ids.Preis.text}
            with open('consumptionmonitor.ini', 'w') as configfile:
                self.config.write(configfile)

    def OpenKeyBoard(self, button, gui, app):
        global Knopf
        Knopf = button
        Factory.KeyBordPopup().open()

    def SetzeEingabewert(self, EingabeWert):
        Knopf.text = EingabeWert
        if Knopf == self.root.ids.Preis:
            self.Preis = float(EingabeWert)


    def DelZeichen(self, button, gui, app):
        tmptxt = gui.ids.EingabeListe.text[0:-1]
        gui.ids.EingabeListe.text = tmptxt

    def build(self):
        return RootWidget()


if __name__ == '__main__':
    ConsumptionMonitorApp().run()
