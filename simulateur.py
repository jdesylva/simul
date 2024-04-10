#!/usr/bin/python3

#
import sys
import appSimul

jsonFile = "demolora.json"

if len(sys.argv) == 1:
    print ("Vous pouvez spécifier le nom du fichier de configuration comme premier paramètre.")
elif  len(sys.argv) == 2:
    jsonFile = sys.argv[1]
else:
    print("Spécifier seulement le nom du fichier de configuration comme premier paramètre. Si le programme est lancé sans paramètre, le fichier 'demolora.json' sera utilisé.")
    exit(0)

print(f"Le fichier '{jsonFile}' est utilisé.")

# Créer et démarrer l'application graphique
application = appSimul.appSimul("1190x750+225+150", jsonFile)
application.run()
