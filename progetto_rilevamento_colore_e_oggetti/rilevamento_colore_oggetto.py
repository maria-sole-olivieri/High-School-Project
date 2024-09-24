import pandas as pd
import cv2
import sys
from opcua import Client
from opcua import ua
from imageai.Detection import ObjectDetection

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
        
        # rilevmento webcam all'ID 0
        cam = cv2.VideoCapture(0)
                
        # controllo dell'avvenuto collegamento con la webcam
        if not (cam.isOpened()):
            print("Errore nell'apertura della webcam")
        
        # crezione istanza della classe ObjectDetecion
        detector = ObjectDetection()
        
        # percorsi di immagine di input, output e modello
        model_path = './modelli_oggetto/yolo-tiny.h5'
        input_path = './input_oggetto/immagine_webcam.png'
        output_path = './output_oggetto/immagine_oggetto.jpg'
                
        # caricamento file contenente i modelli
        detector.setModelTypeAsTinyYOLOv3()
        detector.setModelPath(model_path)
        detector.loadModel()
        
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
        
        # inizializione della finestra nella quale verrà mostrata la visuale della webcam
        cv2.namedWindow('Webcam')
        cv2.setMouseCallback('Webcam', mouse_click) # POSSO TOGLIERE QUESTA RIGA DI CODICE?
        
        # ciclo while per avviare la finestra
        while (True):
            
            # .read ha due valori, il primo non ci serve quindi lo assegnamo ad una variabile casuale
            temp, frame = cam.read()
            
            # mostriamo la webcam
            cv2.imshow('Webcam', frame)
            
            # scatta la foto quando l'utente preme la barra spaziatrice
            if cv2.waitKey(20) & 0xFF == 32:
                cv2.imwrite('./input_oggetto/immagine_webcam.png', frame)
                
                # funzione che restituisce gli oggetti rilevati nell'immagine e la loro probabilità %
                detection, extracted_images = detector.detectObjectsFromImage(input_image = input_path, output_image_path = output_path, extract_detected_objects=True)

                for eachItem in detection:
                    print(eachItem["name"] + " : " + str(eachItem["percentage_probability"]))
            
                # immagine da analizzare
                img = cv2.imread(output_path)
                
                # inizializione della finestra nella quale verrà mostrata l'immagine presa dalla webcam
                cv2.namedWindow('Rilevamento Colore')
                cv2.setMouseCallback('Rilevamento Colore', mouse_click)
        
                # mostriamo l'immagine
                cv2.imshow('Rilevamento Colore', img)
            
            if (clicked):
                
                # cv2.rectangle(image, startpoint, endpoint, color, thickness)
                # -1 riempie tutto il rettangolo
                cv2.rectangle(img, (20,20), (750,60), (b,g,r), -1)
                colore = recognize_color(r, g, b)
                
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
                    
                clicked=False
        
            # esce dal loop while quando l'utente preme il tasto 'Esc' sulla tastiera
            if cv2.waitKey(20) & 0xFF == 27:
                break
        
        cam.release()
        cv2.destroyAllWindows()

    finally:
        client.disconnect()
