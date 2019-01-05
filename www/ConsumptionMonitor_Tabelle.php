<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <link href="navigation.css" type="text/css" rel="stylesheet" />
        <title>ConsumptionMonitor --> Ladungs-Übersicht IONIQ 'Blaue Elise'</title>
        <style>
            /* Tabelle ist mit einem Rahmen versehen */
            table
            {
                border-collapse: collapse;  /* Rahmen der Zellen werden zusammen dargestellt */
                line-height: 1;             /* zeilenhöhe des Textes */
                border: 1px solid black;    /* Linienstärke des Rahmens 1 Px */
            } 
            /* Tabellen-Überschrift is Fixiert */
            thead th 
            {
                position: -webkit-sticky;   /* Tabellen-Überschrift is Fixiert */
                position: sticky;           /* Tabellen-Überschrift is Fixiert */
                top: 0;                     /* 0 damit der Tabellenkopf nicht wegscrollt */
            }    
            /* Formatierung der Kopfzellen */
            th
            {
                vertical-align: top;                                    /* Text-Aurichtung Oben */
                text-align: Start;                                      /* Text fängt vorne an */              
                padding-top: 0.3em;
                padding-bottom: 0.3 em;
                padding-left:0.2em;
                padding-right:0.2em;
                border: 1px solid black;                                /* Linienstärke am Zellenrand ist 1 px */
                background-image: linear-gradient(#f9f9f9, #e3e3e3);    /* Hintergrung als Verlauf */
            }            
            /* Simulierte Linie am unteren Ende der Kopf-Zellen */
            thead th
            {
                vertical-align: bottom;	        /* Textausrichtung unten, damit die "untere Linie" auch tatsächlich unten bei allen Zellen sind */
                padding-bottom: 0;              /* Padding ausch auf "0", damit die "untere Linie" auch tatsächlich unten bei allen Zellen sind */
            }
            thead th:after
            {
                content: '';                    /* Leer-Inhalt */
                display: block;                 /* Leer-Inhalt wird als Block dargestellt, damit der Leer-Inhalt nicht an den Tabellen-Kopf-Text gehängt wird */
                padding-bottom: 0.3em;          /* Größe des Abstands des Leer-Inhalt zur unteren Linie */
                border-bottom: 1px solid black; /* Untere Linie malen */
            }          
            /* Tabellen-Körper-Zellen formtieren */
            td
            {
                vertical-align: top;        /* Text-Aurichtung Oben */
                padding: 0.3em;             /* Abstand um den text mit 0.3 em */
                border: 1px solid black;    /* Gitter-Linien mit 1x Stärke */
            } 
        </style>
    </head>
    <body id="Tabelle">
        <h1>Consumtion-Monitor -- IONIQ 'Blaue Elise'</h1>
        <!-- Einfache Navigations-leiste -->     
        <ul id="navibereich">
            <li id="navi01"><a href="ConsumptionMonitor_Ladezustand.php">Ladezustand</a></li>
            <li id="navi02"><a href="ConsumptionMonitor_Tabelle.php">Ladungs-Übersicht</a></li>
            <li id="navi03"><a href="ConsumptionMonitor_Statistik.php">Ladungs-Statistik</a></li>
        </ul>
        <br>
        <?php
            // Zähler initialisieren
            $counter = 0;
            // CSV-Datei öffen und auslesen
            $csvFile = "IoniqDB.csv";
            $handle = fopen($csvFile, "r");
            // Tabelle erstellen
            echo "<table>\n";
            // Schleife durch alle Datensätze
            while(($data = fgetcsv($handle,0, ";"))!=FALSE) 
            {
                if($counter == 0) 
                {
                    // Tabellen-Überschriften auslesen
                    echo "<thead>\n";
                    echo "<tr>\n";
                    echo "<th>Nummer</th>\n";
                    echo "<th>".$data[0]."</th>\n";
                    echo "<th>".$data[1]."</th>\n";
                    echo "<th>".$data[2]."</th>\n";
                    echo "<th>".$data[3]."</th>\n";
                    echo "<th>".$data[4]."</th>\n";
                    echo "<th>".$data[5]."</th>\n";
                    echo "<th>".$data[6]."</th>\n";
                    echo "<th>".$data[7]."</th>\n";
                    echo "<th>".$data[8]."</th>\n";
                    echo "<th>".$data[9]."</th>\n";
                    echo "<th>".$data[10]."</th>\n";
                    echo "<th>".$data[11]."</th>\n";
                    echo "<th>".$data[12]."</th>\n";
                    echo "<th>".$data[13]."</th>\n";
                    echo "<th>".$data[14]."</th>\n";
                    echo "</tr>\n";                    
                    echo "</thead>\n";
                    // Tabellen-Körper initialisierten
                    echo "<tbody>\n";    
                }
                else 
                {
                    // Den Tabellen-Körper augeben
                    echo "<tr>\n";
                    echo "<td>".$counter."</td>\n";    
                    echo "<td>".$data[0]."</td>\n";
                    echo "<td>".$data[1]."</td>\n";
                    echo "<td>".$data[2]."</td>\n";
                    echo "<td>".$data[3]."</td>\n";
                    echo "<td>".$data[4]."</td>\n";
                    echo "<td>".$data[5]."</td>\n";
                    echo "<td>".$data[6]."</td>\n";
                    echo "<td>".$data[7]."</td>\n";
                    echo "<td>".$data[8]."</td>\n";
                    echo "<td>".$data[9]."</td>\n";
                    echo "<td>".$data[10]."</td>\n";
                    echo "<td>".$data[11]."</td>\n";
                    echo "<td>".$data[12]."</td>\n";
                    echo "<td>".$data[13]."</td>\n";
                    echo "<td>".$data[14]."</td>\n";
                    echo "</tr>\n";    
                }
                // Zähler hochzählen
                $counter++;
            }
            // Tabellen-Körper beenden
            echo "</tbody>\n";
            // Tabell beenden
            echo "</table>\n"; 
            // CSV-Datei Schlißen
            fclose($handle);
        ?>
    </body>
</html>
