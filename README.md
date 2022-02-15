<h2>Monitoraggio PIP4048 con Home-Assistant</h2> 

<h3>Spunto di partenza: </h3>

https://www.energialternativa.info/Public/NewForum/discussione.php?213129&1
E procedura scritta nel file ForumEA_G_Guida PIP4048 e Zabbix  0.1.pdf

<h3>Installazione modulo “request” su raspberry esempi:</h3>

https://qastack.it/programming/17309288/importerror-no-module-named-requests
https://docs.python-requests.org/en/master/user/install/

<h3>Procedura di modifica tra l’installazione del forum e la mia modifica</h3>

Ho modificato la parte dello script che genera un file di testo e lo invia con mqtt con una richiesta API REST.

Per fa questo nel raspberry collegato all’inverte ho seguito le indicazioni del link sopra senza installare la parte di “Zabbix” poi ho tolto la parte di generazione file di testo, aggiunto la parte “Curl”, aggiunto “from requests import post” e “import json”, modificato tutta la parte finale del file SP5000.py che nel mio caso diventa SP5000-V2.py 

Ho aggiunto il valore del Token creato su Home Assistant

Cosi facendo il raspberry collegato all’inverter manda ogni tot i valori 

Per il passaggio di dati dall’inverter a Home Assistant ho preso spunto da:

https://funprojects.blog/2020/12/12/home-assistant-rest-api/ 
In Home Assistant ho aggiunto la riga “api:” al file di configurazione config.yaml come da https://www.home-assistant.io/integrations/api/

Per testare il funzionamento dell’integrazione “api” uso questo funzione da terminale mac avendo l’accortezza di cambiare il token con quello effettivo
```
curl -X GET -H "Authorization: Bearer eyJ0eXAiOiJKV1Qi…….4VhclYQ6ufcw" http://192.168.1.146:8123/api/
Se funziona risponde: {"message": "API running."}
```
Per leggere un valore da Home Assistant si usa questa cambiando il sensore con uno presente in HA:
```
curl -X GET -H "Authorization: Bearer eyJ0eXAiOiJKV1Qi…..42Y4VhclYQ6ufcw" http://192.168.1.146:8123/api/states/sensor.ble_battery_a4c138d7da8f
```
Per scrivere su HA si usa questa, su Home Assistant troveremo un’entita chiamata sensor.myinput1:
```
curl -X POST \
   -H "Authorization: Bearer eyJ0eXAiOiJKV1Qi….42Y4VhclYQ6ufcw" \
   -H "Content-Type: application/json" \
   -d '{"state":"88.6", "attributes": {"unit_of_measurement": "%", "friendly_name": "Remote Input 1"}}' \
   http://192.168.1.146:8123/api/states/sensor.myinput1
```
A questo punto devo trovarmi tra le entità di Home Assistant i vari sensori solar..

<h3>Istruzione per scaricare da GitHub</h3>

Istruzione per scaricare da GitHub i file dell’automatismo nella cartella del raspberry dell’inverter /opt/ermes-ui:

sudo git clone https://github.com/Ermes-ui/PIP4048-inverter-solare.git /opt/ermes-ui

<h3>Pagine relative ai comandi REST</h3>

https://developers.home-assistant.io/docs/api/rest/

https://www.home-assistant.io/integrations/sensor.rest/

https://www.home-assistant.io/integrations/rest_command/


<h3>Esempio di come leggere un file di testo in json tramite comando curl</h3>

https://community.home-assistant.io/t/solved-get-datas-from-json-file/162684

https://kleypot.com/fully-kiosk-rest-api-integration-in-home-assistant/

https://community.home-assistant.io/t/stuck-with-notify-rest/53623/12

