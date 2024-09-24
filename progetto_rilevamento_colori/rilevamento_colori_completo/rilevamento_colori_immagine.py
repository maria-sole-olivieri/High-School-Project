import pandas as pd
import cv2
import sys
from opcua import Client
from opcua import ua

sys.path.insert(0, "..")

if __name__ == "__main__":
    
    # client = Client("opc.tcp://admin@localhost:4840/freeopcua/server/")
    # collegamento tramite utente
    client = Client("opc.tcp://192.168.0.1:4840")
    try:
        client.connect()
        
        # dichiarazione nodi delle variabili plc
        nodo_colore = client.get_node('ns=3;s="DB_Prova"."colore"')
        nodo_red = client.get_node('ns=3;s="red"')
        nodo_green = client.get_node('ns=3;s="green"')
        nodo_blue = client.get_node('ns=3;s="blue"')

        # immagine da analizzare
        img_file = "color_image.jpeg"
        
        img = cv2.imread(img_file)
        
        # lettura file contenente i colori ed i relativi dati
        index=["color", "color_name", "hex", "R", "G", "B"]
        csv = pd.read_csv('colors.csv', names=index, header=None)
        
        clicked = False
        r = g = b = xpos = ypos = 0
        
        # funzione che restituisce il nome ed i valori RGB dei colori
        def recognize_color(R, G, B):
            minimum = 10000
            for i in range(len(csv)):
                d = abs(R- int(csv.loc[i,"R"])) + abs(G- int(csv.loc[i,"G"]))+ abs(B- int(csv.loc[i,"B"]))
                if(d <= minimum):
                    minimum = d
                    cname = csv.loc[i,"color_name"]
            return cname
        
        # funzione che riconosce il doppio click del mouse
        def mouse_click(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDBLCLK:
                global b, g, r, xpos, ypos, clicked
                clicked = True
                xpos = x
                ypos = y
                b ,g, r = img[y,x]
                b = int(b)
                g = int(g)
                r = int(r)
        
        # inizializione della finestra nella quale verrà mostrata l'immagine
        cv2.namedWindow('Rilevamento Colore')
        cv2.setMouseCallback('Rilevamento Colore', mouse_click)
        
        # ciclo while per avviare la finestra
        while (True):
            
            # mostriamo l'immagine
            cv2.imshow("Rilevamento Colore", img)
            
            if (clicked):
                
                #cv2.rectangle(image, startpoint, endpoint, color, thickness)
                # -1 riempie tutto il rettangolo
                cv2.rectangle(img, (20,20), (750,60), (b,g,r), -1)
                colore = recognize_color(r, g, b)
                
                # dichiarazione stringa di testo da mostrare (nome del colore e valori RGB)
                text = colore + ' R='+ str(r) +  ' G='+ str(g) +  ' B='+ str(b)
                
                value = ua.DataValue(ua.Variant(r, ua.VariantType.Int16))
                nodo_red.set_data_value(value)
                red = nodo_red.get_value()
                print("Il nuovo valore del rosso e':", red)
                
                value = ua.DataValue(ua.Variant(g, ua.VariantType.Int16))
                nodo_green.set_data_value(value)
                green = nodo_green.get_value()
                print("Il nuovo valore del verde e':", green)
                
                value = ua.DataValue(ua.Variant(b, ua.VariantType.Int16))
                nodo_blue.set_data_value(value)
                blue = nodo_blue.get_value()
                print("Il nuovo valore del blu e':", blue)
                           
                value = ua.DataValue(ua.Variant(colore, ua.VariantType.String))
                nodo_colore.set_data_value(value)
                colore = nodo_colore.get_value()
                print("Il nuovo colore e':", colore, "\n")
                
                # cv2.putText(img, text, start, font(0-7), fontScale, color, thickness, lineType)
                cv2.putText(img, text, (50,50), 2,0.8, (255,255,255), 2, cv2.LINE_AA)
                
                # per colori molto chiari mostriamo il testo in nero
                if(r+g+b >= 450):
                    cv2.putText(img, text, (50,50), 2,0.8, (0,0,0), 2, cv2.LINE_AA)
                    
                clicked=False
        
            # esce dal loop while quando l'utente preme il tasto 'Esc' sulla tastiera
            if cv2.waitKey(20) & 0xFF == 27:
                break
    
        cv2.destroyAllWindows()

    finally:
        client.disconnect()
