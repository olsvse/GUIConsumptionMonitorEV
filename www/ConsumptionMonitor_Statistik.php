<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <link href="navigation.css" type="text/css" rel="stylesheet" />
        <title>ConsumptionMonitor --> Ladungs-Statistik IONIQ 'Blaue Elise'</title>
        <style>
        </style>
    </head>
    <body id="Statistik">
        <h1>Consumtion-Monitor -- IONIQ 'Blaue Elise'</h1>
        <!-- Einfache Navigations-leiste --> 
        <ul id="navibereich">
            <li id="navi01"><a href="ConsumptionMonitor_Ladezustand.php">Ladezustand</a></li>
            <li id="navi02"><a href="ConsumptionMonitor_Tabelle.php">Ladungs-Übersicht</a></li>
            <li id="navi03"><a href="ConsumptionMonitor_Statistik.php">Ladungs-Statistik</a></li>
        </ul>    
        <br>
        <br>
        <?php
            // Bis-Datum festlegen
            // Kontrolle ob Status-Datei existiert
            if (file_exists("StartData.txt"))
            {
                // Wenn Datei existiert, diese Auslesen
                $StartState = file ("StartData.txt");
                // Datumsstring in das richtige Format bringen
                $DatumArray = array_map('trim', explode('.', $StartState[0]));
                $BisDate=$DatumArray[2]."-".$DatumArray[1]."-".$DatumArray[0];
            }
            else
            {
                // Wenn Datei nicht existiert oder nicht zugegriffen werden kann, aktuelles Datum auslesen
                $BisDate=date("Y-m-d");
            }
            // Formular Mit Datumspicker anlegen
            echo "<form action=\"ConsumptionMonitor_Statistik.php\" method=\"get\">";
            echo "    <p>Zeitraum von: <input type=\"date\" name=\"VonDatum\" min=\"2018-01-25\" max=\"".$BisDate."\" value=\"2018-01-25\"/> bis: <input type=\"date\" name=\"BisDatum\" min=\"2018-01-28\" max=\"".$BisDate."\" value=\"".$BisDate."\"/> <input type=\"submit\" value=\"absenden\" /></p>";
            echo "</form>";
            // Testen ob eingelesene Datumswerte an die Seite übergeben sind
            if (array_key_exists('VonDatum', $_GET) &&  array_key_exists('BisDatum', $_GET) && ($_GET['VonDatum']!="" && $_GET['BisDatum']!="" )) 
            {
                // Start-Datum extrahieren und zerlegen
                $StartDatumArray=explode ("-",$_GET['VonDatum']);
                // Start-Datum-String im richtigen Format zusammensetzen
                $StartDatum=$StartDatumArray[2].".".$StartDatumArray[1].".".$StartDatumArray[0];
                // End-Datum extrahieren und zerlegen
                $EndDatumArray=explode ("-",$_GET['BisDatum']);
                // End-Datum-String im richtigen Format zusammensetzen
                $EndDatum=$EndDatumArray[2].".".$EndDatumArray[1].".".$EndDatumArray[0];
                // Datums-Strings in Datumswerte Umwandeln
                $datevon = strtotime($StartDatum);
                $datebis = strtotime($EndDatum);
                // Testen ob das Enddatum vor dem Startdatum ist
                if ($datebis<$datevon)
                {
                    // Dann die Daten drehen
                    $tmpDate=$datevon;
                    $datevon=$datebis;
                    $datebis=$tmpDate;
                    $tempDatum=$StartDatum;
                    $StartDatum=$EndDatum;
                    $EndDatum=$tempDatum;
                }
                // Titelausgeben.
                echo "<h2> Zeitraum vom ".$StartDatum." bis ".$EndDatum."</h2>";
                // Ergebnis-Arrays anlegen
                $Brutto=array();
                $Netto=array();
                $Recu=array();
                $BleiAnker=array();
                $Achse=array();
                $Tagesstrecke=array();
                // initialisierung der Ergebnis-Variablen
                $StromBezogen=0;
                $EingelagerterStrom=0;
                $StromKosten=0.0;
                // initialisierung der Memory-Variablen auf Plausieble und passende Altwerte
                $dateLogAlt=strtotime("24.01.2018");
                $RecuWertEnergieAlt=0;
                $TachostandTagAlt=0;
                $TachostandNeu=0;
                $LadungsTypAlt="Vollladung";
                // CSV-datei auslesen
                $csvFile = "IoniqDB.csv";
                $handle = fopen($csvFile, "r");
                // Schleife Durch die CSV-Datei
                while(($data = fgetcsv($handle,0, ";"))!=FALSE) 
                {
                    // Erste Spalte des Datensatzes auslesen
                    $dateLog = strtotime($data[0]);
                    // Erkennen welchem Zeitruam der Datensatz zugeordnet werden kann
                    if ($dateLog<$datevon)
                    {
                        // Der Logeintrag ist vor dem gewünschten Zeitraum
                        $StateActiveDate=0;
                    }
                    elseif (($dateLog>=$datevon) && ($dateLog<=$datebis))
                    {        
                        // Der Logeintrag ist in dem gewünschten Zeitraum
                        $StateActiveDate=1;
                    } 
                    else
                    {        
                        // Der Logeintrag ist nach dem gewünschten Zeitraum 
                        $StateActiveDate=2;
                    }                   

                   // Die entsprechenden Werte des Datensatzes Als Alt-Werte erfassen, solange noch nicht das Startdatum erreicht wurde
                    if ($StateActiveDate==0)
                    {
                        // Alter Tachosstand (Tages-Zähler)
                        $TachostandTagAlt=$data[5];
                        // Alter Tachosstand (Gesamt-Zähler)
                        $TachostandAlt=$data[5];
                        // End-wert für Eingelagerte Energiemenge als Altwert für due recuperierte EnergieMenge während des letzen ladens
                        $RecuWertEnergieAlt=str_replace(",",".",$data[9]);
                        // End-wert für Eingelagerte Energiemenge als Startwert für due recuperierte EnergieMenge während des letzen ladens
                        $RecuStartWert=str_replace(",",".",$data[9]);
                    }
                    // Testen ob Datensatz innerhalb des Auswertungs-Zeitraums ist.
                    if ($StateActiveDate==1)
                    {
                        // Datensatz ist innerhalb des Auswertungs-Zeitraums.
                        // Testen ob eine "Vollladung" oder eine Teil- bzw.Stützladung vorliegt
                        if ($data[2]=="Vollladung")
                        {
                            // Es liegt eine Vollladung vor.
                            // Tachostand für gewünschten Zeitraum berechnen
                            $Tachostand=$data[5]-$TachostandAlt;
                            // Tachostand als Endwert für die tagsstrecke ablegen 
                            $TachostandTagEnde=$data[5];
                            // Tages-Strecke ausrechnen
                            $TachostandTag=$TachostandTagEnde-$TachostandTagAlt;
                            // Gesamte eingelagerte Energiemenge ablegen (Enthält Recuperierte Energie-Menge)
                            $EingelagerterStromGesamt=str_replace(",",".",$data[9]); 
                            // Gesamte bezogene Energie-Menge ablegen
                            $StromBezogen=$StromBezogen+str_replace(",",".",$data[10]);
                            // Gesamte eingelagerte Energiemenge ablegen (Ohne Rekuperierte Energie-menge)
                            $EingelagerterStrom=$EingelagerterStrom+str_replace(",",".",$data[13]);
                            // Aufsumierte Stromkosten ablegen
                            $StromKosten=$StromKosten+str_replace(",",".",$data[14]);            
                            // Testen ob der letzte Datensatz eine Volafdung war
                            if ($LadungsTypAlt=="Vollladung")
                            {
                                // Der letzte Datensatz war eine Volladung
                                // Berechnung des Aktuellen Brutto-Verbrauchs
                                $BruttoWert=(str_replace(",",".",$data[10]))/$TachostandTag*100;
                                // Berechnung des Aktuellen Netto-Verbrauchs
                                $NettoWert=(str_replace(",",".",$data[13]))/$TachostandTag*100;
                                // Berechnung der Aktuellen rekuperierten Energie
                                $RecuWertEnergieAkt=str_replace(",",".",$data[9]);                            
                                $RecuWertEnergie=$RecuWertEnergieAkt-$RecuWertEnergieAlt;
                                // Berechnung des Aktuellen Verbrauchs mit rekuperierter Energie
                                $RecuWert=$RecuWertEnergie/$TachostandTag*100;
                            }
                            else
                            {
                                // Der letzte datensatz war keine Volladung
                                // Berechnung des Aktuellen Brutto-Verbrauchs unter Aufsummierung der Alten werte
                                $BruttoWert=((str_replace(",",".",$data[10]))+$EnergieBezogenAlt)/$TachostandTag*100;
                                // Berechnung des Aktuellen Netto-Verbrauchs unter Aufsummierung der Alten werte
                                $NettoWert=((str_replace(",",".",$data[13]))+$EnergieGeladenAlt)/$TachostandTag*100;
                                // Berechnung der Aktuellen rekuperierten Energie
                                $RecuWertEnergie=$RecuWertEnergieAkt-$RecuWertEnergieAlt;
                                // Berechnung des Aktuellen Verbrauchs mit rekuperierter Energie unter Aufsummierung der Alten werte
                                $RecuWert=$RecuWertEnergie/$TachostandTag*100;              
                            }
                            // Alblage der Werte für die Grafiken
                            // Ablage des Brutto-Wertes in das Brutto-Array
                            $Brutto[]=$BruttoWert;
                            // Ablage des Netto-Wertes in das Netto-Array
                            $Netto[]=$NettoWert;
                            // Ablage des Recu-Wertes in das Recu-Array
                            $Recu[]=$RecuWert;
                            // Ablage der Hilfsbatterie-Spannung in das Hilfsbatterie-Array
                            $BleiAnker[]=str_replace(",",".",$data[11]);
                            // Ablage der Log-Datums-werte als Achse
                            $Achse[]=$data[0];
                            // Ablage gefahrenen Tagesstrecke in das stecken-Array
                            $Tagesstrecke[]=$TachostandTag;
                            // Ablage der Gesamt-energie-menge als Memory wert für die berechnung der Rekuperierten energie
                            $RecuWertEnergieAlt=$RecuWertEnergieAkt;
                            // Alblage des Aktuellen Tachostandes als Memory wert für die berechnung der Tages-Strecke
                            $TachostandTagAlt=$TachostandTagEnde;
                        }
                        else
                        {
                            // Es liegt eine Teil- bzw.Stützladung vorliegt
                            // Testen ob der letzte Datensatz eine Volladung war.
                            if ($LadungsTypAlt=="Vollladung")
                            {
                                // war der Letzte datensatz eine Volladung, dann die Werte als Zwischen Größen Abspeichern
                                $EnergieGeladenAlt=str_replace(",",".",$data[13]);
                                $EnergieBezogenAlt=str_replace(",",".",$data[10]);            
                            }
                            else
                            {
                                // War der letzte Datensatz keine Volladung, dann den Aktuellen Adtensatz zu den werten der letzten Ladung Hinzuzählen.
                                $EnergieGeladenAlt=$EnergieGeladenAlt+str_replace(",",".",$data[13]);
                                $EnergieBezogenAlt=$EnergieBezogenAlt+str_replace(",",".",$data[10]);
                            }
                        }
                        // Aktuellen Datentyp als Memory-Variable ablegen
                        $LadungsTypAlt=str_replace(",",".",$data[2]);
                        // Das aktuelle Datensatz-Datum als Memory-variable Ablegen
                        $dateLogAlt=$dateLog;
                    }
                }
                // CSV-Datei Schließen
                fclose($handle);
                // Berechnung der Ladeverluste 
                $Ladeverluste=100-(($EingelagerterStrom/$StromBezogen)*100);
                // Berechnung des Netto-Verbrauchs
                $VerbrauchNetto=$EingelagerterStrom/$Tachostand*100;
                // Berechnung des Brutto-Verbrauchs
                $VerbrauchBrutto=$StromBezogen/$Tachostand*100;
                // Berechnung des Verbrauchs unter einbeziehung der Recukerierten Energie
                $VerbrauchRecu=($EingelagerterStromGesamt-$RecuStartWert)/$Tachostand*100;
            }
            else
            {
                // Info ausgeben, dass der gewählte Zeitraum nicht gültig ist. 
                echo "<p>Der gewählte Zeitraum ist ungültig!</p>";
            }
            // Ausgabe-Tabelle für den gewählten Zeitraum Anlegen
            echo "<table>\n";
            echo "<tr>\n";
            echo "<td>Gesamtstrecke:</td>\n";
            echo "<td>".$Tachostand."</td>\n";
            echo "<td> km</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Bezogene Strommenge:</td>\n";
            echo "<td>".$StromBezogen."</td>\n";
            echo "<td> kWh</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Geladene Strommenge:</td>\n";
            echo "<td>".$EingelagerterStrom."</td>\n";
            echo "<td> kWh</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Kosten für die bezogene Strommenge:</td>\n";
            echo "<td>".$StromKosten."</td>\n";
            echo "<td> €</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Ladeverluste:</td>\n";
            echo "<td>".$Ladeverluste."</td>\n";
            echo "<td> %</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Netto-Verbrauch:</td>\n";
            echo "<td>".$VerbrauchNetto."</td>\n";
            echo "<td> kWh/100km</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Brutto-Verbrauch:</td>\n";
            echo "<td>".$VerbrauchBrutto."</td>\n";
            echo "<td> kWh/100km</td>\n";
            echo "</tr>\n";
            echo "<tr>\n";
            echo "<td>Netto-Verbrauch mit Rekuperierter Energie:</td>\n";
            echo "<td>".$VerbrauchRecu."</td>\n";
            echo "<td> kWh/100km</td>\n";
            echo "</tr>\n";
            echo "</table>\n";
        ?>
    </body>
</html>
