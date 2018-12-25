#!/usr/bin/python3
# coding: utf8
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

# Setze die Fenster-Größe der GUI auf 800x400
Window.size = (800, 480)
# Verwende die Nummerierung auf dem Board als Bais
#GPIO.setmode(GPIO.BOARD)
# Konfiguriere den GPIO-Pinn 5 als Input
#GPIO.setup(5, GPIO.IN)

# Erstellen des Root-Widget wegen Threading und Uhr
# BoxLayout --> Typ des Basis-Elements auf dem das Root-Widget bassiert
class RootWidget(BoxLayout):
    pass

    # Tread-Element für Uhr anlegen
    StopUhr = threading.Event()
    # Thread-Element für OBD-Aktionen Anlegen
    StopOBD = threading.Event()

    # Thread für Uhr Starten
    # Thread für OBD-Aktionen starten
    # self      --> Handel zur App
    # button    --> Handel zum Auskösenden GUI-Element
    # gui       --> Handel zur GUI
    # App       --> Handel zur App    
    def init_app_thread(self, button, gui, app):
        # Uhr-Thread-start
        threading.Thread(target=app.uhr_thread, args=()).start()
        # Ini-Werte auslesen
        app.read_ini_file()

    # Thread für OBD-Aktionen starten
    # self      --> Handel zur App
    # button    --> Handel zum Auskösenden GUI-Element
    # gui       --> Handel zur GUI
    # App       --> Handel zur App
    def start_OBD_thread(self, button, gui, app):
        if app.root.ids.ConectButton.state == 'down':
            # OBD-Thread starten
            threading.Thread(target=app.OBD_thread, args=()).start()
        else:
            # OBD-Thread stoppen
            app.root.StopOBD.set()


# Haupt-Programm
# App  --> Handel zur App
class ConsumptionMonitorApp(App):
    pass

    # Globale Variablen für die Berechnungen
    
    # Labden ist Aktiv
    LadenActiv = False
    # Das Laden wurde gerade destartet
    LadenGestartet = False
    # Das Laden wurde gerade gestoppt
    LadenGestoppt = False
    # Anzahl der Toast-Nachrichten in der Que
    NumToasts=0
    # Bisher geladene Energie-Menge beim Start der Ladung
    CumulativeChargedEnergyStart=0
    # Berogene Energie-Menge
    KiloWattStunden=0.0
    # Kosten für die bezoigene Energie-Menge
    Preis=0.0
    # Anzeige-Wert des Batterie-Ladezustands
    SoCDisp=""
    
    # Globale Variablen für das Lade-Log
    
    # Datum des Log-Eintrags, bzw. der Ladung
    LogDate="01.01.1970"
    # Uhrzeit des Log-Eintrags, bzw. Start der Ladung
    LogTime="00:00:00"
    # Bisher geladene Energie-Menge beim Start der Ladung
    LogCumulativeChargeEnergyStart="0.0"
    # Bisher geladene Energie-Menge beim Ende der Ladung
    LogCumulativeChargedEnergyEnd="0.0"
    # Spannung der Hilfsbatterie
    LogAuxBat="0.0" 
    # Tacho-Stand beim Start der Ladung
    LogOdoMeterValue="0"
    # Uhrzeit des Ladestarts
    LogChargeStart="00:00:00"
    # Uhrzeit des Ladeendes
    LogChargeEnd="00:00:00"
    # Bezogene Energie-Menge
    LogReceivedEnergy="0.0"
    # Preisbasis der aktuellen Ladung
    LogPreisBasis="Home"
    # Preis für eine Einheit der Ladung 
    LogPreis="0.2546"
    # Typ der Ladung
    LogChargeTyp="Vollladung"
    # Eingelagerte Energie-Menge
    LogChargedEnergy="0.0"
    # Ladungs-dauer
    LogChargeDuration="0"
    # Berechnete Kosten der Ladung
    LogKosten="0.0"
    # Verbindungstyp
    LogTOC="typ2_ccs_not_connected"
    # Lade-Status
    LogCharging="blitz_rot"  
    # Ladestand der Batterie
    LogSOC="0"
   
    # Globale Variablen für den Stromzähler
    
    # Thread-Element für den Strom-Zähler
    StopCounter = threading.Event()
    # Uhrzeit des Ladestarts
    PowerCounterStart=datetime.datetime.now()

    
    # Globale Variablen für den Init 

    #Auslese-Variable für den Ini-File-Parser
    config=configparser.ConfigParser()
    
    
    # Thread zur berechnung der aktuellen urzeit und die Anzeige dieser in der Menu-Leiste
    # self  --> Handel zur App    
    def uhr_thread(self):
        while True:
            if self.root.StopUhr.is_set():
                # Beenden des Threads, damit Python auch beebdet werden kann.
                return
            # Setze die Urzeit
            self.SetzeDatumUndZeit()
            # Warte bis zur nächsten Sekunde
            time.sleep(1)

    # Der OBD-Lese-Thread
    # self  --> Handel zur App
    def OBD_thread(self):
        
        # Reinitialisierung der GUI-Ausgabe auf "0"
        self.set_gui_text("AuxBat",0.0)
        self.set_gui_text("ChargedEnergy",0.0)
        self.set_gui_text("ChargeTime",0)
        self.set_gui_text("SoC",0.0)
        self.set_gui_text("PowerCounter",0.0)


        # initialisierung des Bluetooth-Interface-Handels
#        Dongel=serial.Serial("/dev/rfcomm0", timeout=None)
        # initialisierung des Bluetooth-Interface auf 57600 Baud
#        Dongel.baudrate = 57600
#        Dongel.flushInput()
        
        # eine Sekunde um die Initialisierung "Sacken" zu lassen
        time.sleep(1)
        # Dongel in der GUI als Verbunden aber nicht initialisiert anzeigen
        self.set_icons("ConnectState",1)
        # Liste mit den Dongelk-Initialisierungs-Befehlen und den zugehörigen Ausgabe-Texten
        InitListe = [["Z", "Dongel zurueckgesetzt"], ["BRD 45", "Baudrate auf 57600 bps gesetzt"],
                     ["L0", "Linefeed ausgeschaltet"], ["E0", "Echo ausgeschaltet"], ["S0", "Leerzeichen abgeschaltet"],
                     ["h0", "header ausgeschaltet"], ["CAF1", "Autoformat eingeschaltet"],
                     ["CFC1", "CANFLOW eingeschaltet"], ["CM7FF", "Maske gesetzt"],
                     ["AR", "Autoresponse eingeschaltet"], ["CF7EC", "Filter auf 7EC gesetzt"]]
        # jeder Befehl in der Liste wird an den Dongel gesended
        for Befehl, Ausgabe in InitListe:
            # Befehl zusammen setzten
            Kommando='AT'+ Befehl +'\r\n'
            # Initialisierung-Befehl an Dongel absetzen
            obddate_init=self.init_Dongel(Kommando,Ausgabe,Dongel)
            # Falls es sich um die Initialisietung mittels ATZ handelt und diese nicht erkannt wird,
            # Solange in der Schleife drehen bis sie erkannt wird
            while obddate_init=="Unknown command" and Befehl=="Z":
                time.sleep(1)
                obddate_init=self.init_Dongel(Kommando,Ausgabe,Dongel)
            # Ausgabe, dass der initbefehl abgearbeitet ist
            self.SetToast(Ausgabe)
            # Eine Sekunde warten bis der nächste Init-Befehl abgesetzt werden kann
            time.sleep(1)
        # Initialisierung der gobalen Variablen für den Lade-Zustand auf False
        self.LadenActiv=False
        self.LadenGestartet = False
        self.LadenGestoppt = False
        # Die alten thread-Stopper wieder zurücksetzen
        self.root.StopOBD.clear()
        self.StopCounter.clear()
        # Dongel in der GUI als Verbunden und initialisiert anzeigen
        self.set_icons("ConnectState",2)
        # Haupt-Schleife um die PIDs regelmäsig abzufragen
        while True:
            # Testen on die Abbruch-Bedingung, Ladung gestoppt oder App schließen getriggert wurde
            if self.root.StopOBD.is_set() or self.LadenGestoppt:
                # Aktuellen Tread beenden
                break
            # Befehl 2105 absetzen
            obddata=self.get_bms_data("2105",Dongel)
            # Test ob der PID 2105 richtig verarbeitet werden konnte.
            if obddata != "Unknown command" and obddata != "LeseFehler" and obddata != "Fehler":
                # Extrahiere den physikalischen wert des SoC aus dem Rückgabe-String
                SoCDisp=self.get_pid_data(obddata,"SoCDisp")
                # Test ob der Physikalische Wert für den SoC extrahiert werden konnte
                if SoCDisp>=0:
                    # test ob der zurückgegebene physikalische wert des SoC inner halb des erlaubten bereichs liegt
                    if SoCDisp > 0 and SoCDisp <= 100:
                        # Setze den SoC als Text
                        self.set_gui_text("SoC",SoCDisp)
                        # Schreibe den SoC in die globale Variable für den SoC
                        self.LogSOC=str(SoCDisp)
                    # Der Physikalische wert des zurückgegebenen SoC ist auserhalb des gültigen Werte-Bereichs
                    else:
                        # textausgabe wenn der SoC nicht im richtigen bereich ist
                        self.SetToast("SoCDisp ist ausserhalb des erlaubten Bereichs")
                # Der SoC konnte nicht im Rückgabe-String gefunden werden
                else:
                    # Textausgabe wenn der SoC nicht gefunden wurde
                    self.SetToast("Keinen Relevanten Daten-Abschnitt für SoC gefunden")
            # der PID 2105 führte zu Problemen bei der Verarbeitung im Fahrzeug
            else:
                # Text ausgabe bei fehlerhafter PID-Verarabeitung
                self.SetToast("PID 2105 konnte nicht verarbeitet werden") 
            # Befehl 2101 absetzen
            obddata=self.get_bms_data("2101",Dongel)
            # Test ob der PID 2101 richtig verarbeitet werden konnte.
            if obddata != "Unknown command" and obddata != "LeseFehler" and obddata != "Fehler":
                # Extrahiere den Staus-Werte aus dem Rückgabe-String
                StatusField=int(self.get_pid_data(obddata,"StatusField"))
                # Ist in dem Status-Byte ein Bit gesetzt, wird geschaut welches gesetzt ist
                if StatusField>=0:
                    # Bit für CCS-Stecker ist eingesteckt ==> Bit 6 ==> Maske ==> 64                                        
                    # Bit für Typ2-Stecker ist eingesteckt ==> Bit 5 ==> Maske ==> 32
                    # Bitmaske für beide Bits is 96
                    # Also Ver-unden mit 96 und Rechtsschift um 5 um die Verbiunden-Mit werte zu bekommen
                    # Ergebnis == 0 ==> Nichts ist verbunden
                    # Ergebnis == 1 ==> Verbunden mit Typ2
                    # Ergebnis == 2 ==> Verbunden mit CCS
                    # Setzen des entsprechenden Status-icons
                    self.set_icons("ConnectType",(StatusField & 96) >> 5)
                    # Testen ob eine Ladung Aktiv ist
                    # Bit für Laden ist aktiv ==> Bit 7 ==> Maske ==> 128                    
                    if (StatusField & 128) > 0:
                        # Falls das 7. bit gesetzt ist, Testen ob die globale Variable für das Laden auf False steht 
                        if not self.LadenActiv:
                            # Wenn bisher kein "Laden aktiv" war, dann den Merker für "Laden aktiv" setzen. 
                            self.LadenActiv = True
                            # Merker setzen, dass die Ladung gerade gestartet wurde
                            self.LadenGestartet = True
                            # Setzen des Icons für "Ladung ist aktiv"
                            self.set_icons("ChargeState",int(self.LadenActiv))
                            # Ausgabe-Text, dass eine Ladung aktiv ist
                            self.SetToast("Ladevorgang wurde gestartet.")
                    # Falls das 7. bit nicht gesetzt ist, ist keine Ladung aktiv
                    else:
                        # Testen ob bisher eine Ladung aktiv war
                        if self.LadenActiv:
                            # Setze den Merker für "Ladung Aktiv" auf False
                            self.LadenActiv = False
                            # Signalisiere, dass die Ladung gestoppt wurde
                            self.LadenGestoppt = True
                            # Beende den OBD-Thread
                            self.root.StopOBD.set()
                            # Ausgabe-Text, dass der ladevorgang beendet wurde
                            self.SetToast("Ladevorgang wurde beendet.") 
                            # Setze das Ladungs-Icon auf "Keine Ladung aktiv"                            
                            self.set_icons("ChargeState",int(self.LadenActiv))
                # Fahrzeug nicht verbunden oder das Status-Feld konnte nicht richtig extrahiert werden
                else:
                    # Ausgabetext für Status feld ist 0
                    self.SetToast("Fahrzeug nicht verbunden oder keinen Relevanten Daten-Abschnitt für Statusfeld gefunden")
                # Extrahiere den Physikalischen Wert für die Spannung der Hilfsbatterie.
                BattVolt=self.get_pid_data(obddata,"AuxBat")
                # Testen ob die spannung ausgelesen werden konnte
                if BattVolt>=0:
                    # Hilfsbatterie-Spannung ausgenen
                    self.set_gui_text("AuxBat",BattVolt)
                # Hilfs-Batterie-Spannung konnte nicht extrahiert werden
                else:
                    # Ausgabe-Text, dass die Hilfsbatterie-Spanung nicht extrahiert werden konnte
                    self.SetToast("Keinen Relevanten Daten-Abschnitt für Hilfsbatterie gefunden")
                # Extrahiere den aktuellen Stand der Cummulierten geladenen Energie-Menge im Hochvolt-Akku
                CumulativeChargedEnergy=self.get_pid_data(obddata,"ChargedEnergy")
                # Test ob der aktuellen Stand der Cummulierten geladenen Energie-Menge im Hochvolt-Akku richtig extrahiert worden ist
                if CumulativeChargedEnergy>=0:
                    # Wenn das extrahieren geklappt hat, testen ob die Ladung gerade gestartet wurde
                    if (self.LadenGestartet):
                        # aktuellen Stand der Cummulierten geladenen Energie-Menge im Hochvolt-Akku als Start-Wert festlegen
                        self.CumulativeChargedEnergyStart = CumulativeChargedEnergy
                        # Zeitpunkt des Ladestart speichern
                        self.PowerCounterStart=datetime.datetime.now()
                        # Stromzähler-Tread starten
                        self.start_counter_thread()
                        # Merker für "Laden ist gerdae gestartet" wird wieder zurückgesetzt
                        self.LadenGestartet = False
                        # aktuellen Stand der Cummulierten geladenen Energie-Menge im Hochvolt-Akku in die globale Logvariable für den Start-wert schreiben
                        self.LogCumulativeChargeEnergyStart=str(CumulativeChargedEnergy)
                        # Start-Zeitpunkt der Ladung als Uhrzeit-String in die entsprechende globale Logvariable schreiben
                        self.LogChargeStart=self.PowerCounterStart.strftime("%H:%M:%S")
                        # Aktuelles Datum als Log-Start in die entsprechende gloable Log-Variable schreiben 
                        self.LogDate=datetime.datetime.now().strftime("%d.%m.%Y")
                        # Aktuelle Uhrzeit als Log-Start in die entsprechende gloable Log-Variable schreiben 
                        self.LogTime=datetime.datetime.now().strftime("%H:%M:%S")
                        # Log-File für den Ladungsstart auf dem USB-Dongel anlegen
                        # Wird angelegt, um wenigstens die Start-Wete zu haben, falls der RaspPi einfach einfriert und nur durch Reset wieder zum leben erweckt werden kann.
                        # Hiermit lässt sich die Datenbank manuell füllen
                        fobj_out = open("/media/pi/INTENSO/StartData.txt","w")
                        # Schreibe Logadatum
                        fobj_out.write(self.LogDate+"\r\n")
                        # Schreibe Loguhrzeit
                        fobj_out.write(self.LogTime+"\r\n")
                        # Schreibe Startwert des aktuellen Stand der Cummulierten geladenen Energie-Menge im Hochvolt-Akku
                        fobj_out.write(self.LogCumulativeChargeEnergyStart)
                        # Schließe Logdatei
                        fobj_out.close()
                    # Aktuelle Uhrzeit feststellen um die Ladedauer berechnen zu können
                    PowerCounterAkt=datetime.datetime.now()
                    # Berechnen der aktuell geladenen Energiemenge
                    ChargedEnergy = round(CumulativeChargedEnergy - self.CumulativeChargedEnergyStart,2)
                    # Energiemenge an die GUI weitergeben
                    self.set_gui_text("ChargedEnergy",ChargedEnergy)
                    # Solange das Laden aktiv ist wird die Ladedauer berechnet
                    if self.LadenActiv:
                        # Aktueller zeitpunkt minus Gespeicherter Startzeitpunkt ergibzt die Ladedauer
                        TimeDifftmp=PowerCounterAkt-self.PowerCounterStart
                        # Minuten-Überlauf feststellen
                        if TimeDifftmp.seconds % 60 > 0:
                            # ist eine volle Minute Überschritten, wird die Angefangene Minute als eine Minute gezählt
                            TimeDiff=((TimeDifftmp.seconds)//60)+1
                        # Kein Minutenüberlauf
                        else:
                            # Minuten werden genau so ausgegeben wie berechnet
                            TimeDiff=((TimeDifftmp.seconds)//60) 
                        # Ladedauer wird auf der GUI ausgegeben
                        self.set_gui_text("ChargeTime",TimeDiff)
                    # Testen ob die Ladung gestoppt ist
                    if (self.LadenGestoppt):
                        # Merker für gerade gestoppte Ladung zurücksetzten.
                        self.LadenGestoppt = False
                        # Stoppe den Stromzähler-Tread
                        self.StopCounter.set()                        
                        # Schreibe den aktuellen Stand der er Cummulierten geladenen Energie-Menge im Hochvolt-Akku als End-Stand in die entsprechende globale Log-Variable
                        self.LogCumulativeChargedEnergyEnd=str(CumulativeChargedEnergy)
                        # Schreibe die Geladenen Energie-menge in die entsprechende globale Log-Variable
                        self.LogChargedEnergy=str(ChargedEnergy)
                        # Schreibe die Uhrzeit des ladeendes in die entsprechende globale Logvariable
                        self.LogChargeEnd=PowerCounterAkt.strftime("%H:%M:%S")
                        # Schreibe die Ladedauer in die entsprechende globale Logvariable
                        self.LogChargeDuration=str(TimeDiff)
                        # Scheibe den Ladungs-Typ in die entsprechende globale Logvariable
                        self.LogChargeTyp=self.root.ids.LadungsTyp.text
                        # Schreibe den Einheiten-Preis in die entsprechende globale Logvariable
                        self.LogPreis=self.root.ids.Preis.text
                        # Schreibe die Preisbasis für den Einheiten-Preis in die entsprechende globale Logvariable
                        self.LogPreisBasis=self.root.ids.PreisBasis.text
                        # Schreibe den aktuellen Tacho-Stand in die entsprechende globale Logvariable
                        self.LogOdoMeterValue=self.root.ids.km_Tacho.text
                        # Schreibe den aktuellen Stromzählerstand in die entsprechende globale Logvariable
                        self.LogReceivedEnergy=self.root.ids.PowerCounter.text
                        # Berechne die Kosten der Ladung
                        if self.LogPreisBasis == "Pauschale":
                            # Bei einer Pauschale ist der Pauschalen-Preis auch gleich der Ladungs-Kosten
                            KostenRaw=self.Preis
                        elif self.LogPreisBasis == "Min":
                            # Bei einem Minuten Preis berechnet sich die Kosten aus Ladungs-dauer mal Einheiten-Preis
                            KostenRaw=TimeDiff*self.Preis
                        else:
                            # Ansosnten wird nach kWh abgerechnet
                            if self.LogReceivedEnergy=="0.0":
                                # Falls kein Stromzähler vorhanden war, wird die eingelagerte Energiemenge als Berechnungs-Basis verwendet
                                KostenRaw=ChargedEnergy*self.Preis
                            else:
                                # Ansonsten wird der gezählte Wert des Stromzählers verwendet
                                KostenRaw=self.KiloWattStunden*self.Preis 
                        # Scheibe die Ladungs-Kosten in die entsprechende globale Logvariable
                        self.LogKosten=str(KostenRaw)
                        # Schreibe die aktuelle Spannung der Hilfsbatterie in die entsprechende globale Logvariable
                        self.LogAuxBat=self.root.ids.VoltBatAux.text                                                                            
                # Es konnten keine Energie-mengen Werte aus dem Rückgabe-string extrahiert werden
                else:
                    # Ausgabe für die nicht gefundenen Energie-Menge
                    self.SetToast("Keinen Relevanten Daten-Abschnitt für die Energie gefunden")
            # der PID-Befehl 2101 konnte nicht verargeitet werden
            else:
                # Ausgabetext für problematischen 2101-Befehl
                self.SetToast("2101 ist ein unbekannter Befehl")
            # Öffne die Web-Interface-Log-Datei
            fobj_out = open("/dev/shm/AktChargeState.txt","w")
            # Schreibe das Datum und die Urzeit in die Web-Interface-Log-Datei
            fobj_out.write(datetime.datetime.now().strftime("%d.%m.%Y -- %H:%M:%S")+"\r\n")
            # Schreibe den Ladungs-Typ ind die Web-Interface-Log-Datei
            fobj_out.write(self.LogTOC+"\r\n")
            # Schreibe den Ladezustand in die Web-Interface-Log-Datei
            fobj_out.write(self.LogCharging+"\r\n")
            # schreibe den State of Charge in die Web-Interface-Log-Datei
            fobj_out.write(self.LogSOC+"\r\n")
            # Schließe Web-Interface-Log-Datei
            fobj_out.close()
            # Warte 1 Sekunde bis zu nächsten Abfrage der OBD-PIDs
            time.sleep(1)
        # Abschalt-Befehl für den OBD-Dongel zusammen setzen
        Kommando='AT LP\r\n'
        # sende das Abschalt-Kommando an den OBD-Dongel
        obddataclose=self.init_Dongel(Kommando,"Dongel abschalten",Dongel)
        # Warte 2 Sekunden um das Abschalten wirksam werden zu lassen
        time.sleep(2)
        # Setze den Verindungs-Status zurück
        self.set_icons("ConnectState",0)
        # Setze den Ladungs-Typ zurück
        self.set_icons("ConnectType",0)
        # Setze den Ladungs-status zurück
        self.set_icons("ChargeState",0)
        # Öffne die Web-Interface-Log-Datei
        fobj_out = open("/dev/shm/AktChargeState.txt","w")
        # Schreibe das Datum und die Urzeit in die Web-Interface-Log-Datei
        fobj_out.write(datetime.datetime.now().strftime("%d.%m.%Y -- %H:%M:%S")+"\r\n")
        # Schreibe den Ladungs-Typ ind die Web-Interface-Log-Datei
        fobj_out.write(self.LogTOC+"\r\n")
        # Schreibe den Ladezustand in die Web-Interface-Log-Datei
        fobj_out.write(self.LogCharging+"\r\n")
        # schreibe den State of Charge in die Web-Interface-Log-Datei
        fobj_out.write(self.LogSOC+"\r\n")
        # Schließe Web-Interface-Log-Datei
        fobj_out.close()
        # Bringe den Connect-Button in einen released zustand --> Knopf ist nicht mehr eingedrückt.
        self.UnLockConnectButton()
        # Zeige an, dass die OBD-Ladungs-Überwachnug beendet ist
        self.SetToast("Ladungs-Überwachung beendet")
        # Schreibe die Erfassten daten in die Datenbank
        self.SendToDB()
        # OBD-Thread ist beended
        return

        
    # Extrahierung des gewünschten BMS-Wertes aus dem BMS-String
    # blockstart    --> gibt an in welchen Block die gewünschten Daten beginnen
    # blockende     --> gibt an welcher Block die geünschten Daten nicht mehr enthalten.
    # Stehen die Daten z.B. im 3. Daten-Block, so ist blockstart=3 und blockende=4.
    # Beginnen die Daten z.B. im 3. Daten-Block und erstrecken sich in den 4. Datenblock, so ist blockstart=3 und blockende=5.
    # pidstart      --> gibt das erste Byte in den extrahierten Blöcken an, bei dem die Daten stehen
    # pidend        --> Gibt das erste Byte nach den Daten in den extrahierten Blöcken an. Block-Identifier bei Daten über eine Blockgrenze hinweg werden dabei nicht mitgezählt
    # compumethod   --> Die Umrechnungsformel, welche als Divisor benötigt wird um aus dem HEX-Wert einen Physikalischen Wert zu machen.
    # Parameter:
    # self          --> Handel für App
    # commanddata   --> Daten-String als UTF-8-String welcher alle Rückgabe-Blöcke des OBD-Befehls enthält
    # pid           --> String mit dem Variablen-namen, für den die physikalischen Werte aus dem Daten-String extrahiert werden soll
    # return        --> Extrahierter physikalischer Wert
    #               --> -1  ==> Es kann der gewünschte physikalische Wert nicht extrahiert werden.
    #                           -1 wird momentan verwendet, da die aktuell abgefragten werte keine negativen physikalischen Werte besitzen. 
    #                           Das passiert, wenn ein Daten-Block angefordert wird, der nicht in dem aktuellen PID-Rückgabe-String enthalten ist.
    #                           Wird ein existierender Datenblock angeforgert, welcher aber nicht in dem aktuellen PID-Rückgabe-String enthalten ist, 
    #                           so wird ein nicht plausiebler wert zurückgegeben, welcher nicht abgefangen ist.
    def get_pid_data(self,commanddata,pid):
        # Extrahierungs-Daten und Umrechnungsformel für die Spannung der Hilfsbatterie auf PID 2101
        if pid=="AuxBat":
            blockstart=4
            blockende=5
            pidstart=10
            pidend=12
            compumethod = 10.0
        # Extrahierungs-Daten und Umrechnungsformel für die Eingelagerte Energie "CCE" auf PID 2101
        elif pid=="ChargedEnergy":
            blockstart=5
            blockende=7
            pidstart=-18
            pidend=-10
            compumethod = 10
        # Extrahierungs-Daten und Umrechnungsformel für das Ladungs-Zustand-Staus-Feld auf PID 2101
        if pid=="StatusField":
            blockstart=1
            blockende=2
            pidstart=12
            pidend=14
            compumethod = 1
        # Extrahierungs-Daten und Umrechnungsformel für Ladestand der Hochvolt-Batterie "SOC" auf PID 2105
        if pid == "SoCDisp":
            blockstart=4
            blockende=5
            pidstart=14
            pidend=16
            compumethod = 2
        # Extrahierung der benötigten Datenblöcke aus dem Daten-String
        matched_string_groups = re.search(str(blockstart)+':([^;]*)'+str(blockende)+':', commanddata)
        # Weiterverarbeitung wenn der Datenstring die gewünschten Blöcke enthält
        if matched_string_groups:
            # Merken der Block-Texte, welche vor den benötigten Blöcken steht
            first_matched_group_string = str(matched_string_groups.group(0))
            # Entfernen des Block-identifiers wenn sich de benötigten Daten über mehrere Datenblöcke erstecken.
            # Der Block-identifier darf mit der aktuellen Implementierung nur einstellig sein
            if blockende-blockstart>1:
                # der zu entfernende Blockidentifier ist damit 1 Zeichen lang
                blockmitte=blockstart+1
                # Der Blockidentifier plus dem zugehörigen Doppelpunkt werden entfernt
                first_matched_group_string = first_matched_group_string.replace(str(blockmitte)+':', '')
            # Die PID-Daten werden nun aus dem Block-String extrahiert
            pid_string = (first_matched_group_string[pidstart:pidend])
            # Die PID-Daten werden nun vom HEX-Format in eine Integer-Zahl umgewandelt.
            # Die resultierende Integer-Zahl wird dann mittels der Umrechnungsformel in einen physikalishen Wert Umgerechnet.
            pid_data=(int(pid_string, 16) / compumethod)
        # Abbruch, falls er Datenstring die gewünschten Blöcke nicht enthält
        else:
            pid_data=-1
        # Rückgabe des gewünschten physikalischen Wertes.
        return pid_data

                       
    # Initialisierung der OBD-Dongels, bzw. Abschaltung des Dongels wenn die Ladung beendet ist
    # self          --> Handel zur App
    # command       --> AT-Befehl, welcher an den OBD-Dongel geschickt weden soll
    # AusgabeText   --> Der zum AT-Befehl gehörende Textstring, welcher ausgegeben werden soll wenn der AT-Befehl abgearbeitet wird
    # OBD_Dongel    --> Handel zum Dongel
    # return        --> Rückgabe des datenstrings, welcher vom OBD-Dongel kommt.
    #                   Bei Fehlern enthät er die folgende Werte:
    #                   LeseFehler      ==> Der OBD-Dongel kann keine Daten zurückgeben
    #                   Fehler          ==> Es trat bei der Verarbeitung im Fahrzeug ein Fehler auf
    #                   Unknown command ==> Der Befehl ist dem Dongel unbekannt
    def init_Dongel(self,command,AusgabeText,OBD_Dongel):
        # Anzeige, dass jetzt ein OBD-Befehl an den Dongel geschickt wird        
        self.SetToast(AusgabeText)
        # OBD-Befehl an Dongel schicken
        # ByteBefehl=bytes(command, 'utf-8')
        OBD_Dongel.write(command.encode("ascii"))
        OBD_Dongel.flush()
        # Rückgabe-Variable Initialisieren
        seq = []
        # Start der OBD-Lese-Schleife
        while True:
            # abfangen des Lese-Fehlers, wenn der Dongel nichts zurücksendet
            try:
                reading = OBD_Dongel.read()
            # Abbrechen des Aktuellen Lese-Vorganges und Ausgabe eines Fehler-Textes
            except serial.serialutil.SerialException:
                verb="OBD-Dongel gelesen werden"
                local_data="LeseFehler"
                break                
            # Lesen war erfolgreich
            else:
                # Aktueller Datenblock an die vorhandenen Datenblöcke hängen 
                seq.append(reading)                
                # Wenn "ERROR" in der Rückgabe vorkommt, dann eine Fehler-Ausgabe machen und Schleife abbrechen
                if b'ERROR' in reading:
                    verb = "OBD-Dongel verarbeitet werden"
                    local_data="Fehler"
                    break
                # Wenn "?" in der Rückgabe vorkommt, dann "Unbekannter Befehl" ausgeben und Schleife abbrechen 
                elif b'?' in reading:
                    verb = "unbekannt"
                    local_data="Unknown command"
                    break
                # Wenn das ende des Blockes erricht ist, dann alle empfangenen Blöcke zu einem String zusammenfügen bereinigen und die lese-Schleife beenden
                elif b'>' in reading:
                    # Zu einem utf-8-String zusammenfügen
                    local_data = b' '.join(seq).decode("utf-8")
                    # Alle Leerzeichen, alle Minus und alle Return entfernen
                    local_data = local_data.replace(' ', '').replace('-', '').replace('\r', '')
                    verb = "abgearbeitet"
                    break
        # Ausgabe, dass der OBD-Befehl abgearbeitet ist
        if "Fehler" in local_data:
            self.SetToast("Der Befehl {} kann nicht vom {}".format(command, verb))
        else:
            self.SetToast("Befehl {} ist {}".format(command, verb))
        # Rückgabe des empfangenen Strings.      
        return local_data


    # Abfrage des BMS über die OBD-Kommandos 2101 und 2105
    # self          --> Handle zur App
    # PID_Nummer    --> Nummer des PID, welcher abgefragt werden soll
    # OBD_Dongel    --> Handel zum Dongel
    # return        --> Rückgabe des datenstrings, welcher vom OBD-Dongel kommt.
    #                   Bei Fehlern enthät er die folgende Werte:
    #                   LeseFehler      ==> Der OBD-Dongel kann keine Daten zurückgeben
    #                   Fehler          ==> Es trat bei der Verarbeitung im Fahrzeug ein Fehler auf
    #                   Unknown command ==> Der Befehl ist dem Dongel unbekannt
    def get_bms_data(self, PID_Nummer, OBD_Dongel):
        # Anzeige, dass jetzt ein OBD-Befehl an den Dongel geschickt wird
        self.SetToast("PID {} abfragen".format(PID_Nummer))
        # New-Line und return hinzufügen, damit der Befehl vom Dongel als abgeschlossen erkannt wird.
        OBD_Befehl=PID_Nummer+"\r\n"
        # OBD-Befehl an Dongel schicken        
        OBD_Dongel.write(OBD_Befehl.encode("ascii"))
        OBD_Dongel.flush()
        # Rückgabe-Variable Initialisieren
        seq = []
        # Start der OBD-Lese-Schleife
        while True:
            # abfangen des Lese-Fehlers, wenn der Dongel nichts zurücksendet
            try:
                reading = OBD_Dongel.read()
            # Abbrechen des Aktuellen Lese-Vorganges und Ausgabe eines Fehler-Textes
            except serial.serialutil.SerialException:
                verb="OBD-Dongel gelesen werden"
                local_data="LeseFehler"
                break                
            # Lesen war erfolgreich
            else:
                # Aktueller Datenblock an die vorhandenen Datenblöcke hängen 
                seq.append(reading)                
                # Wenn "ERROR" in der Rückgabe vorkommt, dann eine Fehler-Ausgabe machen und Schleife abbrechen
                if b'ERROR' in reading:
                    verb = "OBD-Dongel verarbeitet werden"
                    local_data="Fehler"
                    break
                # Wenn "?" in der Rückgabe vorkommt, dann "Unbekannter Befehl" ausgeben und Schleife abbrechen 
                elif b'?' in reading:
                    verb = "unbekannt"
                    local_data="Unknown command"
                    break
                # Wenn das ende des Blockes erricht ist, dann alle empfangenen Blöcke zu einem String zusammenfügen bereinigen und die lese-Schleife beenden
                elif b'>' in reading:
                    # Zu einem utf-8-String zusammenfügen
                    local_data = b' '.join(seq).decode("utf-8")
                    # Alle Leerzeichen, alle Minus und alle Return entfernen
                    local_data = local_data.replace(' ', '').replace('-', '').replace('\r', '')
                    verb = "abgearbeitet"
                    break
        # Ausgabe, dass der OBD-Befehl abgearbeitet ist
        if "Fehler" in local_data:
            self.SetToast("Der PID {} kann nicht vom {}".format(PID_Nummer, verb))
        else:
            self.SetToast("PID {} ist {}".format(PID_Nummer, verb))
        # Rückgabe des empfangenen Strings.
        return local_data    
 
    
    # Aktuelle Log-Daten an die Datenbank übergeben.
    # Aktuelle implementierung der Datenbank ist eine CSV-Datei,
    # Da Verbrauchswerte jeweils Jährlich erfasst werden wird es keinen überlauf in der CSV-Datei geben.
    # Eine richtige Datenbank währe möglich, aber das währe mit Kanonen auf Spatzen geschossen.
    # self  --> Handel zur App
    def SendToDB(self):
        # Bereitstellen der Log-variablen in der richtigen Spalten-Reihenfolge.
        fields=[self.LogDate,self.LogTime,self.LogChargeTyp,self.LogPreisBasis,self.LogPreis,self.LogOdoMeterValue,self.LogChargeStart,self.LogChargeEnd,self.LogCumulativeChargeEnergyStart,self.LogCumulativeChargedEnergyEnd,self.LogReceivedEnergy,self.LogAuxBat,self.LogChargeDuration,self.LogChargedEnergy,self.LogKosten]
        # Öffnen der CSV-Datei
        with open(r'/media/pi/INTENSO/IoniqDB.csv', 'a') as csvfile:
            # Schreib-Handel für CSV-Datei initialisieren
            writer = csv.writer(csvfile, delimiter =";")
            # Schreiben des Datensatzes
            writer.writerow(fields)

    # start des Stromzähler-Treads
    # self  --> Handel zur App
    def start_counter_thread(self):
        threading.Thread(target=self.counter_thread, args=()).start()

    # Strom-Zähler-Thread
    # Zählt die Impulse am GPIO-port, welcher an den S0-Opto-Koppler des Strom-Zählers angeschlossen ist.
    # Spannungs-Spezigfikation des S0-Opto-Koppler: 5V-27V
    # self  --> Handel zur App    
    def counter_thread(self):
        # Impuls-Zähler wird mit 0 initialisiert
        WattStundenCount=0
        # Toggel-Verhinderer wird auf false initialisiert
        NoToggle=False
        # Globaler Strom-Zähler wird auf 0 initialisiert
        self.KiloWattStunden=0.0
        # Start der Strom-Zähler-Thread-Schleife
        while True:
            # Beenden der Strom-Zähler-Thread-Schleife
            if self.StopCounter.is_set() or self.LadenGestoppt==bool(1):
                # Anzeige was den Strom-Zähler-Trgead angehalten hat
                if self.StopCounter.is_set():
                    self.SetToast("Halte Stromzähler über Thread an")
                else:
                    self.SetToast("Halte Stromzähler über OBD-Daten an")
                break
            # Beim Wechsel von LOW auf High wird der Impuls-Zähler um 1 erhöt
#            if GPIO.input(5) == GPIO.HIGH and not NoToggle:
                # Zähler erhöhen
#                WattStundenCount=WattStundenCount+1
                # Toggel-Verhinderer wird gesetzt
#                NoToggle=True
                # Umrechnung des Impulszählers von Watt-Stunden in Kilowatt-Stunden
#                self.KiloWattStunden=WattStundenCount/1000
                # Ausgabe des Impulszählers in Kilowatt-Stunden
#                self.set_gui_text("PowerCounter",self.KiloWattStunden)
                # Warte 0,1 Sekunden bis zum nächsten auslesen des S0-Ports
#                time.sleep(0.1)
            # Beim Wechsel von HIGH auf LOW wird der Toggel-Verhinderer wieder zurückgesetzt
#            if GPIO.input(5) == GPIO.LOW:
                # Zurücksetzen des Toggel-Verhinderer
#                NoToggle=False
                # Warte 0,1 Sekunden bis zum nächsten auslesen des S0-Ports
#                time.sleep(0.1)
        # Thread ist beendet
        return

    # Connect-Button in die Start-Lage zurück-setzen
    # Ist Teil des Haupt-Threads und wird vom OBD-Thread angesprungen
    # self  --> Handel zur App     
    @mainthread
    def UnLockConnectButton(self):
        self.root.ids.ConectButton.state="normal"

    # Anzeige der Toast-Texte
    # Ist Teil des Haupt-Threads und wird vom OBD-Thread angesprungen
    # self  --> Handel zur App 
    # Text  --> Text-String welcher angezeigt werden soll
    @mainthread
    def SetToast(self,Text):
        # Toast-Text Anzeigen
        self.root.ids.Toast.text=Text
        # Toast-Zähler hochzählen
        self.NumToasts=self.NumToasts+1
        # Toast-Text nach einer Sekunde löschen
        Clock.schedule_once(self.ClrToast, 1)

    # Ausblenden des Toast-Textes nach einer gewissen Zeit
    # Ist Teil des Haupt-Threads und wird vom OBD-Thread angesprungen
    # self  --> Handel zur App
    # dt    --> Zeit bis zum Aufruf der Futnktion 
    @mainthread
    def ClrToast(self,dt):
        # löschen des Letzen Anzeige-Textes
        if self.NumToasts==1:
            self.root.ids.Toast.text =""
        # Zähler um Eins erniedrigen
        self.NumToasts=self.NumToasts-1

    # Anzeige des Verbindungs-Status in der Menu-Leiste
    # Ist Teil des Haupt-Threads und wird vom OBD-Thread angesprungen
    # self      --> Handel zur App
    # typ       --> String mit dem Element, für das eine Status-Änderung angezeigt werden soll
    # status    --> Der neue Status für das Element
    @mainthread
    def set_icons(self,typ,status):
        # Verbindungs-Status zum OBD-Dongel
        if typ=="ConnectState":
            # Verbingung steht und OBD-Dongel ist initialisiert
            if status==2:
                self.root.ids.ComunicationTo.icon = "auto_gruen.png"
            # Verbingung steht
            if status==1:
                self.root.ids.ComunicationTo.icon = "dongel_gruen.png"
            # Verbingung wurde nicht aufgebaut
            elif status==0:
                self.root.ids.ComunicationTo.icon = "dongel_rot.png"
        # Verbindungs-status des Ladesteckers
        if typ=="ConnectType":
            # CSS-Ladestecker ist eingesteckt
            if status==2:
                self.root.ids.ConectorType.icon = "typ2_ccs_ccs_connected.png"
                self.LogTOC="typ2_ccs_ccs_connected"
            # Typ2-Stecker ist eingesteckt
            elif status==1:
                self.root.ids.ConectorType.icon = "typ2_ccs_typ2_connected.png"
                self.LogTOC="typ2_ccs_typ2_connected"
            # es ist nichts eingesteckt
            else:
                self.root.ids.ConectorType.icon = "typ2_ccs_not_connected.png"
                self.LogTOC="typ2_ccs_not_connected"
        # Zustand der aktuellen Ladung
        if typ=="ChargeState":
            # Es wird geladen
            if status == 1:
                self.root.ids.ChargingState.icon = "blitz_gruen.png"
                self.LogCharging="blitz_gruen"
            # Es wird nicht geladen, bzw. noch nicht geladen
            else:
                self.root.ids.ChargingState.icon = "blitz_rot.png"
                self.LogCharging="blitz_rot"


    # Lesen des inifiles
    # Ist Teil des Haupt-Threads und wird vom Uhr-Thread angesprungen
    # self  --> Handel zur App
    @mainthread
    def read_ini_file(self):
        # Ini-File einlesen
        self.config.read('/media/pi/INTENSO/consumptionmonitor.ini')
        # Preis für eine kWh beim Heimladen auslesen
        homepreis=self.config['DEFAULT']['preis']
        # Preis in der GUI eintragen
        self.root.ids.Preis.text=homepreis
        # Preis in dei Globale Variable für den Preis eintragen
        self.Preis=float(homepreis)

    # Berechne die aktuelle Uhrzeit und setze sie in der Menu-Leiste
    # Ist Teil des Haupt-Threads und wird vom Uhrzeit-tread angesprungen
    # self  --> Handel zur App
    @mainthread
    def SetzeDatumUndZeit(self):
        self.root.ids.DatumLabel.text = datetime.datetime.now().strftime("%d.%m.%Y -- %H:%M:%S")


    # Zeige die ausgelesenen und berechneten OBD-Werte auf der GUI an
    # Ist Teil des Haupt-Threads und wird vom OBD-tread angesprungen  
    # self  --> Handel zur App
    # typ   --> Bezeichnung der physikalischen Größe, für welche der neue Wert auf der GUI angezeigt werden soll
    # Wert  --> Physikalischer Wert der auf der GUI angezeigt werden soll
    @mainthread
    def set_gui_text(self,typ,Wert):
        # State of charge
        if typ=="SoC":
            # Anzeige als Wert
            self.root.ids.SoC_Value.text=str(Wert)
            # Anzeige als Fortschritsbalken
            self.root.ids.SoC_Bar.value=Wert
        # Spannung der Hilfsbatterie
        elif typ=="AuxBat": 
            self.root.ids.VoltBatAux.text=str(Wert)
        # Eingelagerte Energie-Menge
        elif typ=="ChargedEnergy":
            self.root.ids.PowerCar.text=str(Wert)
        # Bezogene Energie-menge
        elif typ=="PowerCounter":
            self.root.ids.PowerCounter.text=str(Wert)
        # Ladedauer
        elif typ=="ChargeTime":
            self.root.ids.ChargeTime.text=str(Wert)
     
 
    # Aktionen beim normalen beenden des Scripts:
    # The Kivy event loop is about to stop, set a stop signal;
    # otherwise the app window will close, but the Python process will
    # keep running until all secondary threads exit.  
    # self  --> Handel zur App    
    def on_stop(self):
        # Uhr-Thread anhalten
        self.root.StopUhr.set()
        # OBD-Thread anhalten
        self.root.StopOBD.set()
        # Stromzähler-thread anhalten
        self.StopCounter.set()
        # Sichern des Preis für eine kWh bei einer Heim-Ladung
        if self.root.ids.PreisBasis.text=="Home":
            # Handel des Config-Parsers
            self.config = configparser.ConfigParser()
            # den Aktuellen Preis aus der globalen variable einlesen und in die Ini-Configuration eintragen
            self.config['DEFAULT'] = {'preis': self.root.ids.Preis.text}
            # Ini-Datei schreiben
            with open('/media/pi/INTENSO/consumptionmonitor.ini', 'w') as configfile:
                self.config.write(configfile)

    # einblenden einer Zahlen-Tastatur, wenn der Tacho-Stand oder der Preis eingegeben werden muss.
    # self      --> Handel zur App
    # button    --> Handel zum Button in der GUI, welcher die Touch-Tastatur angefordert hat
    # gui       --> Handel zum Root-Element der gui
    # app       --> Handel zur App
    def OpenKeyBoard(self, button, gui, app):
        # Globale Variable anlegen welche das Handel zum Aufrufenden GUI-Button enthalten soll
        global Knopf
        # Auf die Globale Variable für den GUI-Button wird der handel des Aufrufenden Buttons geschrieben
        Knopf = button
        # Touch-Tastatur wird erzeugt und eingebelendet
        Factory.KeyBordPopup().open()
        
        
    # Zeige die Eingegebenen Werte als Button-Text an.
    # self          --> Handel zur App
    # EingabeWert   --> String, welcher auf dem GUI-Button als Text erscheinen soll
    def SetzeEingabewert(self, EingabeWert):
        # Setze Knopf-Text
        Knopf.text = EingabeWert
        # Aktualisiere den Preis in der globalen variable, falls der Preis angepasst wurde
        if Knopf == self.root.ids.Preis:
            self.Preis = float(EingabeWert)

    # löschen der letzen Ziffer in der Touch-Tastatur 
    # self      --> Handel zur App
    # button    --> Handel zum Del-Button der Touch-Tastatur
    # gui       --> Handel zum Root-Element der gui
    # app       --> Handel zur App    
    def DelZeichen(self, button, gui, app):
        # Den Text aus der Anzeige einlesen und dabei das letzte Zeichen ignorieren
        tmptxt = gui.ids.EingabeListe.text[0:-1]
        # Den neuen verkleinerten Text anzigen
        gui.ids.EingabeListe.text = tmptxt

    # Das Root-Widget einblenden
    # self      --> Handel zur App
    def build(self):
        return RootWidget()

# Haupt-Schleife
if __name__ == '__main__':
    ConsumptionMonitorApp().run()
