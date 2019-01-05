<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0;" />
        <link href="navigation.css" type="text/css" rel="stylesheet" />
        <title>ConsumptionMonitor --> Ladestatus  IONIQ 'Blaue Elise'</title>
        <style>
            /* Raum für SVG-Grafik, wo der Lade-Kreis eingezeivhnet werden soll */
            svg 
            {
                width: 200;
                padding: 0;
                height: 200px;
                background: white;
            }
        </style>
    </head>
    <body id="Ladezustand">
        <h1>Consumtion-Monitor -- IONIQ 'Blaue Elise'</h1>
        <!-- Einfache Navigations-leiste --> 
        <main>
            <ul id="navibereich">
                <li id="navi01"><a href="ConsumptionMonitor_Ladezustand.php">Ladezustand</a></li>
                <li id="navi02"><a href="ConsumptionMonitor_Tabelle.php">Ladungs-Übersicht</a></li>
                <li id="navi03"><a href="ConsumptionMonitor_Statistik.php">Ladungs-Statistik</a></li>
            </ul>
            <!-- PHP-Script, welches den aktuellen Ladezustand aus einer Temporären Datei
            im Verzeichnis /dev/shm/ ausliest und als Lade-Kreis darstellt. -->
            <?php
                // Auslesen der Status-Datei
                $AktState = file ("/dev/shm/AktChargeState.txt");
                $Logtime=$AktState[0];
                $Ladestatus=$AktState[2];
                $Ladetyp=$AktState[1];
                $SoC=$AktState[3];
                $SoCText=$SoC."%";  
                // Initialisierung der Zeichnung
                $cr=90;
                $cx=100;
                $cy=100;
                $winkel_start = 270;
                // Berechnung des Ladebalkens
                $winkel_end = 360/100*$SoC;
                $winkel_end=$winkel_start+$winkel_end;
                // Ist der End-Winkel größer als der Nullpunkt bei 0°/360°, wird der Rest-Winkel berechnet
                if ($winkel_end >= 360) 
                {
                    $winkel_end=$winkel_end-360;
                }
                // Festlegung der Zeichenrichtung 
                if ($SoC>50) 
                {
                    // Der Kreis geht über den Nullpunkt hinaus
                    $BTyp="1,1";
                }
                else 
                {
                    // der Kreis endet vor dem Nullpunkt
                    $BTyp="0,1";
                }
                // Festlegung der Farben des Ladebalkens je nach Ladezustand
                if ($SoC <= 20) 
                {
                    $Farbe="red";
                } 
                else if ($SoC <= 40) 
                {
                    $Farbe="orange";
                } 
                else if ($SoC <=60) 
                {
                    $Farbe="yellow";
                } 
                else if ($SoC<=80) 
                {
                    $Farbe="cyan";
                } 
                else 
                {
                    $Farbe="Green";
                }
                // Detektierung der Text-Länge, um die Textuelle Prozentangabe einigermaßen platzieren zu können
                $MF=strlen($SoCText)*5;
                // Berechnung der Text-Position
                $desc_x = $cx -$MF;
                $desc_y = $cy +5;
                if ($SoC<100) 
                {    
                    // Berechnung der Kreis-Parameter über die Winkelfunktionen wenn SoC < 100%
                    $psx = round(cos(deg2rad($winkel_start)) * $cr + $cx);
                    $psy = round(sin(deg2rad($winkel_start)) * $cr + $cy);
                    $pex = round(cos(deg2rad($winkel_end)) * $cr + $cx);
                    $pey = round(sin(deg2rad($winkel_end)) * $cr + $cy);
                }
                // Ausgabe der aktualität der erfassten Ladezustandsdaten
                echo "<p>Letzte Aktualisierung: ".$Logtime."</p>";
                // Zeuichnen des Ladekreises
                echo "<figure>\n";
                echo "<svg viewbox=\"0 0 200 200\">\n";
                // Bild-Bezeichnung
                echo "  <desc>Prozentanzeige</desc>\n";
                // Kreis als Füllung zeichnen
                echo "  <circle cx=$cx cy=$cy r=$cr fill=\"blue\" />";
                if ($SoC<100) 
                {  
                    // Berechnetes Kreissegment bei SoC kleiner 100% zeichnen
                    echo "  <path d=\"M $psx,$psy A $cr,$cr 0 $BTyp $pex,$pey\" stroke=$Farbe stroke-width=\"10px\" fill=\"none\" Z/>\n";  
                }
                else 
                {
                    // Voll-Kreis bei 100% SoC zeichnen
                    echo " <circle cx=$cx cy=$cy r=$cr fill=\"none\" stroke=\"lime\" stroke-width=\"10\" />";
                }
                // Prozent-Angabe als Text in die Kreis-Mitte zeichen
                echo "  <text x=\"$desc_x\" y=\"$desc_y\" font-size=\"20\" fill=\"#000000\">$SoCText</text>\n";
                // Piktogramm für den erkannten Lade-Typ oberhalb der Prozent-Anzeige einblenden
                echo "  <image x=78 y=35 width=50 height=40 xlink:href=\"".$Ladetyp.".svg\"><title>".$Ladetyp."</titlt></image>/n";
                // Piktogramm für den Ladezustand (Laden/ nicht Laden) unterhalb der  Prozent-Anzeige einblenden
                echo "  <image x=80 y=120 width=40 height=40 xlink:href=\"".$Ladestatus.".svg\"><title>".$Ladestatus."</title></image>\n";                    
                echo "</svg>\n";
            ?>
        </main>
    </body>
</html>
