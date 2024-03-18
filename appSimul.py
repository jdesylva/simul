import socket
import time, sys
import json, csv
import pandas as pd

import tkinter as tk
import tkinter.messagebox as messagebox

from tkinter import simpledialog 

import mqttclient

class appSimul:

    def __init__(self, geo="1000x700+225+150", confFile="demolora.json"):
        '''This class configures and populates the toplevel window.
           top is the toplevel containing window.'''

        if  len(sys.argv) > 1:
            confFile = sys.argv[1]

        try:
            with open(confFile, 'r') as file:
                self.parametres = json.load(file)
        except:
            print(f"Erreur : Impossible d'ouvrir le fichier de configuration {confFile}")
            print("         Fin du programme.")
            sys.exit(-1)
            
        self.adresseIP = self.parametres['adresse_serveur_mqtt']
        self.port = self.parametres['port_tcp_serveur_mqtt']
        self.lafin = False
        self.lblTopics = list()
        self.dictValPeri = dict()
        
        self.root = tk.Tk()
        self.root.geometry(geo)
        #self.root.resizable(False, False)
        #self.root.attributes('-fullscreen',True)
        self.root.minsize(1000, 700)
        self.root.title("Cégep Joliette Télécom@" + str(socket.gethostname()))
        #self.root.wm_attributes('-alpha', 0.75)
        #self.root.overrideredirect(True)  # Remove window borders
        #self.root.wait_visibility(self.root)

        try :

            self.photo = tk.PhotoImage(file="logodemo_t.png")

            # Load the custom icon image
            icon_image = tk.PhotoImage(file="iconeDemo.png")

            # Set the custom icon for the window titlebar
            self.root.iconphoto(False, icon_image)

        except Exception as excpt:
            
            print("Fichiers des images manquants!")
            print("Erreur : ", excpt)
            sys.exit(-1)

        # Relier notre client à l'interface MQTT de notre serveur ChirpStack
        self.mqtt_client = mqttclient.mqttclient(confFile)
        self.mqtt_client.connect()

        # Get the current screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # get the width and height of the image
        image_width = self.photo.width()
        image_height = self.photo.height()

        self.Header = tk.Label(self.root, image=self.photo, width=image_width, height=image_height)
        self.Header.place(relx=0.5, rely=0.03, anchor=tk.N)

        self.Header.bind("<Button-1>", self.buttonLogoClick)
        self.Header.bind("<Configure>", self.on_window_resize)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        heure = time.localtime() # get struct_time
        time_string = time.strftime("%Y%m%d %H:%M", heure)

        self.lblDate = tk.Label(self.root, anchor="w")                          # Entete
        self.lblDate.place(relx=0.05, rely=0.3, height=27, width=225)
        self.lblDate.configure(text=time_string)
        self.lblDate.configure(justify='left')
        self.lblDate.configure(font=("Courrier New", 12))

        self.lblAdresseIP = tk.Label(self.root, anchor="w")                     # Bas de page
        self.lblAdresseIP.place(relx=0.05, rely=0.95, height=23, width=225)
        self.lblAdresseIP.configure(text="Serveur " + self.adresseIP)
        self.lblAdresseIP.configure(justify='left')
        self.lblAdresseIP.configure(font=("Courrier New", 10, "bold"))
        self.lblAdresseIP.bind("<Button-1>", self.buttonAdresse)

        self.lblPortTCP = tk.Label(self.root, anchor="w")                       # Bas de page
        self.lblPortTCP.place(relx=0.25, rely=0.95, height=23, width=100)
        self.lblPortTCP.configure(text="Port " + ":" + str(self.port))
        self.lblPortTCP.configure(justify='left')
        self.lblPortTCP.configure(font=("Courrier New", 10, "bold"))
        self.lblPortTCP.bind("<Button-1>", self.buttonPort)

        i = 0
        j = 0

        for devEui in self.parametres["eui_clients"] :
            #
            lbl = tk.Label(self.root, anchor="w")                       # Bas de page
            lbl.place(relx=0.05, rely=0.35 + ((i+j) * 0.035), height=23, relwidth=0.35)
            #lbl.configure(text=mqtt_client.lstTopics[i])
            lbl.configure(text=devEui)
            lbl.configure(justify='left')
            lbl.configure(font=("Courrier New", 12, "bold"), fg="#0055FF")
            # publish data
            lbl.bind("<Button-1>", self.publishData)
            self.dictValPeri[devEui] = dict()
            #lbl.bind("<Button-1>", self.publishData, lambda event, w=lbl: publishData(event, w))
            self.lblTopics.append(lbl)
            i += 1
            #
            for peripherique in self.parametres["peri_clients"][devEui]:
                lbl = tk.Label(self.root, anchor="w")                       # Bas de page
                lbl.place(relx=0.05, rely=0.35 + ((i+j) * 0.035), height=23, relwidth=0.25)
                lbl.configure(text=peripherique["type"], anchor="e")
                lbl.configure(justify='right')
                lbl.configure(font=("Courrier New", 10, "bold"))
                self.lblTopics.append(lbl)
                #text_box = tk.Text(self.root)
                strVar = tk.StringVar()
                self.dictValPeri[devEui][devEui+peripherique["type"]] = strVar
                text_box = tk.Entry(self.root, textvariable=strVar)
                text_box.place(relx=0.35, rely = 0.35 + ((i+j) * 0.035), height=23, relwidth=0.35)
                #text_box.tag_configure(peripherique["type"])
                j += 1
                

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            self.IP = s.getsockname()[0]
#        except:
            self.IP='127.0.0.1'
        finally:
            s.close()
            
    def publishData(self, event):
        """Cette fonction est utilisée pour publier les paramètres d'un capteur sur le serveur mqtt.
        """
        devEui = event.widget["text"]
        appEui = self.parametres['appeui'] 
        #widget_id = event.widget.winfo_id()
        #print(f"The ID of the widget is: {widget_id}")
        msg = self.creerMessageApplication(appEui, devEui)  #
        self.mqtt_client.publish(f"application/{self.parametres['appeui']}/device/{event.widget['text']}/event/up", msg)
        
    def on_configure(self, event):
        if event.width != self.width or event.height != self.height:
            self.width = event.width
            self.height = event.height
            self.resize()

    def resize(self):

        print(f"Resizing to {self.width}x{self.height}")

            
    def buttonLogoClick(self, event):

        self.on_closing()

    def buttonAdresse(self, event):

        self.adresseIP=simpledialog.askstring("Entrée", "Donner l'adresse IP du serveur", parent=self.root)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.IP = ('localhost', 1)

        tmout = s.gettimeout()

        try:
            # On assume que le serveur mqtt devrait répondre rapidement.
            # On fixe le délai d'attente maximum à 1 seconde
            s.settimeout(1.0)
            #
            # On se relie au serveur selon la configuration actuelle
            s.connect((self.adresseIP, self.port))
            # Si l'adresse entrée ne répond pas, une exception sera générée et le 
            # bloc "try:" va se terminé ici avec une exception.
            # On sauve donc l'adresse dans l'attribut de la classe.
            # self.adresseIP = adresseIP
            # On met à jour l'interface utilisateur avec la nouvelle adresse IP.
            self.lblAdresseIP.configure(text="Serveur : " + str(self.adresseIP))

            # On traite le cas où le progrmme est déjà relié à un serveur
            if None !=self.mqtt_client:
                self.mqtt_client.disconnect()
                
            # Relier notre client à l'interface MQTT du serveur ChirpStack.
            # On passe en paramètre le nom du fichier de configuration json.
            self.mqtt_client = mqttclient.mqttclient("demolora.json")

            self.lblPortTCP.configure(text=str(self.port), fg='black')
            # On mémorise la nouvelle adresse (debug)
            self.IP = self.adresseIP

        except:
            # On mémorise l'adresse localhost si il y a une exception
            self.IP = ('127.0.0.1', 1)
            # On indique dans le GUI qu'il y a eu erreur avec le serveur
            self.lblAdresseIP.configure(text="Serveur : Aucun")
        finally:
            s.settimeout(tmout)
            s.close()

        print(self.IP)

    def buttonPort(self, event):

        self.port=simpledialog.askinteger("Entrée", "Donner le numéro du port TCP \nutilisé par le serveur", parent=self.root, minvalue=1, maxvalue=65535)

        if self.port is not None:
            self.lblPortTCP.configure(text=str(self.port), fg='red')

        print(self.port)

    def updateTime(self):
        heure = time.localtime() # get struct_time
        time_string = time.strftime("%Y%m%d %H:%M", heure)

        self.lblDate.configure(text=time_string)

            
    def run(self):

        i = 0
        
        while not self.lafin:

            i+=1
            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.01)
            # On affiche l'heure à chaque minute
            if i >= 6000:
                i = 0
                self.updateTime()
                    
        self.root.quit()

    
    def on_closing(self):

        if messagebox.askokcancel("Terminé ?", "Est-ce que vous voulez fermer le programme ?"):

            self.lafin = True
            time.sleep(1)
            #root.destroy()
            #mqtt_client.disconnect()
            
    def on_window_resize(self, event):
        width = event.width
        height = event.height
        
    def Label1Click(self, event):

        self.TextDebug.delete("1.0", tk.END)

        named_tuple = time.localtime() # get struct_time
        time_string = time.strftime("%Y%m%d", named_tuple)

        filename = "rslts" + time_string + ".csv"

        try :

            with open(filename, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)

                for row in csv_reader:

                    print(row)
                    
                    self.TextDebug.insert(tk.END, row)
                    self.TextDebug.insert(tk.END, "\n")

        except :

            self.TextDebug.insert(tk.END, "ERREUR : Fichier " + filename + " introuvable.")
            
            
            
    def creerMessageApplication(self, applicationEui, deviceEui):
        '''
        Cette fonction construit le message à envoyer au serveur mqtt. Le message simule
        une transmission du server Chirpstack vers l'application.
        '''
        strObjet = ""
        
        for item in self.parametres["peri_clients"][deviceEui] :
            strObjet += (f'"{item["type"]}":' + self.dictValPeri[deviceEui][deviceEui+item["type"]].get() + ", ")
        # Enlever la derniere virgule
        strObjet = strObjet[0:len(strObjet)-2]

        h = time.localtime()
        nsTime = str(h.tm_year) + f"-{h.tm_mon:0>2d}" + f"-{h.tm_mday:0>2d}T" + f"{h.tm_hour:0>2d}" + f":{h.tm_min:0>2d}" + f":{h.tm_sec:0>2d}"
        
        message = '{"deduplicationId":"030550d5-bab3-4379-bd9f-21fa296d2023", "time":"' + nsTime
        message += '.291078344+00:00", ' +\
            '"deviceInfo":{"tenantId":"52f14cd4-c6f1-4fbd-8f87-4025e1d49242", ' +\
            '"tenantName":"ChirpStack", ' +\
            '"applicationId":"b750d774-16b6-4fe8-8eb0-21ea91ff3481", ' +\
            '"applicationName":"MQTT", ' +\
            '"deviceProfileId":"3869334d-6cee-41e4-9657-9ca881f15401", ' +\
            '"deviceProfileName":"DEV-RP2040-RFM9x", ' +\
            '"deviceName":"Dev-Feather2040RFM-OTAA", ' +\
            '"devEui":"' + deviceEui + '", ' +\
            '"deviceClassEnabled":"CLASS_A", ' +\
            '"tags":{}}, ' +\
            '"devAddr":"013fdad7", ' +\
            '"adr":false, ' +\
            '"dr":0, ' +\
            '"fCnt":4990, ' +\
            '"fPort":1, ' +\
            '"confirmed":false, ' +\
            '"data":"AU0MgACgAAAAAAAA", ' +\
            '"object":{' 

        message  += strObjet +\
            ', "RxInfo": ' +\
            '[ ' +\
            '{"gatewayId":"2cf7f1144420002a", ' +\
            '"uplinkId":1676047845, ' +\
            '"nsTime":"' + nsTime
        message += '.291078344+00:00", ' +\
            '"rssi":-40, ' +\
            '"snr":12.75, ' +\
            '"location":{}, ' +\
            '"context":"AAAAAAAAAAAAGAALoGsxIQ==", ' +\
            '"metadata":{ ' +\
            '"region_config_id":"us915_0", ' +\
            '"region_common_name":"US915" ' +\
            '}, ' +\
            '"crcStatus":"CRC_OK" ' +\
            '} ' +\
            '], ' +\
            '"txInfo":{ ' +\
            '"frequency":902900000, ' +\
            '"modulation":{ ' +\
            '"lora":{ ' +\
            '"bandwidth":125000, ' +\
            '"spreadingFactor":10, ' +\
            '"codeRate":"CR_4_5" ' +\
            '}}}}}'
        print(f"Len message == {len(message)}")
        return message.encode('utf8')
    
        
